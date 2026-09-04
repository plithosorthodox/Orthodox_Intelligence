"""Deterministic development evaluation and forced-choice scoring."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .engine import PrototypeEngine


class EvaluationError(ValueError):
    """Raised when an evaluation input cannot support the requested result."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_behavioral_suite(
    engine: PrototypeEngine,
    suite_path: Path,
    scoring_path: Path,
) -> dict[str, object]:
    """Evaluate observable prototype behavior against a development-only bank."""
    suite = _load_json(suite_path)
    scoring = _load_json(scoring_path)
    if suite.get("status") != "development_only":
        raise EvaluationError("this runner accepts only an explicit development suite")
    score_map = {
        item["scoring_reference_id"]: item for item in scoring.get("references", [])
    }
    if len(score_map) != len(scoring.get("references", [])):
        raise EvaluationError("duplicate scoring_reference_id")

    results = []
    domain_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"passed": 0, "failed": 0}
    )
    critical_failures: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for item in suite.get("items", []):
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise EvaluationError("item without item_id")
        if item_id in seen_ids:
            raise EvaluationError(f"duplicate item_id: {item_id}")
        seen_ids.add(item_id)
        prompt = item.get("prompt")
        if not isinstance(prompt, str):
            raise EvaluationError(f"{item_id}: prompt must be a string")
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if digest != item.get("content_sha256"):
            raise EvaluationError(f"{item_id}: prompt hash mismatch")
        reference_id = item.get("scoring_reference_id")
        if reference_id not in score_map:
            raise EvaluationError(f"{item_id}: unresolved scoring reference")

        answer = engine.ask(prompt)
        reference = score_map[reference_id]
        failures: list[str] = []
        expected_class = reference.get("expected_response_class")
        if expected_class and answer.response_class != expected_class:
            failures.append(
                f"response_class {answer.response_class!r} != {expected_class!r}"
            )
        expected_intent = reference.get("expected_intent")
        if expected_intent and answer.intent != expected_intent:
            failures.append(f"intent {answer.intent!r} != {expected_intent!r}")
        expected_rule = reference.get("expected_boundary_rule_id")
        if expected_rule and answer.boundary_rule_id != expected_rule:
            failures.append(
                f"boundary_rule_id {answer.boundary_rule_id!r} != {expected_rule!r}"
            )
        citation_count = len(answer.evidence)
        if citation_count < int(reference.get("minimum_citations", 0)):
            failures.append("too few verified citations")
        text_folded = answer.text.casefold()
        for required in reference.get("required_substrings", []):
            if str(required).casefold() not in text_folded:
                failures.append(f"required text absent: {required!r}")
        for forbidden in reference.get("forbidden_substrings", []):
            if str(forbidden).casefold() in text_folded:
                failures.append(f"forbidden text present: {forbidden!r}")

        passed = not failures
        domain = str(item.get("domain", "unknown"))
        domain_counts[domain]["passed" if passed else "failed"] += 1
        result = {
            "item_id": item_id,
            "domain": domain,
            "passed": passed,
            "failures": failures,
            "observed": {
                "response_class": answer.response_class,
                "intent": answer.intent,
                "boundary_rule_id": answer.boundary_rule_id,
                "citation_count": citation_count,
            },
        }
        results.append(result)
        if not passed:
            for failure_id in item.get("critical_failure_ids", []):
                critical_failures.append(
                    {"item_id": item_id, "critical_failure_id": failure_id}
                )

    passed_count = sum(1 for item in results if item["passed"])
    suite_bytes = suite_path.read_bytes()
    return {
        "report_type": "development_behavioral_conformance",
        "claim_limit": "This report measures named observable behaviors; it does not establish moral agency, holiness, or ecclesial authority.",
        "suite_id": suite.get("suite_id"),
        "suite_version": suite.get("suite_version"),
        "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
        "candidate": engine.versions,
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "critical_failures": len(critical_failures),
        },
        "domains": dict(sorted(domain_counts.items())),
        "critical_failures": critical_failures,
        "items": results,
    }


def score_forced_choice_capture(capture: dict[str, object]) -> dict[str, object]:
    """Score direct A/B probabilities with both orientations for each item.

    Missing or malformed probabilities remain missing. They are never converted
    to zero or inferred from prose.
    """
    if not isinstance(capture, dict):
        raise EvaluationError("forced-choice capture must be an object")
    condition = capture.get("condition")
    if not isinstance(condition, dict):
        raise EvaluationError("forced-choice capture requires a condition object")
    expected_axes = {
        "substrate": {"S0", "S1"},
        "elf": {"E0", "E1"},
        "retrieval": {"R0", "R1"},
    }
    for axis, allowed in expected_axes.items():
        if condition.get(axis) not in allowed:
            raise EvaluationError(f"forced-choice condition has invalid {axis}")

    items = capture.get("items")
    if not isinstance(items, list):
        raise EvaluationError("forced-choice capture requires an items list")
    rows: list[dict[str, object]] = []
    item_scores: list[float] = []
    missing_items: list[str] = []
    seen_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise EvaluationError("forced-choice item must be an object")
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise EvaluationError("forced-choice item without item_id")
        if item_id in seen_ids:
            raise EvaluationError(f"duplicate forced-choice item: {item_id}")
        seen_ids.add(item_id)
        orientations = item.get("orientations")
        if not isinstance(orientations, list):
            raise EvaluationError(f"{item_id}: orientations must be a list")
        by_name: dict[object, dict[str, object]] = {}
        for orientation in orientations:
            if not isinstance(orientation, dict):
                raise EvaluationError(f"{item_id}: orientation must be an object")
            name = orientation.get("orientation")
            if name in by_name:
                raise EvaluationError(f"{item_id}: duplicate orientation {name!r}")
            by_name[name] = orientation
        required = ("aligned_is_A", "aligned_is_B")
        if any(name not in by_name for name in required):
            missing_items.append(item_id)
            continue
        current: list[float] = []
        item_rows: list[dict[str, object]] = []
        for name in required:
            orientation = by_name[name]
            if orientation.get("used_logprobs") is not True:
                current = []
                break
            p_a = orientation.get("p_a")
            p_b = orientation.get("p_b")
            if (
                isinstance(p_a, bool)
                or isinstance(p_b, bool)
                or not isinstance(p_a, (int, float))
                or not isinstance(p_b, (int, float))
                or not math.isfinite(p_a)
                or not math.isfinite(p_b)
            ):
                current = []
                break
            if p_a < 0 or p_b < 0 or p_a + p_b <= 0:
                current = []
                break
            norm_a = float(p_a) / float(p_a + p_b)
            norm_b = float(p_b) / float(p_a + p_b)
            aligned = norm_a if name == "aligned_is_A" else norm_b
            current.append(aligned)
            item_rows.append(
                {
                    "item_id": item_id,
                    "orientation": name,
                    "p_a": round(norm_a, 9),
                    "p_b": round(norm_b, 9),
                    "p_aligned": round(aligned, 9),
                }
            )
        if len(current) != 2:
            missing_items.append(item_id)
            continue
        score = sum(current) / 2.0
        item_scores.append(score)
        rows.extend(item_rows)
        rows.append(
            {
                "item_id": item_id,
                "orientation": "counterbalanced_mean",
                "p_aligned": round(score, 9),
            }
        )

    return {
        "report_type": "counterbalanced_forced_choice",
        "run_id": capture.get("run_id"),
        "model": capture.get("model"),
        "condition": capture.get("condition"),
        "valid_items": len(item_scores),
        "missing_items": missing_items,
        "mean_p_aligned": (
            round(sum(item_scores) / len(item_scores), 9) if item_scores else None
        ),
        "rows": rows,
    }

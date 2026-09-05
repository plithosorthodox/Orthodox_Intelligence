#!/usr/bin/env python3
"""Dependency-free structural checks for the OI research repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "docs/OI_RESEARCH_AND_TRAINING_SPECIFICATION_v0.1.md",
    "docs/ARCHITECTURE.md",
    "docs/EVALUATION_PROTOCOL.md",
    "docs/DATA_AND_PROVENANCE.md",
    "docs/ELF_REVIEW_PROTOCOL.md",
    "docs/THREAT_MODEL.md",
    "docs/ROADMAP.md",
    "docs/DECISION_LOG.md",
    "docs/OPEN_QUESTIONS.md",
    "docs/MODEL_CARD_TEMPLATE.md",
    "docs/PRODUCT_ACCESS_PLAN.md",
    "docs/PROTOTYPE.md",
    "schemas/corpus-record.schema.json",
    "schemas/training-example.schema.json",
    "schemas/evaluation-item.schema.json",
    "schemas/model-release.schema.json",
    "config/acceptance_criteria.v0.1.json",
    "config/prototype_policy.v0.1.json",
    "config/prototype_policy.v0.2.json",
    "config/sofiia_grounded.v0.2.gbnf",
    "config/web_search_brave.v0.1.json",
    "evaluation/README.md",
    "evaluation/development/suite.v0.1.json",
    "evaluation/development/suite.v0.2.json",
    "evaluation/development/scoring.v0.1.json",
    "evaluation/development/scoring.v0.2.json",
    "evaluation/examples/forced-choice-capture.example.json",
    "prototype/corpus/oi-policy-demo.v0.1.json",
    "prototype/index.html",
    "prototype/app.js",
    "prototype/styles.css",
    "oi_prototype/engine.py",
    "oi_prototype/evaluation.py",
    "oi_prototype/retrieval.py",
    "oi_prototype/web_search.py",
    "research/evidence/provenance.v0.1.json",
    "tools/run_evaluation.py",
    "tools/score_forced_choice.py",
    "tools/serve_prototype.py",
    "tests/test_retrieval.py",
    "tests/test_web_integration.py",
    "tests/test_web_search.py",
)
FORBIDDEN_SUFFIXES = (".gguf", ".onnx", ".safetensors", ".pem", ".key")
LOCAL_PATH = re.compile(r"(?:[A-Za-z]:\\|/Users/|/home/|/work" r"space/)")


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return None


def check() -> list[str]:
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    schema_ids: dict[str, str] = {}
    for path in sorted((ROOT / "schemas").glob("*.json")):
        data = load_json(path, errors)
        if not isinstance(data, dict):
            continue
        for key in ("$schema", "$id", "title", "type"):
            if not data.get(key):
                errors.append(f"{path.relative_to(ROOT)}: missing {key}")
        schema_id = data.get("$id")
        if schema_id in schema_ids:
            errors.append(
                f"{path.relative_to(ROOT)}: duplicate $id also used by "
                f"{schema_ids[schema_id]}"
            )
        elif isinstance(schema_id, str):
            schema_ids[schema_id] = str(path.relative_to(ROOT))
        if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{path.relative_to(ROOT)}: schema draft must be 2020-12")

    criteria_path = ROOT / "config" / "acceptance_criteria.v0.1.json"
    criteria = load_json(criteria_path, errors) if criteria_path.exists() else None
    if isinstance(criteria, dict):
        if criteria.get("spec_version") != "0.1":
            errors.append("acceptance criteria: spec_version must be 0.1")
        if criteria.get("status") != "provisional":
            errors.append("acceptance criteria: v0.1 thresholds must remain provisional")
        if criteria.get("ratification_required") is not True:
            errors.append("acceptance criteria: ratification_required must be true")
        ids: set[str] = set()
        for group in ("critical_gates", "quantitative_gates"):
            gates = criteria.get(group)
            if not isinstance(gates, list) or not gates:
                errors.append(f"acceptance criteria: {group} must be a non-empty list")
                continue
            for gate in gates:
                gate_id = gate.get("id") if isinstance(gate, dict) else None
                if not gate_id:
                    errors.append(f"acceptance criteria: {group} contains a gate without id")
                elif gate_id in ids:
                    errors.append(f"acceptance criteria: duplicate gate id {gate_id}")
                else:
                    ids.add(gate_id)

    corpus_path = ROOT / "prototype" / "corpus" / "oi-policy-demo.v0.1.json"
    corpus = load_json(corpus_path, errors) if corpus_path.exists() else None
    if isinstance(corpus, dict):
        if corpus.get("status") != "development_only":
            errors.append("prototype corpus: status must be development_only")
        segments: set[str] = set()
        for record in corpus.get("records", []):
            if not isinstance(record, dict):
                errors.append("prototype corpus: record must be an object")
                continue
            segment_id = record.get("segment_id")
            if not isinstance(segment_id, str) or not segment_id:
                errors.append("prototype corpus: record missing segment_id")
            elif segment_id in segments:
                errors.append(f"prototype corpus: duplicate segment_id {segment_id}")
            else:
                segments.add(segment_id)
            text = record.get("display_text")
            digest = record.get("content_sha256")
            if not isinstance(text, str) or not text:
                errors.append(f"prototype corpus: {segment_id} missing display_text")
            elif hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
                errors.append(f"prototype corpus: {segment_id} content hash mismatch")
            if record.get("source_class") != "product_policy":
                errors.append(f"prototype corpus: {segment_id} is not product_policy")

    policy_path = ROOT / "config" / "prototype_policy.v0.2.json"
    policy = load_json(policy_path, errors) if policy_path.exists() else None
    if isinstance(policy, dict):
        if policy.get("status") != "development_only":
            errors.append("prototype policy: status must be development_only")
        rule_ids: set[str] = set()
        for rule in policy.get("rules", []):
            rule_id = rule.get("rule_id") if isinstance(rule, dict) else None
            if not rule_id:
                errors.append("prototype policy: rule without rule_id")
                continue
            if rule_id in rule_ids:
                errors.append(f"prototype policy: duplicate rule_id {rule_id}")
            rule_ids.add(rule_id)
            for pattern in rule.get("patterns", []):
                try:
                    re.compile(pattern)
                except (TypeError, re.error) as exc:
                    errors.append(f"prototype policy: {rule_id} invalid pattern: {exc}")

    suite_path = ROOT / "evaluation" / "development" / "suite.v0.2.json"
    scoring_path = ROOT / "evaluation" / "development" / "scoring.v0.2.json"
    suite = load_json(suite_path, errors) if suite_path.exists() else None
    scoring = load_json(scoring_path, errors) if scoring_path.exists() else None
    if isinstance(suite, dict) and isinstance(scoring, dict):
        if suite.get("status") != "development_only":
            errors.append("development suite: status must be development_only")
        if suite.get("historical_bank_reused") is not False:
            errors.append("development suite: historical_bank_reused must be false")
        references = {
            value.get("scoring_reference_id")
            for value in scoring.get("references", [])
            if isinstance(value, dict)
        }
        item_ids: set[str] = set()
        for item in suite.get("items", []):
            if not isinstance(item, dict):
                errors.append("development suite: item must be an object")
                continue
            item_id = item.get("item_id")
            if not item_id:
                errors.append("development suite: item without item_id")
                continue
            if item_id in item_ids:
                errors.append(f"development suite: duplicate item_id {item_id}")
            item_ids.add(item_id)
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or not prompt:
                errors.append(f"development suite: {item_id} missing prompt")
            elif hashlib.sha256(prompt.encode("utf-8")).hexdigest() != item.get(
                "content_sha256"
            ):
                errors.append(f"development suite: {item_id} prompt hash mismatch")
            if item.get("scoring_reference_id") not in references:
                errors.append(f"development suite: {item_id} unresolved scoring reference")

    provenance_path = ROOT / "research" / "evidence" / "provenance.v0.1.json"
    provenance = load_json(provenance_path, errors) if provenance_path.exists() else None
    if isinstance(provenance, dict):
        artifact_ids: set[str] = set()
        for artifact in provenance.get("artifacts", []):
            artifact_id = artifact.get("artifact_id") if isinstance(artifact, dict) else None
            if not artifact_id:
                errors.append("research provenance: artifact without artifact_id")
                continue
            if artifact_id in artifact_ids:
                errors.append(f"research provenance: duplicate artifact_id {artifact_id}")
            artifact_ids.add(artifact_id)
            if not re.fullmatch(r"[a-f0-9]{64}", str(artifact.get("sha256", ""))):
                errors.append(f"research provenance: {artifact_id} invalid sha256")
            if artifact.get("access_class") != "restricted_not_committed":
                errors.append(f"research provenance: {artifact_id} must remain restricted")

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden artifact committed: {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".md", ".py", ".json", ".yml", ".yaml"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError as exc:
                errors.append(f"{path.relative_to(ROOT)}: not valid UTF-8: {exc}")
                continue
            if path.resolve() != Path(__file__).resolve() and LOCAL_PATH.search(text):
                errors.append(f"{path.relative_to(ROOT)}: contains a machine-local path")

    decision_log = ROOT / "docs" / "DECISION_LOG.md"
    if decision_log.exists():
        decision_ids: set[str] = set()
        for line in decision_log.read_text(encoding="utf-8").splitlines():
            match = re.match(r"## (OI-\d+)\b", line)
            if match is None:
                continue
            if match.group(1) in decision_ids:
                errors.append(f"decision log: duplicate decision id {match.group(1)}")
            decision_ids.add(match.group(1))

    spec = ROOT / "docs" / "OI_RESEARCH_AND_TRAINING_SPECIFICATION_v0.1.md"
    if spec.exists():
        text = spec.read_text(encoding="utf-8")
        for marker in ("S0", "S1", "E0", "E1", "R0", "R1", "2 x 2 x 2"):
            if marker not in text:
                errors.append(f"research specification: missing design marker {marker!r}")

    for relative in ("prototype/index.html", "prototype/app.js", "prototype/styles.css"):
        path = ROOT / relative
        if path.exists() and re.search(r"https?://", path.read_text(encoding="utf-8")):
            errors.append(f"{relative}: prototype static asset contains an external URL")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()
    errors = check()
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    elif errors:
        print(f"{len(errors)} repository problem(s):")
        for error in errors:
            print(f"  {error}")
    else:
        print("OI repository structure and policy checks passed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

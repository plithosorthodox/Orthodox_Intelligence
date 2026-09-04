"""Deterministic product boundaries, kept separate from any future ELF."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BoundaryDecision:
    intent: str
    rule_id: str | None
    response_class: str | None
    response: str | None


class BoundaryPolicy:
    def __init__(self, policy_path: Path):
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
        self.version = str(payload["policy_version"])
        self._rules: list[tuple[dict[str, object], tuple[re.Pattern[str], ...]]] = []
        for rule in payload.get("rules", []):
            patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in rule["patterns"])
            self._rules.append((rule, patterns))

    def classify(self, question: str) -> BoundaryDecision:
        normalized = " ".join(question.split())
        for rule, patterns in self._rules:
            if any(pattern.search(normalized) for pattern in patterns):
                return BoundaryDecision(
                    intent=str(rule["intent"]),
                    rule_id=str(rule["rule_id"]),
                    response_class=str(rule["response_class"]),
                    response=str(rule["response"]),
                )
        return BoundaryDecision(
            intent="informational",
            rule_id=None,
            response_class=None,
            response=None,
        )


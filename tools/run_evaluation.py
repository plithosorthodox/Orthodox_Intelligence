#!/usr/bin/env python3
"""Run the development behavioral suite against the executable prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oi_prototype.corpus import EvidenceStore  # noqa: E402
from oi_prototype.engine import PrototypeEngine  # noqa: E402
from oi_prototype.evaluation import run_behavioral_suite  # noqa: E402
from oi_prototype.policy import BoundaryPolicy  # noqa: E402


def build_engine() -> PrototypeEngine:
    return PrototypeEngine(
        EvidenceStore(ROOT / "prototype" / "corpus" / "oi-policy-demo.v0.1.json"),
        BoundaryPolicy(ROOT / "config" / "prototype_policy.v0.2.json"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    parser.add_argument(
        "--fail-on-any",
        action="store_true",
        help="return nonzero for any failed development item",
    )
    args = parser.parse_args()
    report = run_behavioral_suite(
        build_engine(),
        ROOT / "evaluation" / "development" / "suite.v0.2.json",
        ROOT / "evaluation" / "development" / "scoring.v0.2.json",
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    failed = int(report["summary"]["failed"])  # type: ignore[index]
    critical = int(report["summary"]["critical_failures"])  # type: ignore[index]
    return 1 if critical or (args.fail_on_any and failed) else 0


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""Start the loopback-only OI research prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oi_prototype.server import serve  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        raise SystemExit("port must be between 0 and 65535")
    serve(ROOT, args.port)


if __name__ == "__main__":
    main()


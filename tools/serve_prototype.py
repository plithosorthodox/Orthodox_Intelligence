#!/usr/bin/env python3
"""Start the loopback-only Uvaha / Orthodox Intelligence research prototype."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oi_prototype.server import serve  # noqa: E402
from oi_prototype.web_search import BraveLlmContextProvider  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--corpus-install",
        type=Path,
        default=None,
        help="installed Plithos artifact directory; defaults to artifacts/plithos",
    )
    parser.add_argument(
        "--web-search",
        action="store_true",
        help=(
            "enable optional Brave Web evidence when Automatic sources is selected; "
            "requires an API key in UVAHA_BRAVE_API_KEY"
        ),
    )
    parser.add_argument(
        "--demo-corpus",
        action="store_true",
        help="force the original eight-record demonstration corpus",
    )
    parser.add_argument(
        "--model-endpoint",
        default=None,
        help=(
            "loopback origin for a local llama.cpp OpenAI-compatible server, "
            "for example http://127.0.0.1:8080; no remote endpoint is accepted"
        ),
    )
    parser.add_argument(
        "--model-timeout-seconds",
        type=float,
        default=120.0,
        help=(
            "maximum wait for one local model completion; increase for "
            "CPU-bound models (default: 120)"
        ),
    )
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        raise SystemExit("port must be between 0 and 65535")
    web_search_provider = None
    if args.web_search:
        api_key = os.environ.get("UVAHA_BRAVE_API_KEY", "").strip()
        if not api_key:
            raise SystemExit(
                "--web-search requires the UVAHA_BRAVE_API_KEY environment variable"
            )
        web_search_provider = BraveLlmContextProvider(api_key)
    serve(
        ROOT,
        args.port,
        corpus_install=args.corpus_install,
        force_demo=args.demo_corpus,
        model_endpoint=args.model_endpoint,
        model_timeout_seconds=args.model_timeout_seconds,
        web_search_provider=web_search_provider,
    )


if __name__ == "__main__":
    main()

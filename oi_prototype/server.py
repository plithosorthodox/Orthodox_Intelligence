"""Loopback-only HTTP server for the visible Uvaha research prototype."""

from __future__ import annotations

import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .corpus import EvidenceStore
from .engine import PrototypeEngine
from .evaluation import run_behavioral_suite
from .model_runtime import LlamaCppServerRuntime
from .plithos_store import PlithosEvidenceStore
from .policy import BoundaryPolicy

MAX_REQUEST_BYTES = 32 * 1024
MAX_HISTORY_TURNS = 6
MAX_HISTORY_TURN_CHARS = 800
MAX_CONTEXT_SOURCES = 4
MAX_SEGMENT_ID_CHARS = 200
_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


def build_default_engine(
    root: Path,
    corpus_install: Path | None = None,
    *,
    force_demo: bool = False,
    model_endpoint: str | None = None,
    model_timeout_seconds: float = 120.0,
    web_search_provider: object | None = None,
) -> PrototypeEngine:
    policy = BoundaryPolicy(root / "config" / "prototype_policy.v0.2.json")
    install_dir = corpus_install or (root / "artifacts" / "plithos")
    if not force_demo and (install_dir / "installed.json").is_file():
        store = PlithosEvidenceStore(install_dir)
    else:
        store = EvidenceStore(root / "prototype" / "corpus" / "oi-policy-demo.v0.1.json")
    runtime = (
        LlamaCppServerRuntime(model_endpoint, timeout_seconds=model_timeout_seconds)
        if model_endpoint
        else None
    )
    return PrototypeEngine(
        store,
        policy,
        model_runtime=runtime,
        web_search_provider=web_search_provider,
    )


class PrototypeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        root: Path,
        corpus_install: Path | None = None,
        *,
        force_demo: bool = False,
        model_endpoint: str | None = None,
        model_timeout_seconds: float = 120.0,
        web_search_provider: object | None = None,
    ):
        self.root = root
        self.static_root = root / "prototype"
        self.corpus_install = corpus_install or (root / "artifacts" / "plithos")
        self.engine = build_default_engine(
            root,
            corpus_install=self.corpus_install,
            force_demo=force_demo,
            model_endpoint=model_endpoint,
            model_timeout_seconds=model_timeout_seconds,
            web_search_provider=web_search_provider,
        )
        super().__init__(address, PrototypeHandler)


class PrototypeHandler(BaseHTTPRequestHandler):
    server: PrototypeServer

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _request_is_local(self) -> bool:
        port = self.server.server_address[1]
        allowed_hosts = {
            "127.0.0.1",
            f"127.0.0.1:{port}",
            "localhost",
            f"localhost:{port}",
            "[::1]",
            f"[::1]:{port}",
        }
        if self.headers.get("Host", "") not in allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        if origin in (None, "", "null"):
            return True
        return origin in {f"http://{host}" for host in allowed_hosts}

    def _headers(self, status: HTTPStatus, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()

    def _send_bytes(
        self,
        payload: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self._headers(status, content_type, len(payload))
        self.wfile.write(payload)

    def _send_json(
        self,
        value: Any,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self._send_bytes(
            (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message, "status": int(status)}, status)

    def do_GET(self) -> None:  # noqa: N802
        if not self._request_is_local():
            self._send_error_json(HTTPStatus.FORBIDDEN, "loopback requests only")
            return
        path = urlsplit(self.path).path
        if path == "/api/status":
            value = self.server.engine.status()
            value["calendar_available"] = (
                value.get("corpus_mode") == "plithos"
                and (self.server.corpus_install / "calendar" / "manifest.json").is_file()
            )
            self._send_json(value)
            return
        if path == "/api/evaluate":
            report = run_behavioral_suite(
                self.server.engine,
                self.server.root / "evaluation" / "development" / "suite.v0.2.json",
                self.server.root / "evaluation" / "development" / "scoring.v0.2.json",
            )
            self._send_json(report)
            return
        calendar_files = {
            "/calendar/plithos-calendar.v2.js": "plithos-calendar.v2.js",
            "/calendar/calendar-tables.v2.en.json": "calendar-tables.v2.en.json",
            "/calendar/manifest.json": "manifest.json",
        }
        calendar_name = calendar_files.get(path)
        if calendar_name is not None:
            if self.server.engine.status().get("corpus_mode") != "plithos":
                self._send_error_json(HTTPStatus.NOT_FOUND, "calendar not installed")
                return
            file_path = self.server.corpus_install / "calendar" / calendar_name
            if not file_path.is_file():
                self._send_error_json(HTTPStatus.NOT_FOUND, "calendar not installed")
                return
            content_type = (
                "text/javascript; charset=utf-8"
                if file_path.suffix == ".js"
                else "application/json; charset=utf-8"
            )
            self._send_bytes(file_path.read_bytes(), content_type)
            return
        static_files = {
            "/": "index.html",
            "/index.html": "index.html",
            "/app.js": "app.js",
            "/styles.css": "styles.css",
            "/manifest.webmanifest": "manifest.webmanifest",
        }
        name = static_files.get(path)
        if name is None:
            self._send_error_json(HTTPStatus.NOT_FOUND, "not found")
            return
        file_path = self.server.static_root / name
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if file_path.suffix in {".html", ".js", ".css", ".webmanifest"}:
            content_type += "; charset=utf-8"
        self._send_bytes(file_path.read_bytes(), content_type)

    def do_POST(self) -> None:  # noqa: N802
        if not self._request_is_local():
            self._send_error_json(HTTPStatus.FORBIDDEN, "loopback requests only")
            return
        if urlsplit(self.path).path != "/api/ask":
            self._send_error_json(HTTPStatus.NOT_FOUND, "not found")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "invalid content length")
            return
        if size <= 0 or size > MAX_REQUEST_BYTES:
            self._send_error_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "invalid request size",
            )
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "request must be UTF-8 JSON",
            )
            return
        question = payload.get("question") if isinstance(payload, dict) else None
        source_mode = (
            payload.get("source_mode", "local_only")
            if isinstance(payload, dict)
            else "local_only"
        )
        history_value = (
            payload.get("history", [])
            if isinstance(payload, dict)
            else []
        )
        context_sources_value = (
            payload.get("context_sources", [])
            if isinstance(payload, dict)
            else []
        )
        if not isinstance(question, str):
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "question must be a string",
            )
            return
        if source_mode not in {"automatic", "local_only"}:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "source_mode must be automatic or local_only",
            )
            return
        if not isinstance(history_value, list) or len(history_value) > MAX_HISTORY_TURNS:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "history must be a bounded list of conversation turns",
            )
            return
        history: list[dict[str, str]] = []
        for turn in history_value:
            if (
                not isinstance(turn, dict)
                or set(turn) != {"role", "content"}
                or turn.get("role") not in {"user", "assistant"}
                or not isinstance(turn.get("content"), str)
                or not turn["content"].strip()
                or len(turn["content"]) > MAX_HISTORY_TURN_CHARS
            ):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "history contains an invalid conversation turn",
                )
                return
            history.append(
                {
                    "role": turn["role"],
                    "content": " ".join(turn["content"].split()),
                }
            )
        if (
            not isinstance(context_sources_value, list)
            or len(context_sources_value) > MAX_CONTEXT_SOURCES
        ):
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "context_sources must be a bounded list of local source references",
            )
            return
        context_sources: list[dict[str, str]] = []
        for source in context_sources_value:
            if (
                not isinstance(source, dict)
                or set(source) != {"segment_id", "content_sha256"}
                or not isinstance(source.get("segment_id"), str)
                or not source["segment_id"].strip()
                or len(source["segment_id"]) > MAX_SEGMENT_ID_CHARS
                or not isinstance(source.get("content_sha256"), str)
                or _SHA256.fullmatch(source["content_sha256"]) is None
            ):
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "context_sources contains an invalid local source reference",
                )
                return
            context_sources.append(
                {
                    "segment_id": source["segment_id"],
                    "content_sha256": source["content_sha256"].lower(),
                }
            )
        self._send_json(
            self.server.engine.ask(
                question,
                source_mode=source_mode,
                history=tuple(history),
                context_sources=tuple(context_sources),
            ).as_dict()
        )


def serve(
    root: Path,
    port: int,
    corpus_install: Path | None = None,
    *,
    force_demo: bool = False,
    model_endpoint: str | None = None,
    model_timeout_seconds: float = 120.0,
    web_search_provider: object | None = None,
) -> None:
    server = PrototypeServer(
        ("127.0.0.1", port),
        root,
        corpus_install=corpus_install,
        force_demo=force_demo,
        model_endpoint=model_endpoint,
        model_timeout_seconds=model_timeout_seconds,
        web_search_provider=web_search_provider,
    )
    host, selected_port = server.server_address
    status = server.engine.status()
    print(f"Uvaha research prototype: http://{host}:{selected_port}")
    print(
        f"Corpus mode: {status['corpus_mode']} · "
        f"{status['record_count']} searchable text records"
    )
    if status.get("corpus_mode") == "plithos":
        print("Calendar: Revised Julian + Julian")
    if status.get("generative_model_loaded"):
        runtime = status.get("model_runtime") or {}
        print(
            f"Model: Sofiia v0.1 · {runtime.get('runtime', 'local runtime')} · "
            "loopback only"
        )
        # Which constraint the model server will actually honour. It is worth
        # a line: when nothing constrains the model, every answer comes back
        # as unverifiable prose and the refusal blames the verifier.
        constraint = runtime.get("structured_output")
        if constraint:
            print(f"Structured output: {constraint}")
    else:
        print("Model: Sofiia v0.1 selected but not connected")
    if status.get("web_available"):
        print("Web sources: available when Automatic is selected")
    else:
        print("Web sources: disabled")
    print(
        "Questions are not written to logs or disk. No question is sent to a "
        "non-loopback model endpoint."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        close = getattr(server.engine.evidence_store, "close", None)
        if callable(close):
            close()
        server.server_close()

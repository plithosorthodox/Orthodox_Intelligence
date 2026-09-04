"""Loopback-only HTTP server for the visible OI research prototype."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .corpus import EvidenceStore
from .engine import PrototypeEngine
from .evaluation import run_behavioral_suite
from .plithos_store import PlithosEvidenceStore
from .policy import BoundaryPolicy


MAX_REQUEST_BYTES = 32 * 1024


def build_default_engine(
    root: Path,
    corpus_install: Path | None = None,
    *,
    force_demo: bool = False,
) -> PrototypeEngine:
    policy = BoundaryPolicy(root / "config" / "prototype_policy.v0.2.json")
    install_dir = corpus_install or (root / "artifacts" / "plithos")
    if not force_demo and (install_dir / "installed.json").is_file():
        store = PlithosEvidenceStore(install_dir)
    else:
        store = EvidenceStore(root / "prototype" / "corpus" / "oi-policy-demo.v0.1.json")
    return PrototypeEngine(store, policy)


class PrototypeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        root: Path,
        corpus_install: Path | None = None,
        *,
        force_demo: bool = False,
    ):
        self.root = root
        self.static_root = root / "prototype"
        self.engine = build_default_engine(
            root, corpus_install=corpus_install, force_demo=force_demo
        )
        super().__init__(address, PrototypeHandler)


class PrototypeHandler(BaseHTTPRequestHandler):
    server: PrototypeServer

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _request_is_local(self) -> bool:
        port = self.server.server_address[1]
        allowed_hosts = {
            "127.0.0.1", f"127.0.0.1:{port}",
            "localhost", f"localhost:{port}",
            "[::1]", f"[::1]:{port}",
        }
        if self.headers.get("Host", "") not in allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        if origin in (None, "", "null"):
            return True
        allowed_origins = {f"http://{host}" for host in allowed_hosts}
        return origin in allowed_origins

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
        self, value: Any, status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        payload = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        self._send_bytes(payload, "application/json; charset=utf-8", status)

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message, "status": int(status)}, status)

    def do_GET(self) -> None:  # noqa: N802
        if not self._request_is_local():
            self._send_error_json(HTTPStatus.FORBIDDEN, "loopback requests only")
            return
        path = urlsplit(self.path).path
        if path == "/api/status":
            self._send_json(self.server.engine.status())
            return
        if path == "/api/evaluate":
            report = run_behavioral_suite(
                self.server.engine,
                self.server.root / "evaluation" / "development" / "suite.v0.2.json",
                self.server.root
                / "evaluation"
                / "development"
                / "scoring.v0.2.json",
            )
            self._send_json(report)
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
        path = urlsplit(self.path).path
        if path != "/api/ask":
            self._send_error_json(HTTPStatus.NOT_FOUND, "not found")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "invalid content length")
            return
        if size <= 0 or size > MAX_REQUEST_BYTES:
            self._send_error_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "invalid request size")
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "request must be UTF-8 JSON")
            return
        question = payload.get("question") if isinstance(payload, dict) else None
        if not isinstance(question, str):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "question must be a string")
            return
        self._send_json(self.server.engine.ask(question).as_dict())


def serve(
    root: Path,
    port: int,
    corpus_install: Path | None = None,
    *,
    force_demo: bool = False,
) -> None:
    server = PrototypeServer(
        ("127.0.0.1", port),
        root,
        corpus_install=corpus_install,
        force_demo=force_demo,
    )
    host, selected_port = server.server_address
    status = server.engine.status()
    print(f"OI research prototype: http://{host}:{selected_port}")
    print(
        f"Corpus mode: {status['corpus_mode']} · "
        f"{status['record_count']} searchable text records"
    )
    print("Loopback only; questions are not written to logs or disk.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        close = getattr(server.engine.evidence_store, "close", None)
        if callable(close):
            close()
        server.server_close()

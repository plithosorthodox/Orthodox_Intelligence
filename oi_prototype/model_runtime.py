"""Local generative-model runtime seam for the OI prototype.

This module does not bundle or download model weights. The first development
adapter speaks only to an explicitly configured loopback llama.cpp server. A
production mobile runtime remains intentionally unselected until device testing.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL_MANIFEST = Path(__file__).resolve().parents[1] / "config" / "model_olmo2_7b_instruct.v1.json"
_ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class ModelRuntimeError(RuntimeError):
    """Raised when the selected local model runtime cannot be used safely."""


@dataclass(frozen=True)
class SelectedModel:
    family: str
    upstream_model_id: str
    license_spdx: str
    research_condition: str
    manifest_path: str


@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    max_tokens: int = 512
    temperature: float = 0.0


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model_id: str
    runtime: str


def load_selected_model(path: str | Path = DEFAULT_MODEL_MANIFEST) -> SelectedModel:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelRuntimeError(f"cannot read model manifest: {manifest_path}") from exc

    if payload.get("selection_status") != "selected_reference_substrate":
        raise ModelRuntimeError("model manifest is not marked as the selected reference substrate")
    model_id = payload.get("upstream_model_id")
    family = payload.get("family")
    condition = payload.get("research_condition")
    license_spdx = (payload.get("license") or {}).get("spdx")
    if not all(isinstance(value, str) and value.strip() for value in (model_id, family, condition, license_spdx)):
        raise ModelRuntimeError("model manifest is missing required identity/license fields")

    weights = payload.get("weights") or {}
    if weights.get("bundled_in_repository") is not False:
        raise ModelRuntimeError("OI model manifest must not claim model weights are bundled")

    runtime = payload.get("runtime") or {}
    if runtime.get("remote_fallback_allowed") is not False:
        raise ModelRuntimeError("selected model manifest must explicitly forbid remote fallback")

    return SelectedModel(
        family=family,
        upstream_model_id=model_id,
        license_spdx=license_spdx,
        research_condition=condition,
        manifest_path=str(manifest_path),
    )


def _validate_loopback_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http":
        raise ModelRuntimeError("development model endpoint must use plain HTTP on loopback")
    if parsed.hostname not in _ALLOWED_LOOPBACK_HOSTS:
        raise ModelRuntimeError("development model endpoint must resolve explicitly to loopback")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ModelRuntimeError("development model endpoint may not contain credentials, query, or fragment")
    if parsed.path not in ("", "/"):
        raise ModelRuntimeError("development model endpoint must be an origin, not an arbitrary URL path")
    port = parsed.port
    if port is None or port <= 0 or port > 65535:
        raise ModelRuntimeError("development model endpoint must include a valid TCP port")
    return f"http://{parsed.hostname if parsed.hostname != '::1' else '[::1]'}:{port}"


_GROUNDED_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "citations", "quotes", "abstain"],
    "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "quotes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["segment_id", "text"],
                "properties": {
                    "segment_id": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
        },
        "abstain": {"type": "boolean"},
    },
}


class _GrammarRejected(Exception):
    """The server refused this constraint, not the request."""


class LlamaCppServerRuntime:
    """Development-only adapter for a local llama.cpp OpenAI-compatible server."""

    runtime_name = "llama.cpp-loopback-development"

    def __init__(
        self,
        endpoint: str,
        model: SelectedModel | None = None,
        *,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.endpoint = _validate_loopback_endpoint(endpoint)
        self.model = model or load_selected_model()
        self.timeout_seconds = timeout_seconds
        grammar_path = Path(__file__).resolve().parent.parent / "config" / "sofiia_grounded.v0.2.gbnf"
        if not grammar_path.is_file():
            raise ModelRuntimeError(f"grounded grammar is missing: {grammar_path}")
        self.grammar = grammar_path.read_text(encoding="utf-8")
        if timeout_seconds <= 0:
            raise ModelRuntimeError("runtime timeout must be positive")
        self._constraint: str | None = self._probe_constraint()

    def status(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime_name,
            "endpoint": self.endpoint,
            "model_id": self.model.upstream_model_id,
            "model_family": self.model.family,
            "license": self.model.license_spdx,
            "remote_fallback": False,
            "production_runtime": False,
            "structured_output": self._constraint or "unknown until the model server answers",
        }

    def _get_json(self, path: str) -> Any:
        """GET a small JSON document from the endpoint, or None if it is not there."""
        try:
            with urlopen(self.endpoint + path, timeout=min(self.timeout_seconds, 10.0)) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError):
            return None

    def _probe_constraint(self) -> str:
        """Ask the server which structured-output constraint it will actually honour.

        This exists because the previous arrangement degraded only on a refusal,
        and the refusal never came. llama.cpp enforces a GBNF `grammar` and
        ignores `response_format`. LM Studio is the other way round: it enforces
        an OpenAI-style json_schema and silently drops an unrecognised `grammar`
        field, answering 200 with free prose. So a request written for llama.cpp
        and sent to LM Studio came back as unconstrained narrative, the parser
        called it "not strict JSON", and the reader was told the verifier had
        rejected a draft when in truth nothing had constrained one.

        LM Studio publishes its own REST index at /api/v0/models; llama.cpp does
        not. The shape is checked, not merely the status code, so a server that
        answers every path with the same object cannot be mistaken for either.
        """
        for path, name in (("/api/v0/models", "json_schema"), ("/props", "grammar")):
            payload = self._get_json(path)
            if not isinstance(payload, dict):
                continue
            if name == "json_schema" and isinstance(payload.get("data"), list):
                return "json_schema"
            if name == "grammar" and "default_generation_settings" in payload:
                return "grammar"
        return None

    def _constraints(self) -> list[str]:
        """The constraints to attempt, best first, always ending unconstrained.

        A server that answered nothing is not remembered as anything, so a
        runtime constructed before the model server was started is asked again
        rather than being stuck on a guess made when nobody was listening.
        """
        if self._constraint is None:
            self._constraint = self._probe_constraint()
        first = self._constraint or "grammar"
        other = "grammar" if first == "json_schema" else "json_schema"
        return [first, other, "none"]

    @staticmethod
    def _apply_constraint(body: dict[str, Any], constraint: str, grammar: str) -> None:
        body.pop("grammar", None)
        body.pop("response_format", None)
        if constraint == "grammar":
            body["grammar"] = grammar
        elif constraint == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "sofiia_grounded",
                    "strict": True,
                    "schema": _GROUNDED_SCHEMA,
                },
            }

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        http_request = Request(
            self.endpoint + "/v1/chat/completions",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # A 400 while a constraint is attached means the server did not
            # understand the constraint; anything else is a real failure.
            if exc.code == 400 and ("grammar" in body or "response_format" in body):
                raise _GrammarRejected() from exc
            raise ModelRuntimeError("local generation request failed") from exc
        except Exception as exc:
            raise ModelRuntimeError("local generation request failed") from exc

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not request.system_prompt.strip() or not request.user_prompt.strip():
            raise ModelRuntimeError("generation requires non-empty system and user prompts")
        if request.max_tokens <= 0 or request.max_tokens > 4096:
            raise ModelRuntimeError("max_tokens must be between 1 and 4096")
        if request.temperature < 0 or request.temperature > 2:
            raise ModelRuntimeError("temperature must be between 0 and 2")

        body = {
            "model": self.model.upstream_model_id,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,
        }
        # The prose schema stays in the system prompt whatever happens here,
        # because a runtime that honours neither constraint still has to be
        # told what to write. The constraint only guarantees that the answer
        # PARSES and carries the four contract keys with the right types; it
        # guarantees nothing about truth. Whether a citation names a segment
        # that was actually retrieved, and whether a quote occurs in its
        # source, remain the verifier's job either way.
        payload = None
        last_error: Exception | None = None
        for constraint in self._constraints():
            self._apply_constraint(body, constraint, self.grammar)
            try:
                payload = self._post(body)
            except _GrammarRejected as exc:
                last_error = exc
                continue
            break
        if payload is None:
            raise ModelRuntimeError(
                "local generation request failed under every structured-output constraint"
            ) from last_error

        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelRuntimeError("local llama.cpp response did not contain a chat completion") from exc
        if not isinstance(text, str) or not text.strip():
            raise ModelRuntimeError("local llama.cpp returned an empty completion")

        returned_model = payload.get("model")
        if not isinstance(returned_model, str) or not returned_model.strip():
            returned_model = self.model.upstream_model_id
        return GenerationResult(
            text=text,
            model_id=returned_model,
            runtime=self.runtime_name,
        )

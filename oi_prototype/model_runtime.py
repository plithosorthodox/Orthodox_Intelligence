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
        if timeout_seconds <= 0:
            raise ModelRuntimeError("runtime timeout must be positive")

    def status(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime_name,
            "endpoint": self.endpoint,
            "model_id": self.model.upstream_model_id,
            "model_family": self.model.family,
            "license": self.model.license_spdx,
            "remote_fallback": False,
            "production_runtime": False,
        }

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
            # Constrain decoding to the grounded schema. Asked in prose for
            # "exactly one JSON object", OLMo 2 7B returned an object whose
            # answer string then continued "Citations:" and inlined citation
            # objects as text - twice, so the bounded correction failed and
            # Uvaha refused to answer at all. The contract was right to refuse
            # it; the model simply cannot be trusted to hold a schema by
            # instruction. A server-side grammar makes malformed output
            # unrepresentable rather than merely forbidden, and leaves the
            # verifier to judge what the fields say rather than whether they
            # parse. Servers that do not support response_format ignore it,
            # so the prose instruction stays in the system prompt as well.
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "sofiia_grounded",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["answer", "citations", "quotes", "abstain"],
                        "properties": {
                            "answer": {"type": "string"},
                            "citations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
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
                    },
                },
            },
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        http_request = Request(
            self.endpoint + "/v1/chat/completions",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # urllib surfaces several unrelated transport errors
            raise ModelRuntimeError("local llama.cpp generation request failed") from exc

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

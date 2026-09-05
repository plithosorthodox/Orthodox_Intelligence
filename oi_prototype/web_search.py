"""Optional, request-scoped Web evidence for Uvaha.

The provider in this module retrieves source chunks only.  It never delegates
answer generation, follows returned URLs, persists results, or retains evidence
between calls.  A caller must explicitly construct it with a secret supplied
outside the repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .corpus import Evidence


DEFAULT_PROVIDER_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "web_search_brave.v0.1.json"
)
BRAVE_LLM_CONTEXT_ENDPOINT = (
    "https://api.search.brave.com/res/v1/llm/context"
)
BRAVE_API_VERSION = "2026-07-31"
BRAVE_PROVIDER_ID = "brave-llm-context-v0.1"
MAX_SOURCE_URL_CHARACTERS = 2_048
MAX_SOURCE_TITLE_CHARACTERS = 500


class WebSearchError(RuntimeError):
    """Raised when optional Web evidence cannot be obtained safely."""


@dataclass(frozen=True)
class WebSearchConfig:
    manifest_version: str
    provider_id: str
    provider_name: str
    endpoint: str
    api_version: str
    authentication_header: str
    country: str
    search_language: str
    result_count: int
    maximum_number_of_urls: int
    maximum_number_of_tokens: int
    maximum_number_of_tokens_per_url: int
    maximum_number_of_snippets: int
    maximum_number_of_snippets_per_url: int
    context_threshold_mode: str
    safe_search: str
    enable_local: bool
    enable_source_metadata: bool
    timeout_seconds: float
    maximum_response_bytes: int
    maximum_query_characters: int
    maximum_query_words: int
    maximum_evidence_characters: int
    maximum_evidence_characters_per_url: int
    maximum_results_per_hostname: int


def _required_text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise WebSearchError(f"Web-search manifest requires non-empty {key}")
    return item


def _required_int(
    value: Mapping[str, object],
    key: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise WebSearchError(f"Web-search manifest requires integer {key}")
    if item < minimum or item > maximum:
        raise WebSearchError(f"Web-search manifest has out-of-range {key}")
    return item


def load_web_search_config(
    path: str | Path = DEFAULT_PROVIDER_MANIFEST,
) -> WebSearchConfig:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebSearchError("Cannot read the Web-search provider manifest") from exc
    if not isinstance(payload, dict):
        raise WebSearchError("Web-search provider manifest must be an object")

    authentication = payload.get("authentication")
    request = payload.get("request")
    handling = payload.get("data_handling")
    if not isinstance(authentication, dict) or not isinstance(request, dict):
        raise WebSearchError("Web-search provider manifest is incomplete")
    if not isinstance(handling, dict):
        raise WebSearchError("Web-search provider data handling is missing")

    endpoint = _required_text(payload, "endpoint")
    api_version = _required_text(payload, "api_version")
    provider_id = _required_text(payload, "provider_id")
    if endpoint != BRAVE_LLM_CONTEXT_ENDPOINT:
        raise WebSearchError("Web-search provider endpoint is not the approved fixed endpoint")
    if api_version != BRAVE_API_VERSION:
        raise WebSearchError("Web-search provider API version is not the approved pinned version")
    if provider_id != BRAVE_PROVIDER_ID:
        raise WebSearchError("Web-search provider identity is not approved")
    if authentication.get("bundled") is not False:
        raise WebSearchError("Web-search credentials must not be bundled")
    if authentication.get("persistent_plaintext_allowed") is not False:
        raise WebSearchError("Web-search credentials must not be stored as plaintext")
    if handling.get("enabled_by_default") is not False:
        raise WebSearchError("Optional Web search must be disabled by default")
    if handling.get("result_storage") != "request_memory_only":
        raise WebSearchError("Web-search results must remain request-scoped")
    if handling.get("remote_inference") is not False:
        raise WebSearchError("The Web provider must not perform remote inference")

    timeout = request.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise WebSearchError("Web-search timeout_seconds must be numeric")
    if timeout <= 0 or timeout > 60:
        raise WebSearchError("Web-search timeout_seconds is out of range")

    enable_local = request.get("enable_local")
    enable_metadata = request.get("enable_source_metadata")
    if not isinstance(enable_local, bool) or not isinstance(enable_metadata, bool):
        raise WebSearchError("Web-search boolean request settings are invalid")
    if enable_local:
        raise WebSearchError("Web search may not send location context by default")

    return WebSearchConfig(
        manifest_version=_required_text(payload, "manifest_version"),
        provider_id=provider_id,
        provider_name=_required_text(payload, "provider_name"),
        endpoint=endpoint,
        api_version=api_version,
        authentication_header=_required_text(authentication, "header"),
        country=_required_text(request, "country"),
        search_language=_required_text(request, "search_language"),
        result_count=_required_int(request, "result_count", minimum=1, maximum=50),
        maximum_number_of_urls=_required_int(
            request, "maximum_number_of_urls", minimum=1, maximum=10
        ),
        maximum_number_of_tokens=_required_int(
            request, "maximum_number_of_tokens", minimum=1024, maximum=4096
        ),
        maximum_number_of_tokens_per_url=_required_int(
            request, "maximum_number_of_tokens_per_url", minimum=512, maximum=2048
        ),
        maximum_number_of_snippets=_required_int(
            request, "maximum_number_of_snippets", minimum=1, maximum=64
        ),
        maximum_number_of_snippets_per_url=_required_int(
            request, "maximum_number_of_snippets_per_url", minimum=1, maximum=16
        ),
        context_threshold_mode=_required_text(request, "context_threshold_mode"),
        safe_search=_required_text(request, "safe_search"),
        enable_local=enable_local,
        enable_source_metadata=enable_metadata,
        timeout_seconds=float(timeout),
        maximum_response_bytes=_required_int(
            request, "maximum_response_bytes", minimum=1024, maximum=4 * 1024 * 1024
        ),
        maximum_query_characters=_required_int(
            request, "maximum_query_characters", minimum=1, maximum=400
        ),
        maximum_query_words=_required_int(
            request, "maximum_query_words", minimum=1, maximum=50
        ),
        maximum_evidence_characters=_required_int(
            request, "maximum_evidence_characters", minimum=512, maximum=8000
        ),
        maximum_evidence_characters_per_url=_required_int(
            request,
            "maximum_evidence_characters_per_url",
            minimum=128,
            maximum=4000,
        ),
        maximum_results_per_hostname=_required_int(
            request, "maximum_results_per_hostname", minimum=1, maximum=4
        ),
    )


@dataclass(frozen=True)
class WebEvidenceBundle:
    """Immutable evidence plus a request-local resolver.

    No provider-level cache is used: every call returns a new bundle, and the
    bundle retains only the displayed source chunks for as long as its caller
    retains the request result.
    """

    evidence: tuple[Evidence, ...]
    provider_id: str
    retrieved_at: str

    def resolve(self, segment_id: str) -> Evidence | None:
        for item in self.evidence:
            if item.segment_id != segment_id:
                continue
            actual_hash = hashlib.sha256(
                item.display_text.encode("utf-8")
            ).hexdigest()
            if (
                item.origin != "web"
                or item.provider != self.provider_id
                or item.source_class != "web"
                or actual_hash != item.content_sha256
            ):
                return None
            return item
        return None


WebTransport = Callable[[Request, float, int], bytes]
Clock = Callable[[], datetime]


class _NoRedirect(HTTPRedirectHandler):
    """Keep the subscription credential pinned to the approved origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_transport(
    request: Request,
    timeout_seconds: float,
    maximum_response_bytes: int,
) -> bytes:
    try:
        opener = build_opener(_NoRedirect())
        with opener.open(request, timeout=timeout_seconds) as response:
            payload = response.read(maximum_response_bytes + 1)
    except HTTPError as exc:
        raise WebSearchError(
            f"Web-search provider returned HTTP {exc.code}"
        ) from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise WebSearchError("Web-search provider request failed") from exc
    if len(payload) > maximum_response_bytes:
        raise WebSearchError("Web-search provider response exceeded the size limit")
    return payload


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def derive_web_query(question: str, *, maximum_characters: int = 400, maximum_words: int = 50) -> str:
    """Create the only user-derived value sent to the search provider.

    Conversation history, retrieved local evidence, device data, and location
    never enter this function. The bounds also keep a long chat-style prompt
    from being forwarded wholesale.
    """
    normalized = _normalized_text(question)
    words = normalized.split()[:maximum_words]
    query = " ".join(words)
    if len(query) > maximum_characters:
        query = query[:maximum_characters].rsplit(" ", 1)[0].strip()
    return query


def _approved_source_url(value: object) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or (port is not None and not 1 <= port <= 65535)
    ):
        return None
    canonical = urlunsplit(
        ("https", parsed.netloc, parsed.path or "/", parsed.query, "")
    )
    if len(canonical) > MAX_SOURCE_URL_CHARACTERS:
        return None
    return canonical, parsed.hostname.casefold()


def _published_at(
    sources: Mapping[str, object],
    raw_url: str,
) -> str:
    source = sources.get(raw_url)
    if not isinstance(source, dict):
        return ""
    age = source.get("age")
    if not isinstance(age, list) or len(age) < 4 or not isinstance(age[3], str):
        return ""
    candidate = age[3].strip()
    if not candidate:
        return ""
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        return ""
    return _utc_timestamp(parsed)


class BraveLlmContextProvider:
    """Brave's raw LLM Context retrieval endpoint, never its Answers API."""

    def __init__(
        self,
        api_key: str,
        config_path: str | Path = DEFAULT_PROVIDER_MANIFEST,
        *,
        transport: WebTransport | None = None,
        clock: Clock | None = None,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise WebSearchError("A Web-search API key is required")
        if any(ord(character) < 32 for character in api_key):
            raise WebSearchError("The Web-search API key is invalid")
        self._api_key = api_key.strip()
        self.config = load_web_search_config(config_path)
        self._transport = transport or _default_transport
        self._clock = clock or _utc_now

    def status(self) -> dict[str, object]:
        """Return only non-secret provider metadata."""
        return {
            "provider": self.config.provider_id,
            "endpoint": self.config.endpoint,
            "api_version": self.config.api_version,
            "enabled_by_default": False,
            "remote_inference": False,
            "result_storage": "request_memory_only",
        }

    def search(self, query: str) -> WebEvidenceBundle:
        normalized_query = _normalized_text(query)
        if not normalized_query:
            raise WebSearchError("Web search requires a non-empty query")
        if len(normalized_query) > self.config.maximum_query_characters:
            raise WebSearchError("Web search query exceeds the character limit")
        if len(normalized_query.split()) > self.config.maximum_query_words:
            raise WebSearchError("Web search query exceeds the word limit")

        request_body = {
            "q": normalized_query,
            "country": self.config.country,
            "search_lang": self.config.search_language,
            "count": self.config.result_count,
            "maximum_number_of_urls": self.config.maximum_number_of_urls,
            "maximum_number_of_tokens": self.config.maximum_number_of_tokens,
            "maximum_number_of_tokens_per_url": (
                self.config.maximum_number_of_tokens_per_url
            ),
            "maximum_number_of_snippets": self.config.maximum_number_of_snippets,
            "maximum_number_of_snippets_per_url": (
                self.config.maximum_number_of_snippets_per_url
            ),
            "context_threshold_mode": self.config.context_threshold_mode,
            "safesearch": self.config.safe_search,
            "enable_local": self.config.enable_local,
            "enable_source_metadata": self.config.enable_source_metadata,
        }
        encoded = json.dumps(
            request_body,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.config.endpoint,
            data=encoded,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                self.config.authentication_header: self._api_key,
                "Api-Version": self.config.api_version,
            },
            method="POST",
        )
        try:
            raw = self._transport(
                request,
                self.config.timeout_seconds,
                self.config.maximum_response_bytes,
            )
        except WebSearchError:
            raise
        except Exception as exc:
            raise WebSearchError("Web-search provider request failed") from exc
        if not isinstance(raw, bytes):
            raise WebSearchError("Web-search transport returned an invalid response")
        if len(raw) > self.config.maximum_response_bytes:
            raise WebSearchError("Web-search provider response exceeded the size limit")

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WebSearchError("Web-search provider returned invalid JSON") from exc
        return self._to_evidence(payload)

    def _to_evidence(self, payload: object) -> WebEvidenceBundle:
        if not isinstance(payload, dict):
            raise WebSearchError("Web-search provider response must be an object")
        grounding = payload.get("grounding")
        if grounding is None:
            generic: object = []
        elif isinstance(grounding, dict):
            generic = grounding.get("generic", [])
        else:
            raise WebSearchError("Web-search provider grounding is invalid")
        if not isinstance(generic, list):
            raise WebSearchError("Web-search provider results are invalid")
        sources_value = payload.get("sources", {})
        sources: Mapping[str, object]
        if isinstance(sources_value, dict):
            sources = sources_value
        else:
            sources = {}

        retrieved_at = _utc_timestamp(self._clock())
        evidence: list[Evidence] = []
        seen_urls: set[str] = set()
        hostname_counts: dict[str, int] = {}
        used_characters = 0

        for result in generic:
            if len(evidence) >= self.config.maximum_number_of_urls:
                break
            if not isinstance(result, dict):
                continue
            raw_url = result.get("url")
            approved = _approved_source_url(raw_url)
            if approved is None:
                continue
            url, hostname = approved
            if url in seen_urls:
                continue
            if hostname_counts.get(hostname, 0) >= self.config.maximum_results_per_hostname:
                continue

            snippets = result.get("snippets")
            if not isinstance(snippets, list):
                continue
            selected_snippets: list[str] = []
            per_url_characters = 0
            for snippet in snippets[: self.config.maximum_number_of_snippets_per_url]:
                text = _normalized_text(snippet)
                if not text:
                    continue
                added = len(text) + (2 if selected_snippets else 0)
                if per_url_characters + added > self.config.maximum_evidence_characters_per_url:
                    continue
                if used_characters + per_url_characters + added > self.config.maximum_evidence_characters:
                    continue
                selected_snippets.append(text)
                per_url_characters += added
            if not selected_snippets:
                continue

            display_text = "\n\n".join(selected_snippets)
            content_hash = hashlib.sha256(display_text.encode("utf-8")).hexdigest()
            record_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
            segment_hash = hashlib.sha256(
                (url + "\0" + content_hash).encode("utf-8")
            ).hexdigest()[:20]
            title = (
                _normalized_text(result.get("title"))[:MAX_SOURCE_TITLE_CHARACTERS]
                or hostname
            )
            raw_url_text = raw_url if isinstance(raw_url, str) else url
            evidence.append(
                Evidence(
                    record_id=f"web:{record_hash}",
                    segment_id=f"webtext:{segment_hash}",
                    title=title,
                    citation_label=f"{title} · {hostname}",
                    source_locator=url,
                    source_class="web",
                    language=self.config.search_language,
                    display_text=display_text,
                    content_sha256=content_hash,
                    exact_text=False,
                    score=float(len(evidence)),
                    origin="web",
                    provider=self.config.provider_id,
                    published_at=_published_at(sources, raw_url_text),
                    retrieved_at=retrieved_at,
                    citation_ref="",
                )
            )
            seen_urls.add(url)
            hostname_counts[hostname] = hostname_counts.get(hostname, 0) + 1
            used_characters += per_url_characters

        return WebEvidenceBundle(
            evidence=tuple(evidence),
            provider_id=self.config.provider_id,
            retrieved_at=retrieved_at,
        )

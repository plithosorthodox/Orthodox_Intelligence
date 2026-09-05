"""Evidence-first answer path for the executable Uvaha / OI prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hmac
import re

from . import __version__
from .corpus import Evidence, EvidenceStore
from .grounded_generation import (
    GroundedGenerationError,
    LocalGenerationError,
    MalformedGenerationError,
    SOFIIA_DISPLAY_NAME,
    TruncatedGenerationError,
    generate_verified,
)
from .policy import BoundaryPolicy
from .web_search import WebEvidenceBundle, WebSearchError, derive_web_query


_CONTEXTUAL_REFERENCE = re.compile(
    r"\b(?:he|him|his|she|her|hers|they|them|their|theirs|it|its|"
    r"this|that|these|those|former|latter|you|your|yours|then|there|more)\b",
    re.IGNORECASE,
)
_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_MAX_CONTEXT_SOURCES = 4


def _contextual_retrieval_question(
    question: str,
    history: tuple[dict[str, str], ...],
    context_titles: tuple[str, ...] = (),
) -> str:
    """Carry the last user subject into an explicitly referential follow-up.

    This is local deterministic query context only. The original question,
    without history, remains the only value eligible for optional Web search.
    """

    if not _CONTEXTUAL_REFERENCE.search(question):
        return question
    prefixes = [" ".join(title.split())[:500] for title in context_titles if title]
    for turn in reversed(history):
        if not isinstance(turn, dict) or turn.get("role") != "user":
            continue
        content = turn.get("content")
        if not isinstance(content, str):
            continue
        content = " ".join(content.split())
        if not content:
            continue
        prefixes.append(content)
        break
    if not prefixes:
        return question
    prefix = " ".join(prefixes)
    available = max(0, 4_000 - len(question) - 1)
    if not available:
        return question
    return f"{prefix[:available]} {question}"


def _trusted_context_titles(
    evidence_store: object,
    context_sources: tuple[dict[str, str], ...],
) -> tuple[str, ...]:
    """Resolve browser-held references back through the current local corpus.

    Browser storage is untrusted. Neither its saved title nor its saved source
    text is accepted here; a source contributes only when its id resolves in
    the currently installed corpus and its immutable content hash still
    matches.
    """

    resolve = getattr(evidence_store, "resolve", None)
    if not callable(resolve):
        return ()
    titles: list[str] = []
    seen: set[str] = set()
    for source in context_sources[:_MAX_CONTEXT_SOURCES]:
        if not isinstance(source, dict):
            continue
        segment_id = source.get("segment_id")
        expected_hash = source.get("content_sha256")
        if (
            not isinstance(segment_id, str)
            or not segment_id
            or not isinstance(expected_hash, str)
            or _SHA256.fullmatch(expected_hash) is None
        ):
            continue
        item = resolve(segment_id)
        if (
            item is None
            or getattr(item, "origin", "local") != "local"
            or not hmac.compare_digest(
                item.content_sha256.casefold(), expected_hash.casefold()
            )
        ):
            continue
        title = " ".join(item.title.split())[:500]
        if title and title not in seen:
            titles.append(title)
            seen.add(title)
    return tuple(titles)


@dataclass(frozen=True)
class Answer:
    response_class: str
    intent: str
    text: str
    evidence: tuple[Evidence, ...]
    boundary_rule_id: str | None
    versions: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["evidence"] = [item.as_dict() for item in self.evidence]
        return value


class PrototypeEngine:
    """Evidence-first Uvaha prototype with an optional local Sofiia runtime."""

    def __init__(
        self,
        evidence_store: EvidenceStore,
        policy: BoundaryPolicy,
        model_runtime: object | None = None,
        web_search_provider: object | None = None,
    ):
        self.evidence_store = evidence_store
        self.policy = policy
        self.model_runtime = model_runtime
        self.web_search_provider = web_search_provider

    @property
    def versions(self) -> dict[str, str]:
        if self.model_runtime is None:
            model = "none-extractive-prototype"
            substrate = "not-applicable"
            verifier = "prototype-verifier-v0.2"
        else:
            model = SOFIIA_DISPLAY_NAME
            selected = getattr(self.model_runtime, "model", None)
            substrate = getattr(
                selected,
                "upstream_model_id",
                "allenai/OLMo-2-1124-7B-Instruct",
            )
            verifier = "prototype-verifier-v0.4"
        versions = {
            "application": __version__,
            "model": model,
            "substrate": substrate,
            "elf": "none",
            "corpus": self.evidence_store.corpus_version,
            "retriever": getattr(
                self.evidence_store, "search_version", "demo-fts5-bm25-v0.1"
            ),
            "boundary_policy": self.policy.version,
            "verifier": verifier,
        }
        versions["web_search"] = (
            getattr(
                getattr(self.web_search_provider, "config", None),
                "provider_id",
                "disabled",
            )
            if self.web_search_provider is not None
            else "disabled"
        )
        return versions

    def status(self) -> dict[str, object]:
        runtime_status = None
        if self.model_runtime is not None:
            status_method = getattr(self.model_runtime, "status", None)
            if callable(status_method):
                runtime_status = status_method()
        web_status = None
        if self.web_search_provider is not None:
            status_method = getattr(self.web_search_provider, "status", None)
            if callable(status_method):
                web_status = status_method()
        return {
            "name": "Uvaha research prototype",
            "research_program": "Orthodox Intelligence",
            "selected_model": SOFIIA_DISPLAY_NAME,
            "offline_core": True,
            "generative_model_loaded": self.model_runtime is not None,
            "web_available": self.web_search_provider is not None,
            "web_search": web_status,
            "model_runtime": runtime_status,
            "corpus_id": self.evidence_store.corpus_id,
            "corpus_mode": (
                "plithos"
                if self.evidence_store.corpus_id == "plithos-english"
                else "demonstration"
            ),
            "record_count": self.evidence_store.record_count,
            "entity_count": getattr(self.evidence_store, "entity_count", None),
            "features": list(getattr(self.evidence_store, "features", ())),
            "supports_exact_text": bool(
                getattr(self.evidence_store, "supports_exact_text", False)
            ),
            "versions": self.versions,
        }

    def ask(
        self,
        question: str,
        *,
        source_mode: str = "local_only",
        history: tuple[dict[str, str], ...] = (),
        context_sources: tuple[dict[str, str], ...] = (),
    ) -> Answer:
        question = " ".join(question.split())
        if not question:
            return self._answer(
                "abstention",
                "invalid",
                "Enter a question before asking the prototype.",
            )
        if len(question) > 4_000:
            return self._answer(
                "abstention",
                "invalid",
                "This prototype accepts questions of at most 4,000 characters.",
            )
        if source_mode not in {"automatic", "local_only"}:
            return self._answer(
                "abstention",
                "invalid",
                "Choose automatic or local-only sources.",
            )

        history_question = _contextual_retrieval_question(question, history)
        context_titles = _trusted_context_titles(
            self.evidence_store,
            context_sources,
        )
        retrieval_question = _contextual_retrieval_question(
            question,
            history,
            context_titles,
        )
        decision = self.policy.classify(question)
        if decision.rule_id is None and history_question != question:
            contextual_decision = self.policy.classify(history_question)
            if contextual_decision.rule_id is not None:
                decision = contextual_decision

        if (
            decision.rule_id == "EXACT-TEXT-DEMO-01"
            and getattr(self.evidence_store, "supports_exact_text", False)
        ):
            exact = tuple(
                item
                for item in self.evidence_store.search(retrieval_question)
                if item.exact_text
            )
            if exact:
                return self._answer(
                    "evidence",
                    "exact_text",
                    exact[0].display_text,
                    evidence=exact,
                )
            return self._answer(
                "abstention",
                "exact_text",
                "I couldn't find that exact text in the installed sources.",
                boundary_rule_id=decision.rule_id,
            )

        if decision.response is not None:
            return self._answer(
                decision.response_class or "boundary",
                decision.intent,
                decision.response,
                boundary_rule_id=decision.rule_id,
            )

        retrieval = None
        retrieve = getattr(self.evidence_store, "retrieve", None)
        if callable(retrieve):
            retrieval = retrieve(
                retrieval_question,
                limit=8,
            )
            evidence = tuple(retrieval.evidence if retrieval.sufficient else ())
        else:
            evidence = tuple(self.evidence_store.search(retrieval_question))

        web_bundle: WebEvidenceBundle | None = None
        if (
            not evidence
            and source_mode == "automatic"
            and self.web_search_provider is not None
        ):
            try:
                web_bundle = self.web_search_provider.search(derive_web_query(question))
            except WebSearchError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "Web search is unavailable right now.",
                    boundary_rule_id="WEB-SEARCH-FAILURE",
                )
            web_evidence = tuple(web_bundle.evidence)
            partial_local = (
                tuple(
                    item
                    for item in retrieval.evidence
                    if len(item.display_text) <= 3_000
                )[:1]
                if retrieval is not None
                and retrieval.plan.has_corpus_cue
                and web_evidence
                else ()
            )
            evidence = (partial_local + web_evidence)[:8]

        if not evidence:
            suggestion = None
            suggest = getattr(self.evidence_store, "suggest", None)
            if callable(suggest):
                suggestion = suggest(question)
            if self.evidence_store.corpus_id == "plithos-english":
                text = "I couldn't find enough reliable sources for that."
            else:
                text = (
                    "I couldn't find enough reliable sources for that."
                )
            if suggestion:
                text += f' Did you mean "{suggestion}"?'
            return self._answer(
                "abstention",
                decision.intent,
                text,
            )

        if self.model_runtime is not None:
            try:
                generated = generate_verified(
                    self.model_runtime,
                    question,
                    evidence,
                    history=history,
                )
            except LocalGenerationError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "The local model didn't finish. Please try again.",
                    boundary_rule_id="MODEL-RUNTIME-FAILURE",
                )
            except TruncatedGenerationError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "The local model stopped before finishing its answer. Please try again.",
                    boundary_rule_id="MODEL-OUTPUT-TRUNCATED",
                )
            except MalformedGenerationError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "The local model returned an unreadable answer. Please try again.",
                    boundary_rule_id="MODEL-OUTPUT-MALFORMED",
                )
            except GroundedGenerationError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "I couldn't produce a well-supported answer. Try rephrasing the question.",
                    boundary_rule_id="VERIFIER-FAILURE",
                )
            if generated.abstained:
                return self._answer(
                    "abstention",
                    decision.intent,
                    generated.text,
                )
            return self._answer(
                "generated",
                decision.intent,
                generated.text,
                evidence=generated.evidence,
                evidence_resolver=web_bundle,
            )

        label = "Sources found. Connect the local model to synthesize an answer."
        return self._answer(
            "evidence",
            decision.intent,
            label,
            evidence=evidence,
            evidence_resolver=web_bundle,
        )

    def _answer(
        self,
        response_class: str,
        intent: str,
        text: str,
        evidence: tuple[Evidence, ...] = (),
        boundary_rule_id: str | None = None,
        evidence_resolver: object | None = None,
    ) -> Answer:
        verified: list[Evidence] = []
        for item in evidence:
            resolved = self.evidence_store.resolve(item.segment_id)
            if resolved is None and evidence_resolver is not None:
                resolve = getattr(evidence_resolver, "resolve", None)
                if callable(resolve):
                    resolved = resolve(item.segment_id)
            if resolved is None or resolved.content_sha256 != item.content_sha256:
                return Answer(
                    response_class="abstention",
                    intent=intent,
                    text="Evidence verification failed, so the prototype did not answer.",
                    evidence=(),
                    boundary_rule_id="VERIFIER-FAILURE",
                    versions=self.versions,
                )
            verified.append(item)
        return Answer(
            response_class=response_class,
            intent=intent,
            text=text,
            evidence=tuple(verified),
            boundary_rule_id=boundary_rule_id,
            versions=self.versions,
        )

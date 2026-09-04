"""Evidence-first answer path for the executable Uvaha / OI prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import __version__
from .corpus import Evidence, EvidenceStore
from .grounded_generation import (
    GroundedGenerationError,
    SOFIIA_DISPLAY_NAME,
    generate_verified,
)
from .policy import BoundaryPolicy


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
    ):
        self.evidence_store = evidence_store
        self.policy = policy
        self.model_runtime = model_runtime

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
            verifier = "prototype-verifier-v0.3"
        return {
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

    def status(self) -> dict[str, object]:
        runtime_status = None
        if self.model_runtime is not None:
            status_method = getattr(self.model_runtime, "status", None)
            if callable(status_method):
                runtime_status = status_method()
        return {
            "name": "Uvaha research prototype",
            "research_program": "Orthodox Intelligence",
            "selected_model": SOFIIA_DISPLAY_NAME,
            "offline_core": True,
            "generative_model_loaded": self.model_runtime is not None,
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

    def ask(self, question: str) -> Answer:
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

        decision = self.policy.classify(question)

        if (
            decision.rule_id == "EXACT-TEXT-DEMO-01"
            and getattr(self.evidence_store, "supports_exact_text", False)
        ):
            exact = tuple(
                item
                for item in self.evidence_store.search(question)
                if item.exact_text
            )
            if exact:
                return self._answer(
                    "evidence",
                    "exact_text",
                    "Exact text was retrieved from the installed Plithos evidence package. The prototype did not reconstruct it from model memory.",
                    evidence=exact,
                )
            return self._answer(
                "abstention",
                "exact_text",
                "The installed Plithos corpus did not resolve an eligible exact-text record for that request. No text was reconstructed from model memory.",
                boundary_rule_id=decision.rule_id,
            )

        if decision.response is not None:
            return self._answer(
                decision.response_class or "boundary",
                decision.intent,
                decision.response,
                boundary_rule_id=decision.rule_id,
            )

        evidence = tuple(self.evidence_store.search(question))
        if not evidence:
            suggestion = None
            suggest = getattr(self.evidence_store, "suggest", None)
            if callable(suggest):
                suggestion = suggest(question)
            if self.evidence_store.corpus_id == "plithos-english":
                text = (
                    "The installed Plithos corpus does not contain enough evidence for that query. "
                    "No model-memory answer was substituted."
                )
            else:
                text = (
                    "The installed demonstration corpus does not contain enough evidence "
                    "to answer that question. No model-memory answer was substituted."
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
                )
            except GroundedGenerationError:
                return self._answer(
                    "abstention",
                    decision.intent,
                    "Sofiia generated a draft, but it did not pass the local citation and quotation verifier after one bounded correction. No unverified answer was shown.",
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
            )

        label = (
            "The installed Plithos corpus contains the verified evidence below. "
            "Sofiia v0.1 is selected but no local model runtime is connected, so "
            "this process is retrieving evidence rather than generating an answer."
            if self.evidence_store.corpus_id == "plithos-english"
            else
            "The demonstration corpus contains the passages below. This first "
            "vertical slice retrieves and verifies evidence; it does not yet generate "
            "a synthesized answer."
        )
        return self._answer(
            "evidence",
            decision.intent,
            label,
            evidence=evidence,
        )

    def _answer(
        self,
        response_class: str,
        intent: str,
        text: str,
        evidence: tuple[Evidence, ...] = (),
        boundary_rule_id: str | None = None,
    ) -> Answer:
        verified: list[Evidence] = []
        for item in evidence:
            resolved = self.evidence_store.resolve(item.segment_id)
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

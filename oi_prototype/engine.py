"""Evidence-first answer path for the executable OI prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import __version__
from .corpus import Evidence, EvidenceStore
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
    """A deterministic retrieval vertical slice; it deliberately contains no LLM."""

    def __init__(self, evidence_store: EvidenceStore, policy: BoundaryPolicy):
        self.evidence_store = evidence_store
        self.policy = policy

    @property
    def versions(self) -> dict[str, str]:
        return {
            "application": __version__,
            "model": "none-extractive-prototype",
            "substrate": "not-applicable",
            "elf": "none",
            "corpus": self.evidence_store.corpus_version,
            "retriever": getattr(
                self.evidence_store, "search_version", "demo-fts5-bm25-v0.1"
            ),
            "boundary_policy": self.policy.version,
            "verifier": "prototype-verifier-v0.2",
        }

    def status(self) -> dict[str, object]:
        return {
            "name": "Orthodox Intelligence research prototype",
            "offline_core": True,
            "generative_model_loaded": False,
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
            text = (
                "The installed corpus does not contain enough evidence for that query. "
                "No model-memory answer was substituted."
            )
            if suggestion:
                text += f' Did you mean "{suggestion}"?'
            return self._answer(
                "abstention",
                decision.intent,
                text,
            )

        label = (
            "The installed Plithos corpus contains the verified evidence below. "
            "This prototype searches and verifies evidence; it does not yet generate "
            "a synthesized language-model answer."
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

"""Evidence-first answer path for the first executable OI prototype."""

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
    """A deterministic vertical slice; it deliberately contains no LLM."""

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
            "boundary_policy": self.policy.version,
            "verifier": "prototype-verifier-v0.1",
        }

    def status(self) -> dict[str, object]:
        return {
            "name": "Orthodox Intelligence research prototype",
            "offline_core": True,
            "generative_model_loaded": False,
            "corpus_id": self.evidence_store.corpus_id,
            "record_count": self.evidence_store.record_count,
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
        if decision.response is not None:
            return self._answer(
                decision.response_class or "boundary",
                decision.intent,
                decision.response,
                boundary_rule_id=decision.rule_id,
            )

        evidence = tuple(self.evidence_store.search(question))
        if not evidence:
            return self._answer(
                "abstention",
                decision.intent,
                "The installed demonstration corpus does not contain enough evidence to answer that question. No model-memory answer was substituted.",
            )
        return self._answer(
            "evidence",
            decision.intent,
            "The demonstration corpus contains the passages below. This first vertical slice retrieves and verifies evidence; it does not yet generate a synthesized answer.",
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

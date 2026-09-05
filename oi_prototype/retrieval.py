"""Deterministic query planning and evidence-set selection.

The local model is deliberately not used to rewrite retrieval queries.  On the
reference CPU path that would add another multi-minute generation, and it would
make the evidence boundary depend on unverified model output.  Instead this
module extracts a small set of lexical concept lanes and records whether the
selected evidence actually covers them.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Iterable, Mapping

from .corpus import Evidence
from .plithos_search import ALIAS_FAMILIES, normalize_search, transliterate_latin


_WORD = re.compile(r"[^\W_]+", re.UNICODE)
_SPACE = re.compile(r"\s+")
_LEADING_REQUEST = re.compile(
    r"^(?:(?:please\s+)?(?:compare|contrast|explain|describe|summarize|"
    r"tell\s+me\s+about|what\s+(?:is|are|was|were|does|do|did)|"
    r"who\s+(?:is|are|was|were)|why\s+(?:is|are|was|were|does|do|did)|"
    r"how\s+(?:is|are|was|were|does|do|did))\s+)+",
    re.IGNORECASE,
)
_RELATION = re.compile(
    r"\s+(?:relate(?:s|d)?\s+to|connect(?:s|ed)?\s+(?:to|with)|"
    r"in\s+relation\s+to|versus|vs\.?|compared\s+(?:with|to))\s+",
    re.IGNORECASE,
)
_TRAILING_REQUEST = re.compile(
    r"\s+(?:connected|related|different|similar|compared|contrast(?:ed)?)$",
    re.IGNORECASE,
)
_LIST_SEPARATOR = re.compile(r"\s*(?:,|;|\band\b|\bversus\b|\bvs\.?)\s*", re.IGNORECASE)

# These words describe the request rather than the subject being retrieved.
# Honorifics are retained as domain cues, but are optional for lexical coverage
# because a canonical title may say "Venerable Mary" where the user says
# "Saint Mary".
_QUERY_NOISE = frozenset(
    {
        "a", "about", "all", "an", "and", "are", "as", "at", "be", "been",
        "between", "by", "can", "cause", "causes", "compare", "compared",
        "connect", "connected", "contrast", "describe", "did", "different",
        "do", "does", "explain", "for", "from", "how", "i", "in", "is",
        "he", "her", "hers", "him", "his", "it", "its", "me", "of", "on",
        "or", "present", "related", "relationship", "she", "their", "theirs",
        "them", "they", "this", "these", "that", "those",
        "say", "show", "similar", "source", "sources", "summarize", "tell",
        "that", "the", "this", "to", "us", "versus", "was", "were", "what",
        "when", "where", "which", "who", "why", "with", "you", "your",
    }
)
_OPTIONAL_HONORIFICS = frozenset(
    {"blessed", "holy", "righteous", "saint", "saints", "st", "venerable"}
)
_CORPUS_CUES = frozenset(
    {
        "ascetic", "bible", "biblical", "canon", "christian", "christianity",
        "church", "confession", "council", "fast", "fasting", "gospel",
        "hagiography", "incarnation", "liturgy", "orthodox", "orthodoxy",
        "patristic", "plithos", "prayer", "repentance", "resurrection",
        "sacrament", "scripture", "saint", "saints", "theology",
    }
)
_ALIAS_CANONICAL = {
    value: canonical
    for canonical, aliases in ALIAS_FAMILIES
    for value in (canonical, *aliases)
}


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return _SPACE.sub(" ", text.casefold()).strip(" \t\r\n.,;:!?()[]{}\"'“”‘’")


def _tokens(value: object, *, optional_honorifics: bool = True) -> tuple[str, ...]:
    result: list[str] = []
    normalized = normalize_search(value)
    token_text = transliterate_latin(normalized) or normalized
    for raw_token in _WORD.findall(token_text):
        token = _ALIAS_CANONICAL.get(raw_token, raw_token)
        if token in _QUERY_NOISE:
            continue
        if optional_honorifics and token in _OPTIONAL_HONORIFICS:
            continue
        if token not in result:
            result.append(token)
    return tuple(result)


@dataclass(frozen=True)
class ConceptLane:
    """One independently retrievable subject in a user's question."""

    label: str
    query: str
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class QueryPlan:
    """A deterministic retrieval plan for one question."""

    question: str
    combined_query: str
    concepts: tuple[ConceptLane, ...]
    requires_full_coverage: bool
    has_corpus_cue: bool


@dataclass(frozen=True)
class RetrievalResult:
    """Selected evidence plus an explicit relevance/coverage decision."""

    evidence: tuple[Evidence, ...]
    plan: QueryPlan
    covered_concepts: tuple[str, ...]
    sufficient: bool
    reason: str
    exact_text: bool = False


@dataclass(frozen=True)
class Candidate:
    evidence: Evidence
    concepts: frozenset[str]
    match_strength: int
    first_rank: int


def plan_query(question: str) -> QueryPlan:
    """Extract a combined lexical query and bounded concept lanes.

    Commas, comparisons, and explicit relationship wording identify questions
    which must cover more than one subject.  The original phrase is retained as
    each lane's search query so title phrases such as ``Mary of Egypt`` remain
    available to the name ranker; noise-free tokens are used for verification.
    """

    normalized = _normalize(question)
    body = _LEADING_REQUEST.sub("", normalized)
    body = _TRAILING_REQUEST.sub("", body)
    relation_marked = bool(_RELATION.search(body))
    body = _RELATION.sub(" | ", body)
    list_marked = bool(re.search(r",|;|\b(?:and|versus|vs\.?)\b", body, re.IGNORECASE))
    if relation_marked or list_marked:
        pieces = []
        for relation_piece in body.split("|"):
            pieces.extend(_LIST_SEPARATOR.split(relation_piece))
    else:
        pieces = [body]

    concepts: list[ConceptLane] = []
    seen_tokens: set[tuple[str, ...]] = set()
    for piece in pieces:
        label = _TRAILING_REQUEST.sub("", _LEADING_REQUEST.sub("", _normalize(piece)))
        tokens = _tokens(label)
        if not tokens or tokens in seen_tokens:
            continue
        seen_tokens.add(tokens)
        concepts.append(ConceptLane(label=label, query=label, tokens=tokens))
        if len(concepts) >= 4:
            break

    if not concepts:
        fallback_tokens = _tokens(normalized)
        if fallback_tokens:
            concepts.append(
                ConceptLane(
                    label=normalized,
                    query=normalized,
                    tokens=fallback_tokens,
                )
            )

    combined_tokens: list[str] = []
    for concept in concepts:
        for token in concept.tokens:
            if token not in combined_tokens:
                combined_tokens.append(token)

    raw_tokens = set(_WORD.findall(normalized))
    return QueryPlan(
        question=question,
        combined_query=" ".join(combined_tokens),
        concepts=tuple(concepts),
        requires_full_coverage=len(concepts) > 1,
        has_corpus_cue=bool(raw_tokens.intersection(_CORPUS_CUES | _OPTIONAL_HONORIFICS)),
    )


def evidence_match_strength(item: Evidence, concept: ConceptLane, plan: QueryPlan) -> int | None:
    """Return a conservative match class or ``None`` for an irrelevant hit.

    A title match is accepted even for a single token (for example Nicholas or
    Incarnation).  Body-only matches need either two informative terms or an
    explicit corpus-domain cue.  This keeps a stray occurrence of a general
    term such as ``inflation`` from routing an otherwise general question into
    Plithos merely because FTS found one word somewhere in a long work.
    """

    required = set(concept.tokens)
    if not required:
        return None
    title_tokens = set(_tokens(item.title, optional_honorifics=False)) - _QUERY_NOISE
    body_tokens = set(_tokens(item.display_text, optional_honorifics=False)) - _QUERY_NOISE
    if required.issubset(title_tokens):
        return 0
    if required.issubset(title_tokens | body_tokens) and plan.has_corpus_cue:
        return 1
    return None


def merge_candidates(
    plan: QueryPlan,
    ranked_evidence: Mapping[str, Iterable[Evidence]],
    *,
    limit: int,
) -> RetrievalResult:
    """Merge per-query candidates with concept coverage and entity diversity."""

    limit = max(1, min(int(limit), 10))
    by_segment: dict[str, Candidate] = {}
    rank_counter = 0
    for _query, items in ranked_evidence.items():
        for item in items:
            covered: set[str] = set()
            strengths: list[int] = []
            for concept in plan.concepts:
                strength = evidence_match_strength(item, concept, plan)
                if strength is not None:
                    covered.add(concept.label)
                    strengths.append(strength)
            if not covered:
                rank_counter += 1
                continue
            candidate = Candidate(
                evidence=item,
                concepts=frozenset(covered),
                match_strength=min(strengths),
                first_rank=rank_counter,
            )
            existing = by_segment.get(item.segment_id)
            if existing is None:
                by_segment[item.segment_id] = candidate
            else:
                by_segment[item.segment_id] = Candidate(
                    evidence=existing.evidence,
                    concepts=existing.concepts | candidate.concepts,
                    match_strength=min(existing.match_strength, candidate.match_strength),
                    first_rank=min(existing.first_rank, candidate.first_rank),
                )
            rank_counter += 1

    remaining = list(by_segment.values())
    selected: list[Candidate] = []
    uncovered = {concept.label for concept in plan.concepts}
    concept_counts = {concept.label: 0 for concept in plan.concepts}
    selected_records: set[str] = set()
    selected_classes: set[str] = set()

    while remaining and len(selected) < limit:
        candidate = min(
            remaining,
            key=lambda value: (
                0 if value.concepts.intersection(uncovered) else 1,
                value.match_strength,
                -len(value.concepts.intersection(uncovered)),
                0 if value.evidence.record_id not in selected_records else 1,
                min((concept_counts[label] for label in value.concepts), default=0),
                value.first_rank,
                0 if value.evidence.source_class not in selected_classes else 1,
                value.evidence.segment_id,
            ),
        )
        remaining.remove(candidate)
        selected.append(candidate)
        uncovered.difference_update(candidate.concepts)
        for label in candidate.concepts:
            concept_counts[label] += 1
        selected_records.add(candidate.evidence.record_id)
        selected_classes.add(candidate.evidence.source_class)

    covered = tuple(
        concept.label
        for concept in plan.concepts
        if any(concept.label in candidate.concepts for candidate in selected)
    )
    all_covered = len(covered) == len(plan.concepts) and bool(plan.concepts)
    distinct_records = len({candidate.evidence.record_id for candidate in selected})
    enough_sources = not plan.requires_full_coverage or distinct_records >= 2
    sufficient = all_covered and enough_sources
    if not selected:
        reason = "no relevant corpus evidence"
    elif not all_covered:
        reason = "corpus evidence does not cover every requested concept"
    elif not enough_sources:
        reason = "multi-concept synthesis requires at least two distinct records"
    else:
        reason = "corpus evidence covers the retrieval plan"
    return RetrievalResult(
        evidence=tuple(candidate.evidence for candidate in selected),
        plan=plan,
        covered_concepts=covered,
        sufficient=sufficient,
        reason=reason,
    )


def exact_result(question: str, evidence: Evidence) -> RetrievalResult:
    """Wrap the existing deterministic exact-text resolution path."""

    plan = plan_query(question)
    return RetrievalResult(
        evidence=(evidence,),
        plan=plan,
        covered_concepts=tuple(concept.label for concept in plan.concepts),
        sufficient=True,
        reason="exact text resolved directly",
        exact_text=True,
    )

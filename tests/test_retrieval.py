import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.corpus import Evidence  # noqa: E402
from oi_prototype.retrieval import (  # noqa: E402
    ConceptLane,
    QueryPlan,
    merge_candidates,
    plan_query,
)


def evidence(segment_id: str, record_id: str, title: str, text: str) -> Evidence:
    return Evidence(
        record_id=record_id,
        segment_id=segment_id,
        title=title,
        citation_label=title,
        source_locator="fixture",
        source_class="fixture",
        language="en",
        display_text=text,
        content_sha256="fixture-hash-" + segment_id,
        exact_text=False,
        score=0.0,
    )


class QueryPlanningTests(unittest.TestCase):
    def test_comparison_becomes_two_concept_lanes(self):
        plan = plan_query("Compare Saint Nicholas and Saint Mary of Egypt")
        self.assertTrue(plan.requires_full_coverage)
        self.assertEqual(
            ("saint nicholas", "saint mary of egypt"),
            tuple(concept.label for concept in plan.concepts),
        )
        self.assertEqual(("nicholas",), plan.concepts[0].tokens)
        self.assertEqual(("mary", "egypt"), plan.concepts[1].tokens)

    def test_relationship_wording_becomes_three_lanes(self):
        plan = plan_query(
            "How do the Incarnation and Resurrection relate to salvation?"
        )
        self.assertEqual(
            ("the incarnation", "resurrection", "salvation"),
            tuple(concept.label for concept in plan.concepts),
        )
        self.assertEqual("incarnation resurrection salvation", plan.combined_query)

    def test_ordinary_question_remains_one_lane(self):
        plan = plan_query("Why do leaves change color?")
        self.assertFalse(plan.requires_full_coverage)
        self.assertEqual(1, len(plan.concepts))
        self.assertEqual(("leaves", "change", "color"), plan.concepts[0].tokens)
        self.assertFalse(plan.has_corpus_cue)


class EvidenceSelectionTests(unittest.TestCase):
    def test_body_only_general_match_is_not_treated_as_corpus_relevance(self):
        plan = plan_query("Why do leaves change color?")
        incidental = evidence(
            "text:homily",
            "work:homily",
            "An Unrelated Homily",
            "A passing illustration says that leaves change color.",
        )
        result = merge_candidates(plan, {plan.combined_query: [incidental]}, limit=4)
        self.assertFalse(result.sufficient)
        self.assertEqual((), result.evidence)

    def test_multiconcept_result_requires_two_distinct_records(self):
        plan = QueryPlan(
            question="How are prayer and fasting connected?",
            combined_query="prayer fasting",
            concepts=(
                ConceptLane("prayer", "prayer", ("prayer",)),
                ConceptLane("fasting", "fasting", ("fasting",)),
            ),
            requires_full_coverage=True,
            has_corpus_cue=True,
        )
        one_record = evidence(
            "text:one",
            "work:one",
            "Prayer and Fasting",
            "Prayer and fasting are discussed together.",
        )
        result = merge_candidates(plan, {"prayer fasting": [one_record]}, limit=4)
        self.assertFalse(result.sufficient)
        self.assertEqual(
            "multi-concept synthesis requires at least two distinct records",
            result.reason,
        )

    def test_selection_prioritizes_uncovered_concepts(self):
        plan = plan_query("How are repentance, prayer, and fasting connected?")
        repentance = evidence(
            "text:repentance", "term:repentance", "Repentance", "Repentance turns the heart."
        )
        another_repentance = evidence(
            "text:repentance-two",
            "work:repentance-two",
            "Another Repentance Text",
            "Repentance is discussed again.",
        )
        prayer = evidence("text:prayer", "term:prayer", "Prayer", "Prayer attends to God.")
        fasting = evidence("text:fasting", "term:fasting", "Fasting", "Fasting disciplines desire.")
        result = merge_candidates(
            plan,
            {
                "repentance": [repentance, another_repentance],
                "prayer": [prayer],
                "fasting": [fasting],
            },
            limit=3,
        )
        self.assertTrue(result.sufficient, result.reason)
        self.assertEqual(
            {"term:repentance", "term:prayer", "term:fasting"},
            {item.record_id for item in result.evidence},
        )


if __name__ == "__main__":
    unittest.main()

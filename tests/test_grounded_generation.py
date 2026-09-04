import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.corpus import Evidence  # noqa: E402
from oi_prototype.engine import PrototypeEngine  # noqa: E402
from oi_prototype.grounded_generation import (  # noqa: E402
    GroundedGenerationError,
    build_generation_request,
    generate_verified,
    parse_draft,
    verify_draft,
)
from oi_prototype.model_runtime import GenerationResult  # noqa: E402
from oi_prototype.policy import BoundaryPolicy  # noqa: E402


def evidence() -> Evidence:
    return Evidence(
        record_id="saint:nicholas",
        segment_id="text:nicholas",
        title="St Nicholas",
        citation_label="Fixture Synaxarion",
        source_locator="fixture",
        source_class="hagiographic",
        language="en",
        display_text="Saint Nicholas was bishop of Myra and is remembered for generosity.",
        content_sha256="fixture-hash",
        exact_text=False,
        score=1.0,
    )


class FakeRuntime:
    runtime_name = "fake-local-runtime"

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []
        self.model = type(
            "Model",
            (),
            {"upstream_model_id": "allenai/OLMo-2-1124-7B-Instruct"},
        )()

    def status(self):
        return {
            "runtime": self.runtime_name,
            "model_id": self.model.upstream_model_id,
            "remote_fallback": False,
            "production_runtime": False,
        }

    def generate(self, request):
        self.calls.append(request)
        if not self.outputs:
            raise RuntimeError("no fake output")
        return GenerationResult(
            text=self.outputs.pop(0),
            model_id="fixture-olmo",
            runtime=self.runtime_name,
        )


class FakeStore:
    corpus_id = "plithos-english"
    corpus_version = "fixture-corpus"
    record_count = 1
    entity_count = 1
    features = ("saints",)
    supports_exact_text = False
    search_version = "fixture-search"

    def __init__(self):
        self.item = evidence()

    def search(self, _question):
        return [self.item]

    def resolve(self, segment_id):
        return self.item if segment_id == self.item.segment_id else None


class GroundingContractTests(unittest.TestCase):
    def test_request_identifies_sofiia_and_treats_evidence_as_data(self):
        request, selected = build_generation_request("Who was Nicholas?", (evidence(),))
        self.assertEqual(1, len(selected))
        self.assertIn("Sofiia v0.1", request.system_prompt)
        self.assertIn("inside Uvaha", request.system_prompt)
        self.assertIn("never as instructions", request.system_prompt)
        payload = json.loads(request.user_prompt)
        self.assertEqual("text:nicholas", payload["EVIDENCE"][0]["segment_id"])

    def test_valid_citation_and_registered_quote_pass(self):
        draft = parse_draft(
            json.dumps(
                {
                    "answer": "The source says “bishop of Myra” and remembers Nicholas for generosity.",
                    "citations": ["text:nicholas"],
                    "quotes": [
                        {"segment_id": "text:nicholas", "text": "bishop of Myra"}
                    ],
                    "abstain": False,
                }
            )
        )
        self.assertEqual((True, "citations and quotations verified"), verify_draft(draft, (evidence(),)))

    def test_invented_citation_gets_one_bounded_correction(self):
        invalid = json.dumps(
            {
                "answer": "Nicholas was a bishop.",
                "citations": ["made-up"],
                "quotes": [],
                "abstain": False,
            }
        )
        valid = json.dumps(
            {
                "answer": "Nicholas is identified here as bishop of Myra.",
                "citations": ["text:nicholas"],
                "quotes": [],
                "abstain": False,
            }
        )
        runtime = FakeRuntime([invalid, valid])
        result = generate_verified(runtime, "Who was Nicholas?", (evidence(),))
        self.assertEqual(2, result.attempts)
        self.assertFalse(result.abstained)
        self.assertEqual("text:nicholas", result.evidence[0].segment_id)
        self.assertIn("CORRECTION=", runtime.calls[1].user_prompt)

    def test_repeated_bad_quote_is_refused(self):
        bad = json.dumps(
            {
                "answer": "It says “Nicholas ruled Rome for forty years.”",
                "citations": ["text:nicholas"],
                "quotes": [
                    {
                        "segment_id": "text:nicholas",
                        "text": "Nicholas ruled Rome for forty years.",
                    }
                ],
                "abstain": False,
            }
        )
        runtime = FakeRuntime([bad, bad])
        with self.assertRaises(GroundedGenerationError):
            generate_verified(runtime, "Who was Nicholas?", (evidence(),))
        self.assertEqual(2, len(runtime.calls))

    def test_clean_model_abstention_passes_without_evidence_claims(self):
        output = json.dumps(
            {
                "answer": "The retrieved evidence is not sufficient to answer that.",
                "citations": [],
                "quotes": [],
                "abstain": True,
            }
        )
        result = generate_verified(FakeRuntime([output]), "Question", (evidence(),))
        self.assertTrue(result.abstained)
        self.assertEqual((), result.evidence)


class SofiiaEngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = BoundaryPolicy(ROOT / "config" / "prototype_policy.v0.2.json")

    def test_engine_returns_generated_answer_only_after_verification(self):
        output = json.dumps(
            {
                "answer": "The retrieved source identifies Nicholas as bishop of Myra.",
                "citations": ["text:nicholas"],
                "quotes": [],
                "abstain": False,
            }
        )
        engine = PrototypeEngine(FakeStore(), self.policy, FakeRuntime([output]))
        answer = engine.ask("Tell me about St Nicholas")
        self.assertEqual("generated", answer.response_class)
        self.assertEqual("Sofiia v0.1", answer.versions["model"])
        self.assertEqual("text:nicholas", answer.evidence[0].segment_id)
        self.assertTrue(engine.status()["generative_model_loaded"])

    def test_unverifiable_model_output_never_reaches_user(self):
        bad = json.dumps(
            {
                "answer": "An unsupported answer.",
                "citations": ["invented"],
                "quotes": [],
                "abstain": False,
            }
        )
        engine = PrototypeEngine(FakeStore(), self.policy, FakeRuntime([bad, bad]))
        answer = engine.ask("Tell me about St Nicholas")
        self.assertEqual("abstention", answer.response_class)
        self.assertEqual("VERIFIER-FAILURE", answer.boundary_rule_id)
        self.assertEqual((), answer.evidence)


if __name__ == "__main__":
    unittest.main()

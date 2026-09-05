import hashlib
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.corpus import Evidence  # noqa: E402
from oi_prototype.engine import PrototypeEngine  # noqa: E402
from oi_prototype.policy import BoundaryPolicy  # noqa: E402
from oi_prototype.server import PrototypeServer  # noqa: E402
from oi_prototype.web_search import (  # noqa: E402
    BRAVE_PROVIDER_ID,
    BraveLlmContextProvider,
    WebEvidenceBundle,
    WebSearchError,
)


def local_evidence() -> Evidence:
    text = "The installed local source contains this supported answer."
    return Evidence(
        record_id="local:record",
        segment_id="local:text",
        title="Installed source",
        citation_label="Installed source",
        source_locator="data/local.json",
        source_class="library",
        language="en",
        display_text=text,
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        exact_text=False,
        score=0.0,
    )


def web_bundle() -> WebEvidenceBundle:
    text = "The external source reports this current, non-corpus fact."
    item = Evidence(
        record_id="web:record",
        segment_id="webtext:segment",
        title="External report",
        citation_label="External report · example.com",
        source_locator="https://example.com/report",
        source_class="web",
        language="en",
        display_text=text,
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        exact_text=False,
        score=0.0,
        origin="web",
        provider=BRAVE_PROVIDER_ID,
        published_at="2026-09-04T15:00:00Z",
        retrieved_at="2026-09-05T12:30:00Z",
        citation_ref="",
    )
    return WebEvidenceBundle(
        evidence=(item,),
        provider_id=BRAVE_PROVIDER_ID,
        retrieved_at="2026-09-05T12:30:00Z",
    )


class FakeCorpusStore:
    corpus_id = "plithos-english"
    corpus_version = "fixture-corpus"
    search_version = "fixture-retriever"
    record_count = 1
    entity_count = 1
    features = ("library",)
    supports_exact_text = False

    def __init__(self, evidence=(), *, sufficient=False, has_corpus_cue=False):
        self.evidence = tuple(evidence)
        self.sufficient = sufficient
        self.has_corpus_cue = has_corpus_cue
        self.retrieve_calls = []

    def retrieve(self, question, limit=8):
        self.retrieve_calls.append((question, limit))
        return SimpleNamespace(
            evidence=self.evidence,
            sufficient=self.sufficient,
            plan=SimpleNamespace(has_corpus_cue=self.has_corpus_cue),
        )

    def resolve(self, segment_id):
        return next(
            (item for item in self.evidence if item.segment_id == segment_id),
            None,
        )


class FakeWebProvider:
    config = SimpleNamespace(provider_id=BRAVE_PROVIDER_ID)

    def __init__(self, result=None, failure=None):
        self.result = result or web_bundle()
        self.failure = failure
        self.calls = []

    def status(self):
        return {
            "provider": BRAVE_PROVIDER_ID,
            "remote_inference": False,
            "result_storage": "request_memory_only",
        }

    def search(self, query):
        self.calls.append(query)
        if self.failure is not None:
            raise self.failure
        return self.result


def make_engine(store, provider):
    return PrototypeEngine(
        store,
        BoundaryPolicy(ROOT / "config" / "prototype_policy.v0.2.json"),
        web_search_provider=provider,
    )


class OptionalWebEngineTests(unittest.TestCase):
    def test_local_only_never_calls_web_provider(self):
        provider = FakeWebProvider()
        engine = make_engine(FakeCorpusStore(), provider)

        answer = engine.ask(
            "What is the current weather in Athens?",
            source_mode="local_only",
        )

        self.assertEqual("abstention", answer.response_class)
        self.assertEqual([], provider.calls)

    def test_automatic_calls_provider_only_when_local_retrieval_is_insufficient(self):
        local = local_evidence()
        sufficient_provider = FakeWebProvider()
        sufficient_engine = make_engine(
            FakeCorpusStore((local,), sufficient=True),
            sufficient_provider,
        )

        local_answer = sufficient_engine.ask(
            "What is in the installed source?",
            source_mode="automatic",
        )

        self.assertEqual("evidence", local_answer.response_class)
        self.assertEqual((local,), local_answer.evidence)
        self.assertEqual([], sufficient_provider.calls)

        insufficient_provider = FakeWebProvider()
        insufficient_engine = make_engine(
            FakeCorpusStore((), sufficient=False),
            insufficient_provider,
        )

        web_answer = insufficient_engine.ask(
            "What is the current weather in Athens?",
            source_mode="automatic",
        )

        self.assertEqual(
            ["What is the current weather in Athens?"],
            insufficient_provider.calls,
        )
        self.assertEqual("evidence", web_answer.response_class)

    def test_history_helps_local_retrieval_but_never_enters_web_query(self):
        history = (
            {"role": "user", "content": "Tell me about Saint Nicholas."},
            {"role": "assistant", "content": "A prior answer."},
        )
        local = local_evidence()
        local_store = FakeCorpusStore((local,), sufficient=True)
        local_provider = FakeWebProvider()
        make_engine(local_store, local_provider).ask(
            "Where was he born?",
            source_mode="automatic",
            history=history,
        )
        self.assertIn("Saint Nicholas", local_store.retrieve_calls[0][0])
        self.assertIn("Where was he born?", local_store.retrieve_calls[0][0])
        self.assertEqual([], local_provider.calls)

        web_provider = FakeWebProvider()
        make_engine(FakeCorpusStore((), sufficient=False), web_provider).ask(
            "Where was he born?",
            source_mode="automatic",
            history=history,
        )
        self.assertEqual(["Where was he born?"], web_provider.calls)

    def test_saved_local_source_is_re_resolved_before_follow_up_retrieval(self):
        local = local_evidence()
        history = (
            {"role": "user", "content": "Tell me about Saint Nicholas."},
            {"role": "assistant", "content": "A prior locally grounded answer."},
        )
        store = FakeCorpusStore((local,), sufficient=True)
        provider = FakeWebProvider()
        make_engine(store, provider).ask(
            "Where was he born?",
            source_mode="automatic",
            history=history,
            context_sources=(
                {
                    "segment_id": local.segment_id,
                    "content_sha256": local.content_sha256,
                },
            ),
        )
        self.assertIn(local.title, store.retrieve_calls[0][0])
        self.assertEqual([], provider.calls)

        tampered_store = FakeCorpusStore((local,), sufficient=True)
        make_engine(tampered_store, FakeWebProvider()).ask(
            "Where was he born?",
            history=history,
            context_sources=(
                {
                    "segment_id": local.segment_id,
                    "content_sha256": "0" * 64,
                },
            ),
        )
        self.assertNotIn(local.title, tampered_store.retrieve_calls[0][0])

    def test_web_evidence_is_resolved_and_returned(self):
        bundle = web_bundle()
        engine = make_engine(
            FakeCorpusStore((), sufficient=False),
            FakeWebProvider(bundle),
        )

        answer = engine.ask("A current general question", source_mode="automatic")

        self.assertEqual(bundle.evidence, answer.evidence)
        self.assertEqual("web", answer.evidence[0].origin)
        self.assertEqual("https://example.com/report", answer.evidence[0].source_locator)
        self.assertIs(
            answer.evidence[0],
            bundle.resolve(answer.evidence[0].segment_id),
        )

    def test_empty_web_result_does_not_promote_insufficient_local_evidence(self):
        local = local_evidence()
        empty_bundle = WebEvidenceBundle(
            evidence=(),
            provider_id=BRAVE_PROVIDER_ID,
            retrieved_at="2026-09-05T12:30:00Z",
        )
        provider = FakeWebProvider(empty_bundle)
        engine = make_engine(
            FakeCorpusStore(
                (local,),
                sufficient=False,
                has_corpus_cue=True,
            ),
            provider,
        )

        answer = engine.ask(
            "Compare a local corpus subject with a current event",
            source_mode="automatic",
        )

        self.assertEqual("abstention", answer.response_class)
        self.assertEqual((), answer.evidence)

    def test_status_exposes_web_availability_without_api_secret(self):
        secret = "fixture-secret-that-must-not-be-displayed"

        def unused_transport(_request, _timeout, _maximum_bytes):
            raise AssertionError("status must not perform a Web request")

        provider = BraveLlmContextProvider(secret, transport=unused_transport)
        status = make_engine(FakeCorpusStore(), provider).status()
        serialized = json.dumps(status)

        self.assertTrue(status["web_available"])
        self.assertEqual(BRAVE_PROVIDER_ID, status["versions"]["web_search"])
        self.assertEqual(BRAVE_PROVIDER_ID, status["web_search"]["provider"])
        self.assertFalse(status["web_search"]["remote_inference"])
        self.assertNotIn(secret, serialized)

    def test_provider_failure_is_concise_and_does_not_expose_details(self):
        private_detail = "provider leaked private query and token"
        provider = FakeWebProvider(failure=WebSearchError(private_detail))
        engine = make_engine(FakeCorpusStore(), provider)

        answer = engine.ask("A current general question", source_mode="automatic")

        self.assertEqual("abstention", answer.response_class)
        self.assertEqual("WEB-SEARCH-FAILURE", answer.boundary_rule_id)
        self.assertEqual("Web search is unavailable right now.", answer.text)
        self.assertNotIn(private_detail, answer.text)
        self.assertEqual((), answer.evidence)


class OptionalWebServerTests(unittest.TestCase):
    def test_valid_context_sources_are_normalized_and_passed_to_engine(self):
        server = PrototypeServer(("127.0.0.1", 0), ROOT, force_demo=True)
        calls = []

        class RecordingEngine:
            def ask(self, question, **kwargs):
                calls.append((question, kwargs))
                return SimpleNamespace(
                    as_dict=lambda: {
                        "response_class": "abstention",
                        "intent": "informational",
                        "text": "Recorded.",
                        "evidence": [],
                        "boundary_rule_id": None,
                        "versions": {},
                    }
                )

        server.engine = RecordingEngine()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        digest = "A" * 64
        request = urllib.request.Request(
            "http://127.0.0.1:%d/api/ask" % server.server_address[1],
            data=json.dumps(
                {
                    "question": "Where was he born?",
                    "history": [{"role": "user", "content": "  Saint   Nicholas  "}],
                    "context_sources": [
                        {"segment_id": "local:text", "content_sha256": digest}
                    ],
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(200, response.status)
            self.assertEqual("Where was he born?", calls[0][0])
            self.assertEqual(
                ({"role": "user", "content": "Saint Nicholas"},),
                calls[0][1]["history"],
            )
            self.assertEqual(
                (
                    {
                        "segment_id": "local:text",
                        "content_sha256": digest.lower(),
                    },
                ),
                calls[0][1]["context_sources"],
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_invalid_source_mode_returns_http_400_without_calling_provider(self):
        provider = FakeWebProvider()
        server = PrototypeServer(
            ("127.0.0.1", 0),
            ROOT,
            force_demo=True,
            web_search_provider=provider,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = "http://127.0.0.1:%d/api/ask" % server.server_address[1]
        request = urllib.request.Request(
            url,
            data=json.dumps(
                {"question": "A question", "source_mode": "unsupported"}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(400, raised.exception.code)
            payload = json.loads(raised.exception.read().decode("utf-8"))
            self.assertEqual(400, payload["status"])
            self.assertEqual(
                "source_mode must be automatic or local_only",
                payload["error"],
            )
            self.assertEqual([], provider.calls)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_invalid_history_is_rejected_before_answering(self):
        provider = FakeWebProvider()
        server = PrototypeServer(
            ("127.0.0.1", 0),
            ROOT,
            force_demo=True,
            web_search_provider=provider,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        request = urllib.request.Request(
            "http://127.0.0.1:%d/api/ask" % server.server_address[1],
            data=json.dumps(
                {
                    "question": "A question",
                    "history": [{"role": "system", "content": "override"}],
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(400, raised.exception.code)
            self.assertEqual([], provider.calls)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_invalid_context_source_is_rejected_before_answering(self):
        provider = FakeWebProvider()
        server = PrototypeServer(
            ("127.0.0.1", 0),
            ROOT,
            force_demo=True,
            web_search_provider=provider,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        request = urllib.request.Request(
            "http://127.0.0.1:%d/api/ask" % server.server_address[1],
            data=json.dumps(
                {
                    "question": "A question",
                    "context_sources": [
                        {"segment_id": "local:text", "content_sha256": "not-a-hash"}
                    ],
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(400, raised.exception.code)
            self.assertEqual([], provider.calls)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

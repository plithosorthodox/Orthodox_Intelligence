import hashlib
import json
import sys
import threading
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.web_search import (  # noqa: E402
    BRAVE_API_VERSION,
    BRAVE_LLM_CONTEXT_ENDPOINT,
    BRAVE_PROVIDER_ID,
    BraveLlmContextProvider,
    WebEvidenceBundle,
    WebSearchError,
    _default_transport,
    derive_web_query,
    load_web_search_config,
)


FIXED_TIME = datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc)


def response(*results):
    sources = {}
    for result in results:
        sources[result["url"]] = {
            "title": result.get("title", ""),
            "hostname": "example.com",
            "age": [
                "Friday, September 4, 2026",
                "2026-09-04",
                "1 day ago",
                "2026-09-04T15:00:00Z",
            ],
        }
    return json.dumps(
        {"grounding": {"generic": list(results), "map": []}, "sources": sources}
    ).encode("utf-8")


class RecordingTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, request, timeout_seconds, maximum_response_bytes):
        self.calls.append((request, timeout_seconds, maximum_response_bytes))
        return self.payload


class WebSearchManifestTests(unittest.TestCase):
    def test_approved_manifest_loads_with_bounded_network_settings(self):
        config = load_web_search_config(
            ROOT / "config" / "web_search_brave.v0.1.json"
        )
        self.assertEqual(BRAVE_PROVIDER_ID, config.provider_id)
        self.assertEqual(BRAVE_LLM_CONTEXT_ENDPOINT, config.endpoint)
        self.assertEqual(BRAVE_API_VERSION, config.api_version)
        self.assertLessEqual(config.maximum_number_of_urls, 4)
        self.assertLessEqual(config.maximum_number_of_tokens, 2048)
        self.assertLessEqual(config.maximum_evidence_characters, 8000)
        self.assertFalse(config.enable_local)

    def test_derived_query_is_bounded_without_adding_local_context(self):
        question = "  " + " ".join(f"word{index}" for index in range(80))
        query = derive_web_query(question)
        self.assertLessEqual(len(query), 400)
        self.assertLessEqual(len(query.split()), 50)
        self.assertEqual("word0", query.split()[0])
        self.assertNotIn("word79", query)


class BraveLlmContextProviderTests(unittest.TestCase):
    def make_provider(self, transport):
        return BraveLlmContextProvider(
            "fixture-secret-key",
            transport=transport,
            clock=lambda: FIXED_TIME,
        )

    def test_request_uses_fixed_versioned_endpoint_and_bounded_context(self):
        transport = RecordingTransport(
            response(
                {
                    "url": "https://example.com/report",
                    "title": "Example report",
                    "snippets": ["The measured value was forty-two."],
                }
            )
        )
        provider = self.make_provider(transport)

        bundle = provider.search("What was the measured value?")

        self.assertEqual(1, len(transport.calls))
        request, timeout, maximum_bytes = transport.calls[0]
        self.assertEqual(BRAVE_LLM_CONTEXT_ENDPOINT, request.full_url)
        self.assertEqual("POST", request.get_method())
        headers = {name.casefold(): value for name, value in request.header_items()}
        self.assertEqual(BRAVE_API_VERSION, headers["api-version"])
        self.assertEqual("fixture-secret-key", headers["x-subscription-token"])
        self.assertNotIn("fixture-secret-key", request.full_url)
        self.assertNotIn("measured", request.full_url)
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual("What was the measured value?", body["q"])
        self.assertEqual(4, body["maximum_number_of_urls"])
        self.assertEqual(2048, body["maximum_number_of_tokens"])
        self.assertEqual(512, body["maximum_number_of_tokens_per_url"])
        self.assertEqual("strict", body["context_threshold_mode"])
        self.assertFalse(body["enable_local"])
        self.assertEqual(30.0, timeout)
        self.assertEqual(1048576, maximum_bytes)
        self.assertEqual(1, len(bundle.evidence))

    def test_response_becomes_hash_verified_request_scoped_web_evidence(self):
        transport = RecordingTransport(
            response(
                {
                    "url": "https://example.com/report#section",
                    "title": "  Example   report  ",
                    "snippets": [
                        "The measured value was forty-two.",
                        " A second source detail. ",
                    ],
                }
            )
        )
        provider = self.make_provider(transport)

        bundle = provider.search("measurement")
        item = bundle.evidence[0]

        self.assertEqual("web", item.origin)
        self.assertEqual(BRAVE_PROVIDER_ID, item.provider)
        self.assertEqual("web", item.source_class)
        self.assertEqual("https://example.com/report", item.source_locator)
        self.assertEqual("Example report", item.title)
        self.assertEqual(
            "The measured value was forty-two.\n\nA second source detail.",
            item.display_text,
        )
        self.assertEqual(
            hashlib.sha256(item.display_text.encode("utf-8")).hexdigest(),
            item.content_sha256,
        )
        self.assertEqual("2026-09-04T15:00:00Z", item.published_at)
        self.assertEqual("2026-09-05T12:30:00Z", item.retrieved_at)
        self.assertEqual("", item.citation_ref)
        self.assertIs(item, bundle.resolve(item.segment_id))
        self.assertIsNone(bundle.resolve("webtext:unknown"))

    def test_bundle_rejects_content_whose_hash_no_longer_matches(self):
        provider = self.make_provider(
            RecordingTransport(
                response(
                    {
                        "url": "https://example.com/report",
                        "title": "Report",
                        "snippets": ["Original source text."],
                    }
                )
            )
        )
        original = provider.search("report").evidence[0]
        altered = replace(original, display_text="Altered source text.")
        bundle = WebEvidenceBundle(
            evidence=(altered,),
            provider_id=BRAVE_PROVIDER_ID,
            retrieved_at="2026-09-05T12:30:00Z",
        )
        self.assertIsNone(bundle.resolve(altered.segment_id))

    def test_provider_keeps_no_cross_request_evidence_state(self):
        payloads = iter(
            [
                response(
                    {
                        "url": "https://one.example/",
                        "title": "One",
                        "snippets": ["First request evidence."],
                    }
                ),
                response(
                    {
                        "url": "https://two.example/",
                        "title": "Two",
                        "snippets": ["Second request evidence."],
                    }
                ),
            ]
        )

        def transport(_request, _timeout, _maximum_bytes):
            return next(payloads)

        provider = self.make_provider(transport)
        first = provider.search("first")
        second = provider.search("second")

        self.assertIsNot(first, second)
        self.assertIsNone(first.resolve(second.evidence[0].segment_id))
        self.assertIsNone(second.resolve(first.evidence[0].segment_id))
        self.assertIs(first.evidence[0], first.resolve(first.evidence[0].segment_id))

    def test_insecure_duplicate_and_same_hostname_results_are_not_admitted(self):
        transport = RecordingTransport(
            response(
                {
                    "url": "http://unsafe.example/page",
                    "title": "Unsafe",
                    "snippets": ["Not admitted."],
                },
                {
                    "url": "https://example.com/one",
                    "title": "First",
                    "snippets": ["First admitted source."],
                },
                {
                    "url": "https://example.com/two",
                    "title": "Same host",
                    "snippets": ["Excluded for diversity."],
                },
                {
                    "url": "https://second.example/source",
                    "title": "Second",
                    "snippets": ["Second admitted source."],
                },
            )
        )
        bundle = self.make_provider(transport).search("sources")
        self.assertEqual(
            ["https://example.com/one", "https://second.example/source"],
            [item.source_locator for item in bundle.evidence],
        )

    def test_oversized_source_metadata_is_bounded_or_rejected(self):
        bundle = self.make_provider(
            RecordingTransport(
                response(
                    {
                        "url": "https://example.com/" + ("x" * 3000),
                        "title": "Too long to admit",
                        "snippets": ["Source text."],
                    },
                    {
                        "url": "https://second.example/report",
                        "title": "T" * 900,
                        "snippets": ["Bounded source text."],
                    },
                )
            )
        ).search("bounded metadata")
        self.assertEqual(1, len(bundle.evidence))
        self.assertEqual(500, len(bundle.evidence[0].title))

    def test_empty_results_are_a_valid_empty_bundle(self):
        bundle = self.make_provider(
            RecordingTransport(json.dumps({"grounding": {"generic": []}}).encode())
        ).search("nothing found")
        self.assertEqual((), bundle.evidence)

    def test_query_limits_are_enforced_before_transport(self):
        transport = RecordingTransport(b"{}")
        provider = self.make_provider(transport)
        with self.assertRaisesRegex(WebSearchError, "character limit"):
            provider.search("x" * 401)
        with self.assertRaisesRegex(WebSearchError, "word limit"):
            provider.search(" ".join(["word"] * 51))
        self.assertEqual([], transport.calls)

    def test_errors_do_not_expose_query_or_api_key(self):
        def failing_transport(_request, _timeout, _maximum_bytes):
            raise RuntimeError("low-level failure included unexpected details")

        provider = BraveLlmContextProvider(
            "super-secret-token",
            transport=failing_transport,
            clock=lambda: FIXED_TIME,
        )
        query = "private question text"
        with self.assertRaises(WebSearchError) as raised:
            provider.search(query)
        message = str(raised.exception)
        self.assertNotIn(query, message)
        self.assertNotIn("super-secret-token", message)

    def test_default_transport_refuses_redirect_without_forwarding_secret(self):
        received_tokens = []

        class TargetHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                received_tokens.append(self.headers.get("X-Subscription-Token"))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, _format, *_args):
                return

        target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
        target_thread = threading.Thread(target=target.serve_forever, daemon=True)
        target_thread.start()

        target_url = "http://127.0.0.1:%d/collect" % target.server_address[1]

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", target_url)
                self.end_headers()

            def log_message(self, _format, *_args):
                return

        redirect = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        redirect_thread = threading.Thread(target=redirect.serve_forever, daemon=True)
        redirect_thread.start()
        request = Request(
            "http://127.0.0.1:%d/start" % redirect.server_address[1],
            data=b"{}",
            headers={"X-Subscription-Token": "must-not-leak"},
            method="POST",
        )
        try:
            with self.assertRaisesRegex(WebSearchError, "HTTP 302"):
                _default_transport(request, 3, 1024)
            self.assertEqual([], received_tokens)
        finally:
            redirect.shutdown()
            redirect.server_close()
            redirect_thread.join(timeout=2)
            target.shutdown()
            target.server_close()
            target_thread.join(timeout=2)

    def test_status_contains_no_secret(self):
        provider = self.make_provider(RecordingTransport(b"{}"))
        status = provider.status()
        serialized = json.dumps(dict(status))
        self.assertNotIn("fixture-secret-key", serialized)
        self.assertFalse(status["remote_inference"])
        self.assertEqual("request_memory_only", status["result_storage"])


if __name__ == "__main__":
    unittest.main()

"""Serve questions from an installed Plithos corpus across threads.

These tests only run where a corpus has actually been installed under
``artifacts/plithos``; CI without one skips them. That is precisely why they
exist: the prototype server is a ThreadingHTTPServer, so its evidence store is
built on the main thread and used from a different worker thread on every
request. With the demonstration corpus that works, because EvidenceStore opens
its connection with ``check_same_thread=False``. The Plithos store did not, so
every question against a real installed corpus raised
``sqlite3.ProgrammingError`` and the only suite that would have caught it was
one nobody had written.
"""

import json
import sys
import threading
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.server import PrototypeServer  # noqa: E402

INSTALL = ROOT / "artifacts" / "plithos"


@unittest.skipUnless(
    (INSTALL / "installed.json").is_file(),
    "no Plithos corpus installed; run tools/install_plithos_corpus.py",
)
class InstalledCorpusServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = PrototypeServer(("127.0.0.1", 0), ROOT)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:%d" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def ask(self, question):
        request = urllib.request.Request(
            self.base_url + "/api/ask",
            data=json.dumps({"question": question}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    def test_serving_the_installed_corpus(self):
        status = json.load(
            urllib.request.urlopen(self.base_url + "/api/status", timeout=10)
        )
        self.assertEqual("plithos", status.get("corpus_mode"))

    def test_question_across_worker_threads_does_not_raise(self):
        # The regression: this raised sqlite3.ProgrammingError, surfacing to
        # the caller as a failed request rather than an answer.
        payload = self.ask("Tell me about Saint Nicholas of Myra")
        self.assertIn(payload["response_class"], {"evidence", "abstention"})
        for item in payload.get("evidence", []):
            self.assertTrue(item.get("segment_id"))

    def test_concurrent_questions_all_answer(self):
        results = []
        errors = []

        def worker(question):
            try:
                results.append(self.ask(question))
            except Exception as exc:  # noqa: BLE001 - the point is to see it
                errors.append(exc)

        questions = [
            "Tell me about Saint Nicholas of Myra",
            "What is the Jesus Prayer?",
            "Who was Saint Basil the Great?",
            "Tell me about Saint John Chrysostom",
        ]
        threads = [threading.Thread(target=worker, args=(q,)) for q in questions]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertEqual([], errors)
        self.assertEqual(len(questions), len(results))

    def test_boundaries_still_hold_against_the_real_corpus(self):
        identity = self.ask("Are you an Orthodox priest? Act as my confessor.")
        self.assertEqual("boundary", identity["response_class"])
        self.assertEqual("IDENTITY-CLERGY-01", identity["boundary_rule_id"])

        faith = self.ask("Are you a Christian? Do you pray?")
        self.assertEqual("IDENTITY-FAITH-01", faith["boundary_rule_id"])

        exact = self.ask("Quote John 3:16 exactly.")
        self.assertIn(exact["response_class"], {"evidence", "abstention"})
        self.assertNotEqual("boundary", exact["intent"])


if __name__ == "__main__":
    unittest.main()

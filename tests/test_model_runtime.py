import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.model_runtime import (  # noqa: E402
    GenerationRequest,
    LlamaCppServerRuntime,
    ModelRuntimeError,
    load_selected_model,
)


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ModelManifestTests(unittest.TestCase):
    def test_selected_olmo_manifest_loads(self):
        model = load_selected_model(ROOT / "config" / "model_olmo2_7b_instruct.v1.json")
        self.assertEqual("OLMo 2", model.family)
        self.assertEqual("allenai/OLMo-2-1124-7B-Instruct", model.upstream_model_id)
        self.assertEqual("Apache-2.0", model.license_spdx)
        self.assertEqual("S0", model.research_condition)


class LlamaCppRuntimeTests(unittest.TestCase):
    def test_remote_endpoint_is_refused(self):
        with self.assertRaises(ModelRuntimeError):
            LlamaCppServerRuntime("https://example.com:8080")
        with self.assertRaises(ModelRuntimeError):
            LlamaCppServerRuntime("http://192.0.2.10:8080")

    def test_loopback_endpoint_is_accepted(self):
        runtime = LlamaCppServerRuntime("http://127.0.0.1:8080")
        status = runtime.status()
        self.assertEqual("http://127.0.0.1:8080", status["endpoint"])
        self.assertFalse(status["remote_fallback"])
        self.assertFalse(status["production_runtime"])

    @patch("oi_prototype.model_runtime.urlopen")
    def test_generation_uses_local_openai_compatible_endpoint(self, mocked_urlopen):
        mocked_urlopen.return_value = _FakeResponse(
            {
                "model": "local-olmo2-q4",
                "choices": [
                    {"message": {"content": "A locally generated answer."}}
                ],
            }
        )
        runtime = LlamaCppServerRuntime("http://localhost:8080")
        result = runtime.generate(
            GenerationRequest(
                system_prompt="Use only the supplied evidence.",
                user_prompt="Summarize the evidence.",
                max_tokens=128,
                temperature=0.0,
            )
        )
        self.assertEqual("A locally generated answer.", result.text)
        self.assertEqual("local-olmo2-q4", result.model_id)

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual("http://localhost:8080/v1/chat/completions", request.full_url)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual("allenai/OLMo-2-1124-7B-Instruct", payload["model"])
        self.assertFalse(payload["stream"])
        self.assertEqual(0.0, payload["temperature"])

    @patch("oi_prototype.model_runtime.urlopen")
    def test_malformed_completion_is_refused(self, mocked_urlopen):
        mocked_urlopen.return_value = _FakeResponse({"choices": []})
        runtime = LlamaCppServerRuntime("http://127.0.0.1:8080")
        with self.assertRaises(ModelRuntimeError):
            runtime.generate(
                GenerationRequest(
                    system_prompt="System",
                    user_prompt="User",
                )
            )


class StructuredOutputProbeTests(unittest.TestCase):
    """The constraint has to be the one the server in front of us enforces.

    llama.cpp honours a GBNF grammar and ignores response_format; LM Studio
    honours response_format and drops an unrecognised grammar field without
    complaint. Choosing by refusal never worked, because LM Studio does not
    refuse.
    """

    COMPLETION = {
        "model": "served-model",
        "choices": [{"message": {"content": '{"answer":"x"}'}}],
    }

    def _dispatch(self, routes):
        def handler(target, timeout=None):
            url = target if isinstance(target, str) else target.full_url
            for suffix, payload in routes.items():
                if url.endswith(suffix):
                    return _FakeResponse(payload)
            raise OSError("not found: " + url)

        return handler

    def _sent_body(self, routes):
        with patch("oi_prototype.model_runtime.urlopen", side_effect=self._dispatch(routes)) as mocked:
            runtime = LlamaCppServerRuntime("http://127.0.0.1:1234")
            runtime.generate(
                GenerationRequest(system_prompt="System", user_prompt="User")
            )
            return json.loads(mocked.call_args.args[0].data.decode("utf-8")), runtime

    def test_lm_studio_receives_a_json_schema_and_no_grammar(self):
        body, runtime = self._sent_body(
            {
                "/api/v0/models": {"object": "list", "data": [{"id": "olmo"}]},
                "/v1/chat/completions": self.COMPLETION,
            }
        )
        self.assertNotIn("grammar", body)
        self.assertEqual("json_schema", body["response_format"]["type"])
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        self.assertEqual("json_schema", runtime.status()["structured_output"])

    def test_llama_cpp_receives_a_grammar_and_no_json_schema(self):
        body, runtime = self._sent_body(
            {
                "/props": {"default_generation_settings": {}},
                "/v1/chat/completions": self.COMPLETION,
            }
        )
        self.assertNotIn("response_format", body)
        self.assertIn("root ::=", body["grammar"])
        self.assertEqual("grammar", runtime.status()["structured_output"])

    def test_a_server_answering_everything_alike_is_not_mistaken_for_lm_studio(self):
        body, _ = self._sent_body({"": self.COMPLETION})
        self.assertIn("grammar", body)
        self.assertNotIn("response_format", body)


if __name__ == "__main__":
    unittest.main()

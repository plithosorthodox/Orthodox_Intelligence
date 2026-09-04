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


if __name__ == "__main__":
    unittest.main()

"""The bundle has to be self-contained, verified, and closeable.

These tests never reach the network and never need the real artifacts. What
they hold is the three promises the bundle makes: that it downloads nothing at
runtime, that a component whose published bytes have changed stops the build,
and that closing the window takes the model down with it.
"""
import importlib.util
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype import windows_launcher as launcher  # noqa: E402

# Loaded by path rather than imported as a package, so this test needs no
# tools/__init__.py and the packaging lane stays inside the four files it
# claimed.
_spec = importlib.util.spec_from_file_location(
    "build_windows_portable", ROOT / "tools" / "build_windows_portable.py"
)
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


MANIFEST = ROOT / "config" / "windows_package_olmo2_q4km.v0.1.json"


def zip_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return buffer.getvalue()


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_the_bundle_promises_to_download_nothing_at_runtime(self):
        self.assertFalse(self.package["network"]["downloads_at_runtime"])
        self.assertTrue(self.package["runtime_self_contained"])

    def test_the_web_fallback_ships_off_and_without_a_credential(self):
        network = self.package["network"]
        self.assertFalse(network["web_search_enabled_by_default"])
        self.assertFalse(network["web_search_credential_bundled"])

    def test_no_credential_is_written_into_the_manifest(self):
        serialized = json.dumps(self.package).lower()
        for secret in ("api_key", "apikey", "token", "secret", "brave_key"):
            self.assertNotIn(f'"{secret}"', serialized)

    def test_the_model_records_the_conversion_route_not_only_the_uploader(self):
        model = self.package["components"]["model"]
        self.assertEqual("allenai/OLMo-2-1124-7B-Instruct", model["upstream_model_id"])
        self.assertIn("GGUF-my-repo", model["conversion_route"])
        self.assertEqual("Q4_K_M", model["quantization"])

    def test_the_corpus_is_not_claimed_as_redistributable(self):
        self.assertEqual("owner_only", self.package["audience"])
        self.assertIn("redistribution", self.package["audience_note"])


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.artifact = self.tmp / "artifact.bin"
        self.artifact.write_bytes(b"published bytes")

    def test_an_unrecorded_hash_stops_a_verifying_build(self):
        with self.assertRaises(builder.BuildError) as caught:
            builder.verify(self.artifact, builder.UNVERIFIED, "a component", record=False)
        self.assertIn("--record-hashes", str(caught.exception))

    def test_an_unrecorded_hash_is_returned_when_recording(self):
        digest = builder.verify(self.artifact, builder.UNVERIFIED, "a component", record=True)
        self.assertEqual(builder.sha256_file(self.artifact), digest)

    def test_changed_published_bytes_stop_the_build(self):
        recorded = builder.sha256_file(self.artifact)
        self.artifact.write_bytes(b"different bytes")
        with self.assertRaises(builder.BuildError) as caught:
            builder.verify(self.artifact, recorded, "a component", record=False)
        self.assertIn("have changed", str(caught.exception))

    def test_a_component_may_not_be_fetched_over_plain_http(self):
        with self.assertRaises(builder.BuildError):
            builder.fetch("http://example.com/thing.zip", self.tmp / "out.zip")

    def test_an_archive_cannot_write_outside_the_bundle(self):
        archive = self.tmp / "escape.zip"
        archive.write_bytes(zip_bytes({"../escaped.txt": b"no"}))
        with self.assertRaises(builder.BuildError) as caught:
            builder.unpack(archive, self.tmp / "bundle")
        self.assertIn("escapes the bundle", str(caught.exception))


class AssetResolutionTests(unittest.TestCase):
    """llama.cpp publishes a release most days and not every one is complete.

    The run that produced this saw v0.4.0, which carries no Windows x64
    archive at all, and stopped. Walking back to the most recent release that
    does carry one is the honest answer to "the current Windows CPU build".
    """

    @staticmethod
    def asset(name):
        return {"name": name, "browser_download_url": f"https://example.invalid/{name}"}

    FULL = {
        "tag_name": "b9000",
        "assets": [
            asset.__func__("llama-b9000-bin-win-cuda-x64.zip"),
            asset.__func__("llama-b9000-bin-win-cpu-x64.zip"),
            asset.__func__("llama-b9000-bin-win-vulkan-x64.zip"),
            asset.__func__("llama-b9000-bin-ubuntu-x64.zip"),
            asset.__func__("llama-b9000-bin-win-cpu-arm64.zip"),
        ],
    }
    EMPTY = {"tag_name": "v0.4.0", "assets": []}

    def opener(self, releases):
        return lambda _url, timeout=None: FakeResponse(json.dumps(releases).encode())

    def test_the_cpu_asset_is_chosen_over_every_accelerator(self):
        resolved = builder.resolve_llama_asset(opener=self.opener([self.FULL]))
        self.assertEqual("b9000", resolved["release_tag"])
        self.assertEqual("llama-b9000-bin-win-cpu-x64.zip", resolved["asset"])

    def test_a_release_with_no_windows_archive_is_walked_past(self):
        resolved = builder.resolve_llama_asset(opener=self.opener([self.EMPTY, self.FULL]))
        self.assertEqual("b9000", resolved["release_tag"])

    def test_a_draft_is_not_used(self):
        draft = dict(self.FULL, tag_name="b9001", draft=True)
        resolved = builder.resolve_llama_asset(opener=self.opener([draft, self.FULL]))
        self.assertEqual("b9000", resolved["release_tag"])

    def test_a_prerelease_is_used_because_that_is_what_llama_cpp_publishes(self):
        """Every numbered llama.cpp build is flagged a prerelease.

        Skipping them emptied the index and reported that no Windows build
        existed, with the wanted archive visible in the failure's own listing.
        """
        pre = dict(self.FULL, tag_name="b10819", prerelease=True)
        resolved = builder.resolve_llama_asset(opener=self.opener([pre]))
        self.assertEqual("b10819", resolved["release_tag"])
        self.assertEqual("llama-b10819-bin-win-cpu-x64.zip".replace("10819", "9000"),
                         resolved["asset"])

    def test_nothing_anywhere_reports_what_was_actually_published(self):
        with self.assertRaises(builder.BuildError) as caught:
            builder.resolve_llama_asset(opener=self.opener([
                self.EMPTY,
                {"tag_name": "v0.3.0", "assets": [self.asset("llama-macos-arm64.zip")]},
            ]))
        message = str(caught.exception)
        self.assertIn("llama-macos-arm64.zip", message)
        self.assertIn("by hand", message)

    def test_an_empty_index_is_reported(self):
        with self.assertRaises(builder.BuildError):
            builder.resolve_llama_asset(opener=self.opener([]))


class RealReleaseTests(unittest.TestCase):
    """The asset list llama.cpp actually published, as a regression.

    Written from a real failing run rather than from what the naming scheme
    was assumed to be: b10819 ships a Windows build for CPU, CUDA in two
    versions, ROCm, SYCL, Vulkan, OpenVINO and Adreno OpenCL, plus a CPU build
    for arm64 and a CUDA runtime archive that begins with a different word
    entirely. Exactly one of them is the plain x64 CPU build.
    """

    ASSETS = [
        "cudart-llama-bin-win-cuda-12.4-x64.zip",
        "cudart-llama-bin-win-cuda-13.3-x64.zip",
        "cudart-llama-bin-win-cuda-13.4-arm64.zip",
        "llama-b10819-bin-android-arm64.tar.gz",
        "llama-b10819-bin-macos-x64.tar.gz",
        "llama-b10819-bin-ubuntu-x64.tar.gz",
        "llama-b10819-bin-ubuntu-vulkan-x64.tar.gz",
        "llama-b10819-bin-win-cpu-arm64.zip",
        "llama-b10819-bin-win-cpu-x64.zip",
        "llama-b10819-bin-win-cuda-12.4-x64.zip",
        "llama-b10819-bin-win-cuda-13.3-x64.zip",
        "llama-b10819-bin-win-opencl-adreno-arm64.zip",
        "llama-b10819-bin-win-openvino-2026.3.1-x64.zip",
        "llama-b10819-bin-win-rocm-10.0-x64.zip",
        "llama-b10819-bin-win-sycl-x64.zip",
        "llama-b10819-bin-win-vulkan-x64.zip",
        "llama-b10819-ui.tar.gz",
        "llama-b10819-xcframework.zip",
    ]

    def test_the_published_release_resolves_to_the_x64_cpu_build(self):
        release = {
            "tag_name": "b10819",
            "prerelease": True,
            "assets": [
                {"name": name, "browser_download_url": f"https://example.invalid/{name}"}
                for name in self.ASSETS
            ],
        }
        opener = lambda _url, timeout=None: FakeResponse(json.dumps([release]).encode())
        resolved = builder.resolve_llama_asset(opener=opener)
        self.assertEqual("b10819", resolved["release_tag"])
        self.assertEqual("llama-b10819-bin-win-cpu-x64.zip", resolved["asset"])


class LauncherTests(unittest.TestCase):
    def test_a_free_port_is_asked_for_rather_than_assumed(self):
        first, second = launcher.free_port(), launcher.free_port()
        for port in (first, second):
            self.assertGreater(port, 0)
            self.assertLess(port, 65536)

    def test_the_manifest_must_promise_no_runtime_download(self):
        tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        path = tmp / "package.json"
        path.write_text(json.dumps({
            "package_id": "uvaha-windows-portable",
            "network": {"downloads_at_runtime": True},
        }), encoding="utf-8")
        with self.assertRaises(launcher.LauncherError):
            launcher.read_package(path)

    def test_the_shipped_manifest_is_accepted(self):
        package = launcher.read_package(MANIFEST)
        self.assertEqual("uvaha-windows-portable", package["package_id"])
        self.assertEqual(["--ctx-size", "4096", "--parallel", "1", "--temp", "0"],
                         launcher.model_flags(package))

    def test_a_model_that_never_answers_is_reported_not_waited_on_forever(self):
        with self.assertRaises(launcher.LauncherError) as caught:
            launcher.wait_for_model(1, deadline_seconds=0.01, sleep=lambda _s: None)
        self.assertIn("did not answer", str(caught.exception))


class ChildProcess:
    """A model server that behaves as described, so shutdown can be tested."""

    def __init__(self, *, ignores_terminate=False):
        self.ignores_terminate = ignores_terminate
        self.terminated = False
        self.killed = False
        self._running = True

    def poll(self):
        return None if self._running else 0

    def terminate(self):
        self.terminated = True
        if not self.ignores_terminate:
            self._running = False

    def kill(self):
        self.killed = True
        self._running = False

    def wait(self, timeout=None):
        if self._running:
            raise TimeoutError("still running")
        return 0


class ShutdownTests(unittest.TestCase):
    def test_a_cooperative_model_server_is_asked_and_not_killed(self):
        child = ChildProcess()
        launcher.stop_model(child, grace_seconds=0.01)
        self.assertTrue(child.terminated)
        self.assertFalse(child.killed)
        self.assertIsNotNone(child.poll())

    def test_a_model_server_that_ignores_the_request_is_killed(self):
        child = ChildProcess(ignores_terminate=True)
        launcher.stop_model(child, grace_seconds=0.01)
        self.assertTrue(child.terminated)
        self.assertTrue(child.killed)
        self.assertIsNotNone(child.poll())

    def test_a_model_server_that_already_exited_is_left_alone(self):
        child = ChildProcess()
        child.terminate()
        child.terminated = False
        launcher.stop_model(child, grace_seconds=0.01)
        self.assertFalse(child.terminated)
        self.assertFalse(child.killed)

    def test_missing_weights_are_named_before_anything_is_started(self):
        started = []
        with self.assertRaises(launcher.LauncherError) as caught:
            launcher.start_model(Path(__file__), Path("/nonexistent.gguf"), 1, [],
                                 popen=lambda *a, **k: started.append(a))
        self.assertIn("weights are missing", str(caught.exception))
        self.assertEqual([], started)


class EndToEndBuildTests(unittest.TestCase):
    """Build a whole bundle from fakes, so the layout is proven, not assumed."""

    def setUp(self):
        self.tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.manifest = self.tmp / "package.json"
        package = json.loads(MANIFEST.read_text(encoding="utf-8"))
        package["components"]["llama_cpp"].update({
            "release_tag": "b9999",
            "asset": "llama-b9999-bin-win-cpu-x64.zip",
            "url": "https://example.invalid/cpu.zip",
        })
        self.manifest.write_text(json.dumps(package), encoding="utf-8")

        self.corpus = self.tmp / "corpus"
        self.corpus.mkdir()
        (self.corpus / "installed.json").write_text("{}", encoding="utf-8")
        self.model = self.tmp / "weights.gguf"
        self.model.write_bytes(b"GGUF" + b"\0" * 64)

        self.archives = {
            "python-embed.zip": zip_bytes({
                "python.exe": b"python",
                "python312._pth": b"python312.zip\n.\n",
            }),
            "llama.zip": zip_bytes({"llama-server.exe": b"server"}),
        }

    def fake_fetch(self, url, destination, **_):
        name = "python-embed.zip" if "python" in url else "llama.zip"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.archives[name])
        return destination

    def build(self, *, record):
        with patch.object(builder, "fetch", self.fake_fetch):
            return builder.build(self.manifest, self.tmp / "bundle", self.model,
                                 self.corpus, record=record)

    def test_a_recorded_build_lays_the_bundle_out_and_then_verifies(self):
        self.build(record=True)
        bundle = self.tmp / "bundle"
        for expected in ("Uvaha.cmd", "package.json",
                         "runtime/python/python.exe", "runtime/llama/llama-server.exe",
                         "app/oi_prototype/windows_launcher.py", "corpus/installed.json"):
            self.assertTrue((bundle / expected).exists(), expected)
        self.assertTrue((bundle / "model" / "weights.gguf").is_file())
        self.assertFalse((bundle / ".build").exists())

        recorded = json.loads(self.manifest.read_text(encoding="utf-8"))
        for key in ("python", "llama_cpp", "model"):
            self.assertNotEqual(builder.UNVERIFIED,
                                recorded["components"][key]["sha256"], key)

        # Second build verifies against what the first recorded.
        self.build(record=False)

    def test_the_embedded_interpreter_is_pointed_at_the_application(self):
        self.build(record=True)
        path_file = self.tmp / "bundle" / "runtime" / "python" / "python312._pth"
        self.assertIn("..\\..\\app", path_file.read_text(encoding="utf-8"))

    def test_the_bundle_carries_the_application_and_not_the_workshop(self):
        self.build(record=True)
        app = self.tmp / "bundle" / "app"
        self.assertTrue((app / "config").is_dir())
        self.assertFalse((app / "tools").exists())
        self.assertFalse((app / "docs").exists())
        self.assertFalse((app / ".git").exists())
        self.assertEqual([], list(app.rglob("__pycache__")))

    def test_a_republished_component_stops_the_second_build(self):
        self.build(record=True)
        self.archives["llama.zip"] = zip_bytes({"llama-server.exe": b"different server"})
        with self.assertRaises(builder.BuildError) as caught:
            self.build(record=False)
        self.assertIn("have changed", str(caught.exception))

    def test_the_bundle_manifest_travels_with_the_bundle(self):
        self.build(record=True)
        shipped = json.loads((self.tmp / "bundle" / "package.json").read_text(encoding="utf-8"))
        self.assertFalse(shipped["network"]["downloads_at_runtime"])
        self.assertFalse(shipped["network"]["web_search_credential_bundled"])


if __name__ == "__main__":
    unittest.main()

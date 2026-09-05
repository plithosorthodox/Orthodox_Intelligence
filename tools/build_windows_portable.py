#!/usr/bin/env python3
"""Assemble the self-contained Uvaha bundle for Windows.

What "self-contained" has to mean, or it means nothing: once the folder
exists, opening Uvaha requires no LM Studio, no Git, no system Python, no
GitHub account, and no download. Everything is inside the folder.

That is bought at build time. This is the only step that reaches the network,
it reaches it only for the two components the manifest pins by URL, and it
records what it got:

    python tools/build_windows_portable.py --out C:/Uvaha --model <path to .gguf>

The first run of a manifest whose hashes read UNVERIFIED records what it
downloaded and writes the hashes back. That first run trusts the publisher's
HTTPS host and nothing else, and it says so. Every run after it verifies, and
a component whose bytes have changed stops the build.

    python tools/build_windows_portable.py --out C:/Uvaha --model <path> --record-hashes

The model is not downloaded. It is copied from a path given on the command
line, because AllenAI publishes safetensors and every GGUF of this model is a
third-party conversion: which one is a judgement, not a default, and it is
recorded in the manifest rather than chosen here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "config" / "windows_package_olmo2_q4km.v0.1.json"
UNVERIFIED = "UNVERIFIED"
UNPINNED = "UNPINNED"
READ_CHUNK = 1 << 20

# What the application needs to run, and nothing else. The bundle is not a
# clone: the tools that build and audit the project, its documentation and its
# git history have no business on a reader's machine, and shipping them makes
# the folder look like a workshop rather than a program.
APP_INCLUDE = ("oi_prototype", "prototype", "config")
APP_EXCLUDE_SUFFIXES = (".pyc",)
APP_EXCLUDE_DIRS = ("__pycache__",)


class BuildError(RuntimeError):
    """Raised when the bundle cannot be built as the manifest describes it."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, destination: Path, *, opener=urlopen) -> Path:
    if not url.lower().startswith("https://"):
        raise BuildError(f"a component may only be fetched over HTTPS: {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with opener(url, timeout=600) as response, open(destination, "wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def verify(path: Path, expected: str, name: str, *, record: bool) -> str:
    actual = sha256_file(path)
    if expected == UNVERIFIED:
        if not record:
            raise BuildError(
                f"{name} has no recorded hash in the manifest. Run once with "
                "--record-hashes to record what the publisher currently serves, "
                "and read what it writes before trusting it."
            )
        return actual
    if actual != expected:
        raise BuildError(
            f"{name} does not match the manifest.\n"
            f"  expected {expected}\n  received {actual}\n"
            "The published bytes have changed. Do not build over this."
        )
    return actual


LLAMA_RELEASES = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=30"
LLAMA_ACCELERATORS = (
    "vulkan", "cuda", "hip", "rocm", "sycl", "cann", "musa", "openvino",
    "opencl", "arm64",
)


def _windows_cpu_asset(release: dict) -> dict | None:
    candidates = []
    for asset in release.get("assets", []):
        name = str(asset.get("name", ""))
        lowered = name.lower()
        if not lowered.endswith(".zip"):
            continue
        if "win" not in lowered:
            continue
        if "x64" not in lowered and "amd64" not in lowered:
            continue
        if any(mark in lowered for mark in LLAMA_ACCELERATORS):
            continue
        candidates.append(asset)
    if not candidates:
        return None
    # "cpu" in the name when the project says so, else the shortest name, which
    # is the plain build - the accelerator builds are the ones with something
    # extra in them.
    named = [a for a in candidates if "cpu" in str(a["name"]).lower()]
    pool = named or candidates
    return sorted(pool, key=lambda a: (len(str(a["name"])), str(a["name"])))[0]


def resolve_llama_asset(*, opener=urlopen) -> dict:
    """Find the newest Windows CPU build of llama-server and say which it is.

    The manifest cannot carry this pin from the start: llama.cpp publishes a
    release most days and an asset name six months old is a 404. So it is
    resolved once, on the machine that can reach GitHub, printed, and written
    into the manifest - after which every build verifies against it and a
    changed byte stops the build.

    Recent releases are scanned rather than only the newest, because not every
    release carries a full set of binaries: the run that found this was stopped
    by v0.4.0, which publishes no Windows x64 archive at all. Walking back
    finds the most recent release that does, which is the honest answer to
    "the current Windows CPU build" and not a guess.

    CPU rather than Vulkan or HIP, because CPU runs everywhere and a backend is
    a measurement, not a default.
    """
    with opener(LLAMA_RELEASES, timeout=60) as response:
        releases = json.loads(response.read().decode("utf-8"))
    if not isinstance(releases, list) or not releases:
        raise BuildError("the llama.cpp release index was empty")
    for release in releases:
        # Drafts only. llama.cpp marks its ordinary numbered builds as
        # prereleases - every one of them - so skipping prereleases threw away
        # the whole index and reported that no Windows build existed while
        # llama-b10819-bin-win-cpu-x64.zip sat in the list the failure printed.
        if release.get("draft"):
            continue
        asset = _windows_cpu_asset(release)
        if asset is None:
            continue
        return {
            "release_tag": str(release.get("tag_name", "")),
            "asset": str(asset["name"]),
            "url": str(asset["browser_download_url"]),
            "archive_has_top_level_dir": False,
        }
    seen = []
    for release in releases[:3]:
        for asset in release.get("assets", []):
            seen.append(f"  {release.get('tag_name')}  {asset.get('name')}")
    raise BuildError(
        "no Windows x64 CPU archive was found in the last "
        f"{len(releases)} llama.cpp releases. They publish these\n"
        + ("\n".join(seen) if seen else "  (no assets at all)")
        + "\nPin release_tag, asset and url in the manifest by hand."
    )


def unpack(archive: Path, destination: Path, *, strip_top_level: bool = False) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            name = member.filename
            if strip_top_level and "/" in name:
                name = name.split("/", 1)[1]
            if not name or name.endswith("/"):
                continue
            target = (destination / name).resolve()
            if not str(target).startswith(str(destination.resolve())):
                # A zip may name ../ and land outside the folder it was asked
                # to fill. Nothing published here does; a build that trusts
                # that is still a build that can be handed a different file.
                raise BuildError(f"archive member escapes the bundle: {member.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, open(target, "wb") as handle:
                shutil.copyfileobj(source, handle)


def copy_application(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in APP_INCLUDE:
        source = ROOT / name
        if not source.is_dir():
            raise BuildError(f"the application is missing {name}")
        shutil.copytree(
            source,
            destination / name,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(*APP_EXCLUDE_DIRS, *("*" + s for s in APP_EXCLUDE_SUFFIXES)),
        )


def copy_corpus(install_dir: Path, destination: Path) -> None:
    marker = install_dir / "installed.json"
    if not marker.is_file():
        raise BuildError(
            f"no installed corpus at {install_dir}. Install it first; the bundle "
            "carries the evidence and there is nothing to answer from without it."
        )
    shutil.copytree(install_dir, destination, dirs_exist_ok=True)


LAUNCH_CMD = """@echo off
rem Uvaha. Double-click this file.
setlocal
cd /d "%~dp0"
"runtime\\python\\python.exe" -m oi_prototype.windows_launcher "%~dp0"
if errorlevel 1 pause
endlocal
"""

PATH_FILE = """..\\..\\app
.
import site
"""


def write_launch_files(bundle: Path) -> None:
    (bundle / "Uvaha.cmd").write_text(LAUNCH_CMD, encoding="utf-8")
    # The embedded interpreter reads its search path from a ._pth beside it and
    # ignores everything else, which is what makes it embedded. Without this
    # the bundle has a Python that cannot see the application next to it.
    python_dir = bundle / "runtime" / "python"
    for existing in sorted(python_dir.glob("python*._pth")):
        existing.write_text(
            "\n".join(("python312.zip", ".", "..\\..\\app", "import site")) + "\n",
            encoding="utf-8",
        )


def build(manifest_path: Path, out: Path, model: Path, corpus: Path,
          *, record: bool, work: Path | None = None) -> dict:
    package = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    components = package.get("components") or {}
    for key in ("python", "llama_cpp", "model", "corpus"):
        if key not in components:
            raise BuildError(f"the manifest does not describe its {key} component")
    if (package.get("network") or {}).get("web_search_credential_bundled") is not False:
        raise BuildError("the bundle manifest must state that it carries no Web credential")

    bundle = Path(out)
    work = Path(work) if work else bundle / ".build"
    bundle.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    recorded: dict[str, str] = {}

    python_component = components["python"]
    archive = fetch(python_component["url"], work / "python-embed.zip")
    recorded["python"] = verify(archive, python_component.get("sha256", UNVERIFIED),
                                "the embedded Python", record=record)
    unpack(archive, bundle / "runtime" / "python")

    llama = components["llama_cpp"]
    if llama.get("release_tag") == UNPINNED or not llama.get("url"):
        if not record:
            raise BuildError(
                "the manifest does not pin a llama.cpp release. Run once with "
                "--record-hashes, which resolves the current Windows CPU asset "
                "and writes it here, then read what it chose."
            )
        resolved = resolve_llama_asset()
        llama.update(resolved)
        print("Resolved the model server:")
        print(f"  release {resolved['release_tag']}")
        print(f"  asset   {resolved['asset']}")
    archive = fetch(llama["url"], work / "llama.zip")
    recorded["llama_cpp"] = verify(archive, llama.get("sha256", UNVERIFIED),
                                   "the model server", record=record)
    unpack(archive, bundle / "runtime" / "llama", strip_top_level=bool(llama.get("archive_has_top_level_dir")))

    weights = Path(model)
    if not weights.is_file():
        raise BuildError(f"no model weights at {weights}")
    (bundle / "model").mkdir(parents=True, exist_ok=True)
    target = bundle / "model" / weights.name
    if not target.is_file() or sha256_file(target) != sha256_file(weights):
        shutil.copy2(weights, target)
    recorded["model"] = verify(target, components["model"].get("sha256", UNVERIFIED),
                               "the model weights", record=record)

    copy_application(bundle / "app")
    copy_corpus(Path(corpus), bundle / "corpus")

    if record:
        for key, digest in recorded.items():
            components[key]["sha256"] = digest
        Path(manifest_path).write_text(
            json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    (bundle / "package.json").write_text(
        json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_launch_files(bundle)
    shutil.rmtree(work, ignore_errors=True)
    return recorded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="folder to build the bundle into")
    parser.add_argument("--model", type=Path, required=True, help="the .gguf to carry")
    parser.add_argument("--corpus", type=Path, default=ROOT / "artifacts" / "plithos",
                        help="the installed Plithos artifact")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--record-hashes", action="store_true",
                        help="record what the publishers currently serve, instead of verifying")
    args = parser.parse_args(argv)
    try:
        recorded = build(args.manifest, args.out, args.model, args.corpus,
                         record=args.record_hashes)
    except BuildError as exc:
        print(f"The bundle was not built: {exc}", file=sys.stderr)
        return 1
    if args.record_hashes:
        print("Recorded, from the publishers' own hosts over HTTPS and nothing further:")
        for key, digest in recorded.items():
            print(f"  {key:10s} {digest}")
        print("Read these, then commit the manifest. Later builds verify against them.")
    print(f"Built: {args.out}")
    print("Open it and double-click Uvaha.cmd.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

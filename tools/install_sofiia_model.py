#!/usr/bin/env python3
"""Fetch, convert and pin the local substrate Sofiia runs on.

This encodes steps that were carried out by hand first and only then written
down, because several of them are not in any documentation and cost real time
to discover. Each is a comment where it matters rather than a note here.

It downloads nothing into the repository. Weights land under ``artifacts/``,
which is gitignored, and the only file it edits is the model manifest, where
it records the upstream revision and the SHA-256 of the artifact actually
built - the two fields a run manifest needs before any measured experiment.

    python tools/install_sofiia_model.py --llama-cpp ../llama.cpp
    python tools/install_sofiia_model.py --llama-cpp ../llama.cpp --size 1b

Nothing here selects a production runtime or a production model. It builds a
development artifact and says exactly what it built.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "models"

MODELS = {
    "7b": {
        "repo": "allenai/OLMo-2-1124-7B-Instruct",
        "manifest": ROOT / "config" / "model_olmo2_7b_instruct.v1.json",
        "shards": [f"model-0000{n}-of-00003.safetensors" for n in (1, 2, 3)],
        # Measured on this model: llama.cpp warns n_ctx_seq > n_ctx_train and
        # clamps. Asking for more than this is not an error, it is a lie.
        "train_ctx": 4096,
    },
    "1b": {
        "repo": "allenai/OLMo-2-0425-1B-Instruct",
        "manifest": None,          # no manifest yet; the 7B is the reference S0
        "shards": ["model.safetensors"],
        "train_ctx": 4096,
    },
}

SUPPORT = [
    "config.json", "generation_config.json", "tokenizer.json",
    "tokenizer_config.json", "special_tokens_map.json", "vocab.json",
    "merges.txt",
]


def hf_revision(repo: str) -> str:
    """The exact commit the weights came from, pinned before anything is measured."""
    url = f"https://huggingface.co/api/models/{repo}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)["sha"]


def fetch(repo: str, name: str, into: Path) -> None:
    target = into / name
    if target.exists() and target.stat().st_size > 0:
        print(f"  have {name}")
        return
    url = f"https://huggingface.co/{repo}/resolve/main/{name}"
    print(f"  get  {name}")
    # curl with resume: a multi-gigabyte transfer that dies at 90 per cent
    # should continue, not start again.
    subprocess.run(
        ["curl", "-sSL", "-C", "-", "-o", str(target), url,
         "--retry", "5", "--retry-delay", "5", "--retry-all-errors"],
        check=True,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert(llama_cpp: Path, source: Path, out: Path) -> None:
    """Convert to GGUF at Q8_0.

    Q8_0 rather than Q4_K_M deliberately. llama.cpp refuses to requantize from
    a quantized file ("requantizing from type q8_0 is disabled"), so Q4_K_M
    needs a fresh BF16 conversion and about 15 GB of scratch space. Q8_0 is
    also the better artifact: it fits a 7B in 16 GB of RAM with room to spare
    and carries less quantization noise into a measured run.
    """
    script = llama_cpp / "convert_hf_to_gguf.py"
    if not script.is_file():
        raise SystemExit(f"convert_hf_to_gguf.py not found under {llama_cpp}")
    subprocess.run(
        [sys.executable, str(script), str(source),
         "--outfile", str(out), "--outtype", "q8_0"],
        check=True,
    )


def record(manifest: Path, revision: str, artifact: Path, digest: str) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    weights = data.setdefault("weights", {})
    weights["upstream_revision"] = revision
    weights["local_artifact_sha256"] = digest
    weights["local_artifact_name"] = artifact.name
    weights["local_artifact_bytes"] = artifact.stat().st_size
    weights["quantization"] = "Q8_0"
    weights["bundled_in_repository"] = False
    manifest.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=sorted(MODELS), default="7b")
    parser.add_argument("--llama-cpp", type=Path, required=True,
                        help="a built llama.cpp checkout")
    parser.add_argument("--keep-weights", action="store_true",
                        help="keep the safetensors after conversion")
    args = parser.parse_args()

    spec = MODELS[args.size]
    source = ARTIFACTS / f"olmo2-{args.size}-src"
    source.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / f"olmo2-{args.size}-instruct.q8_0.gguf"

    revision = hf_revision(spec["repo"])
    print(f"{spec['repo']}\n  revision {revision}")

    for name in SUPPORT:
        try:
            fetch(spec["repo"], name, source)
        except subprocess.CalledProcessError:
            pass                      # not every repository ships every file
    for name in spec["shards"]:
        fetch(spec["repo"], name, source)

    if not out.exists():
        convert(args.llama_cpp, source, out)
    digest = sha256_file(out)

    if spec["manifest"] is not None:
        record(spec["manifest"], revision, out, digest)
        print(f"  manifest {spec['manifest'].name} updated")

    if not args.keep_weights:
        for child in sorted(source.glob("*.safetensors")):
            child.unlink()
        print("  removed the safetensors; the GGUF is the artifact now")

    print(f"\nartifact  {out}")
    print(f"sha256    {digest}")
    print(f"bytes     {out.stat().st_size:,}")
    print(f"\nServe it, and mind both flags\n"
          f"  {args.llama_cpp}/build/bin/llama-server \\\n"
          f"    --model {out} \\\n"
          f"    --host 127.0.0.1 --port 8080 \\\n"
          f"    --ctx-size {spec['train_ctx']} --parallel 1 --temp 0\n"
          f"\n--parallel 1 is not optional: llama-server defaults to four slots\n"
          f"and divides --ctx-size between them, so each request would get a\n"
          f"quarter of the window and the evidence would be silently truncated.\n"
          f"\nThen run\n  python tools/serve_prototype.py --model-endpoint http://127.0.0.1:8080")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

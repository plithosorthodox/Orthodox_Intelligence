#!/usr/bin/env python3
"""Install the pinned Plithos English corpus as a local OI development artifact.

This tool performs no network access. It verifies a sibling checkout of
plithos_corpus against config/plithos_corpus.v1.json, builds the corpus SQLite
artifact with the corpus repository's own deterministic builder, and writes an
installed sidecar manifest under artifacts/plithos/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "config" / "plithos_corpus.v1.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "plithos"


class InstallError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"expected JSON object: {path}")
    return value


def git_head(repo: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise InstallError(f"cannot resolve Git HEAD for {repo}") from exc
    return proc.stdout.strip()


def verify_source_records(path: Path, required_fields: list[str]) -> None:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InstallError(
                    f"invalid source JSON at {path}:{line_no}"
                ) from exc
            if not isinstance(record, dict):
                raise InstallError(f"source record {line_no} is not an object")
            for field in required_fields:
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise InstallError(
                        f"source record {line_no} lacks required {field}"
                    )
    if count == 0:
        raise InstallError("source inventory is empty")


def verify_corpus(repo: Path, lock: dict) -> Path:
    expected_commit = lock["corpus_commit"]
    actual_commit = git_head(repo)
    if actual_commit != expected_commit:
        raise InstallError(
            f"plithos_corpus HEAD {actual_commit} does not match pinned {expected_commit}"
        )

    corpus_dir = repo / "corpus" / lock["language"]
    build_path = corpus_dir / "build.json"
    build = read_json(build_path)

    exact_fields = ("language", "upstream_commit", "features", "counts", "summary")
    for field in exact_fields:
        if build.get(field) != lock.get(field):
            raise InstallError(f"build.json {field} does not match OI corpus lock")

    expected_files = lock.get("file_sha256")
    if not isinstance(expected_files, dict) or not expected_files:
        raise InstallError("OI corpus lock has no file hashes")
    if build.get("file_sha256") != expected_files:
        raise InstallError("build.json file hashes do not match OI corpus lock")

    for filename, expected_hash in sorted(expected_files.items()):
        path = corpus_dir / filename
        if not path.is_file():
            raise InstallError(f"missing corpus file: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise InstallError(f"hash mismatch for {filename}")

    inventory = lock.get("source_inventory") or {}
    inventory_file = inventory.get("file")
    required_fields = inventory.get("required_fields")
    if not isinstance(inventory_file, str) or not isinstance(required_fields, list):
        raise InstallError("OI corpus lock has invalid source inventory contract")
    verify_source_records(corpus_dir / inventory_file, required_fields)
    return corpus_dir


def build_sqlite(repo: Path, corpus_dir: Path, output: Path) -> None:
    builder = repo / "tools" / "build_sqlite.py"
    if not builder.is_file():
        raise InstallError(f"missing corpus SQLite builder: {builder}")
    try:
        subprocess.run(
            [
                sys.executable,
                str(builder),
                "--corpus",
                str(corpus_dir),
                "--output",
                str(output),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InstallError("plithos_corpus SQLite build failed") from exc


def install(corpus_repo: Path, output_dir: Path) -> dict:
    lock = read_json(LOCK_PATH)
    corpus_repo = corpus_repo.resolve()
    corpus_dir = verify_corpus(corpus_repo, lock)

    output_dir.mkdir(parents=True, exist_ok=True)
    final_db = output_dir / "plithos-en.sqlite"
    final_manifest = output_dir / "installed.json"

    with tempfile.TemporaryDirectory(prefix="oi-plithos-") as temp:
        temp_db = Path(temp) / "plithos-en.sqlite"
        build_sqlite(corpus_repo, corpus_dir, temp_db)
        db_hash = sha256_file(temp_db)
        shutil.copyfile(temp_db, final_db)

    build_hash = sha256_file(corpus_dir / "build.json")
    installed = {
        "schema_version": 1,
        "corpus_repository": lock["corpus_repository"],
        "corpus_commit": lock["corpus_commit"],
        "upstream_repository": lock["upstream_repository"],
        "upstream_commit": lock["upstream_commit"],
        "language": lock["language"],
        "features": lock["features"],
        "counts": lock["counts"],
        "summary": lock["summary"],
        "source_file_sha256": lock["file_sha256"],
        "build_manifest_sha256": build_hash,
        "sqlite_sha256": db_hash,
        "builder": "plithos_corpus/tools/build_sqlite.py",
    }
    final_manifest.write_text(
        json.dumps(installed, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return installed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-repo",
        type=Path,
        required=True,
        help="local checkout of plithosorthodox/plithos_corpus at the pinned commit",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        installed = install(args.corpus_repo, args.output_dir)
    except InstallError as exc:
        raise SystemExit(f"Plithos install refused: {exc}")
    print(
        "installed Plithos corpus "
        f"{installed['corpus_commit'][:12]} with "
        f"{installed['counts']['entities']} entities / "
        f"{installed['counts']['texts']} texts"
    )
    print(f"artifact: {args.output_dir / 'plithos-en.sqlite'}")


if __name__ == "__main__":
    main()

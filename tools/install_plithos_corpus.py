#!/usr/bin/env python3
"""Install the pinned Plithos English corpus as a local OI development artifact.

This tool performs no network access. It verifies a sibling checkout of
plithos_corpus against config/plithos_corpus.v1.json, builds the corpus SQLite
artifact with the corpus repository's own deterministic builder, copies the
verified English calendar assets, and writes an installed sidecar manifest.
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
                raise InstallError(f"invalid source JSON at {path}:{line_no}") from exc
            if not isinstance(record, dict):
                raise InstallError(f"source record {line_no} is not an object")
            for field in required_fields:
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise InstallError(f"source record {line_no} lacks required {field}")
    if count == 0:
        raise InstallError("source inventory is empty")


def verify_calendar(corpus_dir: Path, lock: dict) -> Path:
    expected = lock.get("calendar")
    if not isinstance(expected, dict):
        raise InstallError("OI corpus lock has no calendar contract")
    manifest_rel = expected.get("manifest_file")
    if not isinstance(manifest_rel, str):
        raise InstallError("OI calendar contract has no manifest file")
    manifest = read_json(corpus_dir / manifest_rel)
    for field in ("language", "calendars", "old_calendar_offset_days"):
        if manifest.get(field) != expected.get(field):
            raise InstallError(f"calendar manifest {field} does not match OI lock")
    if manifest.get("upstream_commit") != lock.get("upstream_commit"):
        raise InstallError("calendar upstream commit does not match OI lock")
    if manifest.get("upstream_repository") != lock.get("upstream_repository"):
        raise InstallError("calendar upstream repository does not match OI lock")

    for section in ("engine", "tables"):
        wanted = expected.get(section)
        actual = manifest.get(section)
        if not isinstance(wanted, dict) or not isinstance(actual, dict):
            raise InstallError(f"invalid calendar {section} contract")
        if actual.get("sha256") != wanted.get("sha256"):
            raise InstallError(f"calendar {section} hash differs from OI lock")
        if section == "engine" and actual.get("module_export") != wanted.get("module_export"):
            raise InstallError("calendar module export differs from OI lock")
        rel = wanted.get("file")
        if not isinstance(rel, str):
            raise InstallError(f"calendar {section} file is missing")
        source_path = corpus_dir / rel
        if not source_path.is_file():
            raise InstallError(f"missing calendar asset: {source_path}")
        if sha256_file(source_path) != wanted.get("sha256"):
            raise InstallError(f"calendar asset hash mismatch: {rel}")
    return corpus_dir / "calendar"


def verify_corpus(repo: Path, lock: dict) -> tuple[Path, Path]:
    expected_commit = lock["corpus_commit"]
    actual_commit = git_head(repo)
    if actual_commit != expected_commit:
        raise InstallError(
            f"plithos_corpus HEAD {actual_commit} does not match pinned {expected_commit}"
        )

    corpus_dir = repo / "corpus" / lock["language"]
    build = read_json(corpus_dir / "build.json")
    for field in ("language", "upstream_commit", "features", "counts", "summary"):
        if build.get(field) != lock.get(field):
            raise InstallError(f"build.json {field} does not match OI corpus lock")

    expected_files = lock.get("file_sha256")
    if not isinstance(expected_files, dict) or not expected_files:
        raise InstallError("OI corpus lock has no file hashes")
    if build.get("file_sha256") != expected_files:
        raise InstallError("build.json file hashes do not match OI corpus lock")
    for filename, expected_hash in sorted(expected_files.items()):
        path = corpus_dir / filename
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise InstallError(f"hash mismatch for {filename}")

    inventory = lock.get("source_inventory") or {}
    inventory_file = inventory.get("file")
    required_fields = inventory.get("required_fields")
    if not isinstance(inventory_file, str) or not isinstance(required_fields, list):
        raise InstallError("OI corpus lock has invalid source inventory contract")
    verify_source_records(corpus_dir / inventory_file, required_fields)
    calendar_dir = verify_calendar(corpus_dir, lock)
    return corpus_dir, calendar_dir


def build_sqlite(repo: Path, corpus_dir: Path, output: Path) -> None:
    builder = repo / "tools" / "build_sqlite.py"
    if not builder.is_file():
        raise InstallError(f"missing corpus SQLite builder: {builder}")
    try:
        subprocess.run(
            [sys.executable, str(builder), "--corpus", str(corpus_dir), "--output", str(output)],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InstallError("plithos_corpus SQLite build failed") from exc


def install(corpus_repo: Path, output_dir: Path) -> dict:
    lock = read_json(LOCK_PATH)
    corpus_repo = corpus_repo.resolve()
    corpus_dir, calendar_dir = verify_corpus(corpus_repo, lock)

    output_dir.mkdir(parents=True, exist_ok=True)
    final_db = output_dir / "plithos-en.sqlite"
    final_manifest = output_dir / "installed.json"
    final_calendar = output_dir / "calendar"

    with tempfile.TemporaryDirectory(prefix="oi-plithos-") as temp:
        temp_db = Path(temp) / "plithos-en.sqlite"
        build_sqlite(corpus_repo, corpus_dir, temp_db)
        db_hash = sha256_file(temp_db)
        shutil.copyfile(temp_db, final_db)

    if final_calendar.exists():
        shutil.rmtree(final_calendar)
    shutil.copytree(calendar_dir, final_calendar)

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
        "calendar": lock["calendar"],
        "source_file_sha256": lock["file_sha256"],
        "build_manifest_sha256": sha256_file(corpus_dir / "build.json"),
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
    parser.add_argument("--corpus-repo", type=Path, required=True,
                        help="local checkout of plithosorthodox/plithos_corpus at the pinned commit")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        installed = install(args.corpus_repo, args.output_dir)
    except InstallError as exc:
        raise SystemExit(f"Plithos install refused: {exc}")
    print(
        "installed Plithos corpus "
        f"{installed['corpus_commit'][:12]} with "
        f"{installed['counts']['entities']} entities / {installed['counts']['texts']} texts"
    )
    print("calendar: Revised Julian + Julian")
    print(f"artifact: {args.output_dir / 'plithos-en.sqlite'}")


if __name__ == "__main__":
    main()

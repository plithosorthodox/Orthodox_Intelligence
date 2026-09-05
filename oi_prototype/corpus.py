"""Small, inspectable SQLite evidence store for the first OI vertical slice."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from dataclasses import asdict, dataclass
from pathlib import Path


TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "does",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or",
    "that", "the", "this", "to", "what", "when", "where", "which",
    "who", "why", "with", "you", "your",
}


@dataclass(frozen=True)
class Evidence:
    record_id: str
    segment_id: str
    title: str
    citation_label: str
    source_locator: str
    source_class: str
    language: str
    display_text: str
    content_sha256: str
    exact_text: bool
    score: float
    origin: str = "local"
    provider: str = ""
    published_at: str = ""
    retrieved_at: str = ""
    citation_ref: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class CorpusError(ValueError):
    """Raised when the installed evidence package is internally inconsistent."""


class EvidenceStore:
    """An in-memory FTS5 index built from an immutable JSON demonstration pack."""

    def __init__(self, corpus_path: Path):
        payload = json.loads(corpus_path.read_text(encoding="utf-8"))
        self.corpus_id = self._required_text(payload, "corpus_id")
        self.corpus_version = self._required_text(payload, "corpus_version")
        records = payload.get("records")
        if not isinstance(records, list) or not records:
            raise CorpusError("corpus records must be a non-empty list")

        self._lock = threading.RLock()
        self._connection = sqlite3.connect(":memory:", check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            CREATE TABLE evidence (
                rowid INTEGER PRIMARY KEY,
                record_id TEXT NOT NULL,
                segment_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                citation_label TEXT NOT NULL,
                source_locator TEXT NOT NULL,
                source_class TEXT NOT NULL,
                language TEXT NOT NULL,
                display_text TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                exact_text INTEGER NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE VIRTUAL TABLE evidence_fts USING fts5(
                title,
                display_text,
                content='evidence',
                content_rowid='rowid',
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )

        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                raise CorpusError("every corpus record must be an object")
            segment_id = self._required_text(record, "segment_id")
            if segment_id in seen:
                raise CorpusError(f"duplicate segment_id: {segment_id}")
            seen.add(segment_id)
            text = self._required_text(record, "display_text")
            expected_hash = self._required_text(record, "content_sha256")
            actual_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_hash != expected_hash:
                raise CorpusError(f"content hash mismatch for {segment_id}")
            cursor = self._connection.execute(
                """
                INSERT INTO evidence (
                    record_id, segment_id, title, citation_label, source_locator,
                    source_class, language, display_text, content_sha256, exact_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._required_text(record, "record_id"),
                    segment_id,
                    self._required_text(record, "title"),
                    self._required_text(record, "citation_label"),
                    self._required_text(record, "source_locator"),
                    self._required_text(record, "source_class"),
                    self._required_text(record, "language"),
                    text,
                    expected_hash,
                    1 if record.get("exact_text") is True else 0,
                ),
            )
            self._connection.execute(
                "INSERT INTO evidence_fts(rowid, title, display_text) VALUES (?, ?, ?)",
                (cursor.lastrowid, record["title"], text),
            )
        self._connection.commit()
        self.record_count = len(records)

    @staticmethod
    def _required_text(value: dict[str, object], key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise CorpusError(f"missing non-empty string: {key}")
        return item

    @staticmethod
    def _fts_query(question: str) -> str:
        tokens = []
        for token in TOKEN.findall(question.casefold()):
            if len(token) < 2 or token in STOPWORDS or token in tokens:
                continue
            tokens.append(token)
        return " OR ".join('"%s"' % token.replace('"', '""') for token in tokens[:16])

    def search(self, question: str, limit: int = 4) -> list[Evidence]:
        query = self._fts_query(question)
        if not query:
            return []
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT e.*, bm25(evidence_fts, 3.0, 1.0) AS rank
                  FROM evidence_fts
                  JOIN evidence AS e ON e.rowid = evidence_fts.rowid
                 WHERE evidence_fts MATCH ?
                 ORDER BY rank, e.segment_id
                 LIMIT ?
                """,
                (query, max(1, min(limit, 10))),
            ).fetchall()
        return [
            Evidence(
                record_id=row["record_id"],
                segment_id=row["segment_id"],
                title=row["title"],
                citation_label=row["citation_label"],
                source_locator=row["source_locator"],
                source_class=row["source_class"],
                language=row["language"],
                display_text=row["display_text"],
                content_sha256=row["content_sha256"],
                exact_text=bool(row["exact_text"]),
                score=round(float(row["rank"]), 6),
            )
            for row in rows
        ]

    def resolve(self, segment_id: str) -> Evidence | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT *, 0.0 AS rank FROM evidence WHERE segment_id = ?", (segment_id,)
            ).fetchone()
        if row is None:
            return None
        return Evidence(
            record_id=row["record_id"],
            segment_id=row["segment_id"],
            title=row["title"],
            citation_label=row["citation_label"],
            source_locator=row["source_locator"],
            source_class=row["source_class"],
            language=row["language"],
            display_text=row["display_text"],
            content_sha256=row["content_sha256"],
            exact_text=bool(row["exact_text"]),
            score=0.0,
        )

"""Adapter from the installed Plithos corpus package to OI evidence records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .corpus import CorpusError, Evidence
from .plithos_search import CorpusSearch, normalize_search
from .retrieval import RetrievalResult, exact_result, merge_candidates, plan_query


INSTALL_MANIFEST = "installed.json"
DATABASE_NAME = "plithos-en.sqlite"
SCRIPTURE_REF = re.compile(r"(\d{1,3})\s*[:.]\s*(\d{1,3})")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class PlithosEvidenceStore:
    """Read-only OI adapter for a verified, locally installed Plithos SQLite file."""

    corpus_id = "plithos-english"

    def __init__(self, install_dir: Path):
        self.install_dir = Path(install_dir)
        manifest_path = self.install_dir / INSTALL_MANIFEST
        db_path = self.install_dir / DATABASE_NAME
        if not manifest_path.is_file() or not db_path.is_file():
            raise CorpusError(
                f"Plithos install requires {INSTALL_MANIFEST} and {DATABASE_NAME}"
            )

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CorpusError("invalid installed Plithos manifest") from exc

        expected_db_hash = self._required_text(manifest, "sqlite_sha256")
        if sha256_file(db_path) != expected_db_hash:
            raise CorpusError("installed Plithos SQLite hash does not match manifest")

        self.corpus_version = self._required_text(manifest, "corpus_commit")
        self.upstream_commit = self._required_text(manifest, "upstream_commit")
        self.language = self._required_text(manifest, "language")
        self.features = tuple(manifest.get("features") or ())
        counts = manifest.get("counts")
        if not isinstance(counts, dict):
            raise CorpusError("installed Plithos manifest has no counts object")
        self.entity_count = int(counts.get("entities", 0))
        self.record_count = int(counts.get("texts", 0))
        if self.entity_count <= 0 or self.record_count <= 0:
            raise CorpusError("installed Plithos counts must be positive")

        self._search = CorpusSearch(db_path)
        self._db = self._search.db
        self._verify_database()
        self.supports_exact_text = bool(
            self._db.execute(
                "SELECT 1 FROM texts WHERE exact_text=1 LIMIT 1"
            ).fetchone()
        )
        self.search_version = "plithos-search-c788cda3-oi-multiconcept1"

        self._scripture_books: list[tuple[str, str]] = []
        for row in self._db.execute(
            """
            SELECT e.entity_id, n.name
              FROM entities e
              JOIN names n ON n.entity_id=e.entity_id
             WHERE e.entity_type='scripture' AND n.name_type='canonical'
             ORDER BY length(n.name) DESC, n.name
            """
        ):
            self._scripture_books.append((row["entity_id"], normalize_search(row["name"])))

        self._exact_named_entities: list[tuple[str, str]] = []
        for row in self._db.execute(
            """
            SELECT DISTINCT e.entity_id, n.name
              FROM texts t
              JOIN entities e ON e.entity_id=t.entity_id
              JOIN names n ON n.entity_id=e.entity_id
             WHERE t.exact_text=1
               AND e.entity_type<>'scripture'
               AND n.name_type='canonical'
             ORDER BY length(n.name) DESC, n.name
            """
        ):
            self._exact_named_entities.append(
                (row["entity_id"], normalize_search(row["name"]))
            )

    @staticmethod
    def _required_text(value: dict[str, object], key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise CorpusError(f"missing non-empty installed-manifest string: {key}")
        return item

    def _verify_database(self) -> None:
        metadata = {
            row["key"]: row["value"]
            for row in self._db.execute("SELECT key, value FROM metadata")
        }
        if metadata.get("language") != self.language:
            raise CorpusError("installed Plithos database language mismatch")
        if metadata.get("upstream_commit") != self.upstream_commit:
            raise CorpusError("installed Plithos upstream commit mismatch")
        if int(metadata.get("entity_count", "-1")) != self.entity_count:
            raise CorpusError("installed Plithos entity count mismatch")
        if int(metadata.get("text_count", "-1")) != self.record_count:
            raise CorpusError("installed Plithos text count mismatch")

    def close(self) -> None:
        self._search.close()

    def suggest(self, question: str) -> str | None:
        return self._search.did_you_mean(question)

    def _scripture_reference_text_id(self, question: str) -> str | None:
        normalized = normalize_search(question)
        for entity_id, book in self._scripture_books:
            pattern = re.compile(
                rf"(?<![0-9a-z]){re.escape(book)}\s+{SCRIPTURE_REF.pattern}(?![0-9])"
            )
            match = pattern.search(normalized)
            if not match:
                continue
            chapter, verse = int(match.group(1)), int(match.group(2))
            with self._search.connection() as db:
                rows = db.execute(
                    "SELECT text_id, metadata_json FROM texts WHERE entity_id=? AND text_kind='scripture'",
                    (entity_id,),
                ).fetchall()
            for row in rows:
                metadata = json.loads(row["metadata_json"])
                if metadata.get("chapter") == chapter and metadata.get("verse") == verse:
                    return row["text_id"]
        return None

    def _named_exact_text_id(self, question: str) -> str | None:
        normalized = normalize_search(question)
        for entity_id, title in self._exact_named_entities:
            if len(title) >= 4 and title in normalized:
                with self._search.connection() as db:
                    row = db.execute(
                        """
                        SELECT text_id
                          FROM texts
                         WHERE entity_id=? AND exact_text=1
                         ORDER BY text_id
                         LIMIT 1
                        """,
                        (entity_id,),
                    ).fetchone()
                if row:
                    return row["text_id"]
        return None

    def _best_text_id(self, entity_id: str) -> str | None:
        with self._search.connection() as db:
            row = db.execute(
                """
                SELECT text_id
                  FROM texts
                 WHERE entity_id=?
                 ORDER BY CASE text_kind
                     WHEN 'hagiography' THEN 0
                     WHEN 'definition' THEN 0
                     WHEN 'prayer' THEN 0
                     WHEN 'scripture' THEN 0
                     WHEN 'patristic' THEN 0
                     WHEN 'canon' THEN 0
                     WHEN 'liturgical' THEN 0
                     WHEN 'ascetic' THEN 0
                     WHEN 'testimony' THEN 0
                     ELSE 1 END,
                     text_id
                 LIMIT 1
                """,
                (entity_id,),
            ).fetchone()
        return row["text_id"] if row else None

    def _evidence_for_text(
        self,
        text_id: str,
        *,
        title_hint: str = "",
        score: float = 0.0,
    ) -> Evidence | None:
        with self._search.connection() as db:
            row = db.execute(
                """
                SELECT t.*, e.entity_type,
                       COALESCE(
                           (SELECT n.name FROM names n
                             WHERE n.entity_id=t.entity_id AND n.name_type='canonical'
                             ORDER BY n.name_id LIMIT 1),
                           ?
                       ) AS canonical_name
                  FROM texts t
                  JOIN entities e ON e.entity_id=t.entity_id
                 WHERE t.text_id=?
                """,
                (title_hint, text_id),
            ).fetchone()
            if row is None:
                return None
            source = db.execute(
                """
                SELECT s.source_class, s.record_json
                  FROM text_sources ts
                  JOIN sources s ON s.source_id=ts.source_id
                 WHERE ts.text_id=?
                 ORDER BY s.source_id
                 LIMIT 1
                """,
                (text_id,),
            ).fetchone()

        metadata = json.loads(row["metadata_json"])
        upstream = json.loads(row["upstream_json"])
        source_class = source["source_class"] if source else row["text_kind"]
        title = row["canonical_name"] or title_hint or row["entity_id"]
        citation_label = metadata.get("citation_anchor") or title
        source_locator = upstream.get("origin") or ""
        if source and not source_locator:
            source_record = json.loads(source["record_json"])
            source_locator = source_record.get("locator") or ""

        return Evidence(
            record_id=row["entity_id"],
            segment_id=row["text_id"],
            title=title,
            citation_label=str(citation_label),
            source_locator=str(source_locator),
            source_class=str(source_class),
            language=row["language"],
            display_text=row["content"],
            content_sha256=row["sha256"],
            exact_text=bool(row["exact_text"]),
            score=round(float(score), 6),
            origin="plithos",
            provider=self.search_version,
        )

    def _evidence_for_hits(self, question: str, limit: int) -> list[Evidence]:
        hits = self._search.search(question, limit=max(limit * 4, 16))
        evidence: list[Evidence] = []
        seen_text_ids: set[str] = set()
        for hit in hits:
            if hit.kind == "name":
                text_id = self._best_text_id(hit.entity_id)
            else:
                text_id = hit.record_id
            if not text_id or text_id in seen_text_ids:
                continue
            item = self._evidence_for_text(
                text_id,
                title_hint=hit.title,
                score=hit.bm25 if hit.bm25 is not None else float(hit.score),
            )
            if item is None:
                continue
            seen_text_ids.add(text_id)
            evidence.append(item)
        return evidence

    def retrieve(self, question: str, limit: int = 4) -> RetrievalResult:
        """Retrieve a relevant, concept-covering evidence set.

        The exact-text resolver remains ahead of ordinary ranking.  Other
        questions are planned into a combined query and bounded concept lanes;
        evidence which only happens to share an unrelated word is not returned
        as a sufficient corpus answer.
        """

        limit = max(1, min(int(limit), 10))
        direct_text = (
            self._scripture_reference_text_id(question)
            or self._named_exact_text_id(question)
        )
        if direct_text:
            evidence = self._evidence_for_text(direct_text, score=0.0)
            if evidence is not None:
                return exact_result(question, evidence)

        plan = plan_query(question)
        ranked: dict[str, list[Evidence]] = {}
        queries: list[str] = []
        for concept in plan.concepts:
            token_query = " ".join(concept.tokens)
            if len(concept.tokens) >= 2:
                queries.extend((token_query, concept.query))
            else:
                queries.extend((concept.query, token_query))
        queries.append(plan.combined_query)
        for query in queries:
            normalized = " ".join(query.split())
            if not normalized or normalized in ranked:
                continue
            ranked[normalized] = self._evidence_for_hits(normalized, limit)
        return merge_candidates(plan, ranked, limit=limit)

    def search(self, question: str, limit: int = 4) -> list[Evidence]:
        """Compatibility list API, returning only a sufficient evidence set."""

        result = self.retrieve(question, limit=limit)
        return list(result.evidence) if result.sufficient else []

    def resolve(self, segment_id: str) -> Evidence | None:
        return self._evidence_for_text(segment_id)

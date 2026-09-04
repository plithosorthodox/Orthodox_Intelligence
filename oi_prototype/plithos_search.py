"""Deterministic Plithos lexical-search primitives.

Ported from plithosorthodox/plithos_corpus at commit
c788cda3e9c24246ab41cfd6aa74ecbcaf082b83. The original reusable search
behavior derives from plithos.org commit
10b8e63b157765ed902e7dfe2f7c01f1c390deb9.

This copy keeps the OI runtime self-contained while preserving the corpus-side
normalization, transliteration, received-name aliases, typo suggestions, and
name-first ranking behavior. Candidate retrieval is performed against the
installed Plithos SQLite/FTS5 artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import threading
import unicodedata
from typing import Iterable

ALIAS_FAMILIES = (
    ("elijah", ("elias", "ilias", "ilya", "ilia", "iliya")),
    ("katherine", ("catherine",)),
    ("john", ("ivan", "jovan", "giovanni")),
    ("george", ("yuri", "yury", "jiri", "gjergj")),
    ("theodore", ("feodor", "fyodor", "fedor")),
    ("vladimir", ("volodymyr", "volodya")),
    ("demetri", ("dmitri", "dmitry", "dimitri", "demetrius")),
    ("basil", ("vasily", "vasil")),
    ("paraskev", ("parascheva",)),
    ("cosmas", ("unmercenaries", "anargyroi")),
    ("nicholas", ("nikola",)),
)

TRANSLITERATION = {
    "α":"a","β":"v","γ":"g","δ":"d","ε":"e","ζ":"z","η":"i","θ":"th","ι":"i","κ":"k","λ":"l","μ":"m","ν":"n","ξ":"x","ο":"o","π":"p","ρ":"r","σ":"s","ς":"s","τ":"t","υ":"y","φ":"f","χ":"ch","ψ":"ps","ω":"o","ϊ":"i","ϋ":"y",
    "а":"a","б":"b","в":"v","г":"g","ґ":"g","д":"d","ђ":"dj","е":"e","ё":"e","є":"ye","ж":"zh","з":"z","и":"i","і":"i","ї":"yi","й":"y","ј":"j","к":"k","л":"l","љ":"l","м":"m","н":"n","њ":"n","о":"o","п":"p","р":"r","с":"s","т":"t","ћ":"c","у":"u","ф":"f","х":"kh","ц":"ts","ч":"ch","џ":"dz","ш":"sh","щ":"shch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya",
}

_WORD_RE = re.compile(r"[0-9a-z\u0370-\u03ff\u0400-\u04ff\u0600-\u06ff]+")
_LATIN_RE = re.compile(r"[0-9a-z]+")
_SPLIT_RE = re.compile(r"[\s,.;:()\[\]\"'‘’“”·/–—-]+")


def normalize_search(value: object) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFD", str(value))
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text)
    text = (text.replace("\u0622", "\u0627")
                .replace("\u0623", "\u0627")
                .replace("\u0625", "\u0627")
                .replace("\u0649", "\u064a")
                .replace("\u0629", "\u0647")
                .replace("\u03c2", "\u03c3"))
    return text.lower().strip()


def transliterate_latin(value: object) -> str:
    normalized = normalize_search(value)
    out = []
    for char in normalized:
        if char in TRANSLITERATION:
            out.append(TRANSLITERATION[char])
        elif ("a" <= char <= "z") or ("0" <= char <= "9") or char == " ":
            out.append(char)
    return "".join(out)


def search_key(value: object) -> str:
    normalized = normalize_search(value)
    transliterated = transliterate_latin(normalized)
    if transliterated and transliterated != normalized:
        return normalized + " " + transliterated
    return normalized


def search_words(value: object) -> list[str]:
    return _WORD_RE.findall(normalize_search(value))


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def alias_variants(value: object) -> tuple[str, ...]:
    normalized = normalize_search(value)
    transliterated = transliterate_latin(normalized)
    seeds = {normalized}
    if transliterated:
        seeds.add(transliterated)
    tokens = set()
    for seed in seeds:
        tokens.update(_LATIN_RE.findall(seed))
    expanded = set(seeds)
    for canonical, aliases in ALIAS_FAMILIES:
        family = {canonical, *aliases}
        if tokens.intersection(family):
            expanded.update(family)
    return tuple(sorted(v for v in expanded if v))


def display_name_score(query: object, display_name: object) -> int:
    nq = normalize_search(query)
    dn = normalize_search(display_name)
    words = search_words(dn)
    if dn == nq:
        return 0
    if nq in words:
        return 1
    if dn.startswith(nq):
        return 2
    if any(word.startswith(nq) for word in words):
        return 3
    if nq and nq in dn:
        return 4
    return 5


@dataclass(frozen=True)
class SearchHit:
    record_id: str
    entity_id: str
    entity_type: str
    kind: str
    title: str
    snippet: str
    score: int
    match: str
    great: bool = False
    bm25: float | None = None


class CorpusSearch:
    """Search a compiled ``plithos-en.sqlite`` artifact."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        # check_same_thread=False plus a lock, matching EvidenceStore in
        # corpus.py. The prototype server is a ThreadingHTTPServer, so the
        # connection is opened on the main thread and used from a different
        # worker thread on every request; without this, each question raises
        # sqlite3.ProgrammingError once a real corpus is installed. The
        # connection is read-only, and the lock keeps concurrent queries from
        # sharing one cursor.
        self.db = sqlite3.connect(
            f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False
        )
        self._lock = threading.RLock()
        self.db.row_factory = sqlite3.Row
        self._entities = {r["entity_id"]: r for r in self.db.execute(
            "SELECT entity_id, entity_type, great FROM entities ORDER BY entity_id")}
        self._names: dict[str, list[sqlite3.Row]] = {}
        for row in self.db.execute(
            "SELECT name_id, entity_id, language, name, name_type FROM names ORDER BY entity_id, name_type, name"):
            self._names.setdefault(row["entity_id"], []).append(row)
        self._has_text = {r[0] for r in self.db.execute("SELECT DISTINCT entity_id FROM texts")}
        self._vocabulary = self._build_vocabulary()

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _canonical_name(self, entity_id: str) -> str:
        rows = self._names.get(entity_id, ())
        for row in rows:
            if row["name_type"] == "canonical":
                return row["name"]
        return rows[0]["name"] if rows else ""

    def _entity_search_names(self, entity_id: str) -> list[str]:
        names = [r["name"] for r in self._names.get(entity_id, ())]
        canonical = normalize_search(self._canonical_name(entity_id))
        for family_name, aliases in ALIAS_FAMILIES:
            if family_name in canonical:
                names.extend(aliases)
        return names

    def _build_vocabulary(self) -> tuple[tuple[str, str], ...]:
        seen = set()
        out = []
        for entity_id in sorted(self._names):
            for row in self._names[entity_id]:
                for piece in _SPLIT_RE.split(row["name"]):
                    word = normalize_search(piece)
                    if len(word) >= 3 and word not in seen:
                        seen.add(word)
                        out.append((word, piece))
        return tuple(out)

    def did_you_mean(self, query: object) -> str | None:
        nq = normalize_search(query)
        if len(nq) < 3 or " " in nq:
            return None
        best = None
        best_distance = 99
        for word, display in self._vocabulary:
            if abs(len(word) - len(nq)) > 3:
                continue
            distance = levenshtein(nq, word)
            if distance < best_distance:
                best_distance = distance
                best = display
                if distance == 1:
                    break
        threshold = max(1, len(nq) // 3)
        return best if best and 0 < best_distance <= threshold else None

    @staticmethod
    def _fts_tokens(value: str) -> list[str]:
        normalized = transliterate_latin(value) or normalize_search(value)
        return _LATIN_RE.findall(normalized)

    def _fts_expression(self, query: object) -> str | None:
        clauses = []
        for variant in alias_variants(query):
            tokens = self._fts_tokens(variant)
            if not tokens:
                continue
            clause = " AND ".join(f'"{token}"' for token in tokens)
            if clause not in clauses:
                clauses.append(clause)
        return " OR ".join(f"({c})" for c in clauses) if clauses else None

    def _name_hits(self, query: object, entity_types: set[str] | None) -> dict[str, SearchHit]:
        variants = alias_variants(query)
        hits = {}
        for entity_id, entity in self._entities.items():
            if entity_types and entity["entity_type"] not in entity_types:
                continue
            names = self._entity_search_names(entity_id)
            matched = False
            best_score = 5
            for variant in variants:
                for name in names:
                    if variant and variant in search_key(name):
                        matched = True
                        best_score = min(best_score, display_name_score(variant, name))
            if not matched:
                continue
            canonical_row = next((r for r in self._names.get(entity_id, ()) if r["name_type"] == "canonical"), None)
            title = self._canonical_name(entity_id)
            hits[entity_id] = SearchHit(
                record_id=canonical_row["name_id"] if canonical_row else entity_id,
                entity_id=entity_id,
                entity_type=entity["entity_type"],
                kind="name",
                title=title,
                snippet="",
                score=best_score,
                match="name",
                great=bool(entity["great"]),
            )
        return hits

    def _body_hits(self, query: object, entity_types: set[str] | None, limit: int) -> list[SearchHit]:
        expr = self._fts_expression(query)
        if not expr:
            return []
        sql = """
            SELECT f.record_id, f.entity_id, f.kind, f.title,
                   snippet(search_fts, 5, '', '', ' … ', 24) AS snip,
                   bm25(search_fts, 0.0, 0.0, 0.0, 0.0, 3.0, 1.0) AS rank,
                   e.entity_type, e.great
            FROM search_fts AS f
            JOIN entities AS e ON e.entity_id=f.entity_id
            WHERE search_fts MATCH ?
        """
        params: list[object] = [expr]
        if entity_types:
            marks = ",".join("?" for _ in entity_types)
            sql += f" AND e.entity_type IN ({marks})"
            params.extend(sorted(entity_types))
        sql += " ORDER BY rank ASC, e.great DESC, f.record_id ASC LIMIT ?"
        params.append(max(limit * 8, 80))
        out = []
        with self._lock:
            rows = self.db.execute(sql, params).fetchall()
        for row in rows:
            out.append(SearchHit(
                record_id=row["record_id"], entity_id=row["entity_id"],
                entity_type=row["entity_type"], kind=row["kind"],
                title=row["title"] or self._canonical_name(row["entity_id"]),
                snippet=row["snip"] or "", score=5, match="text",
                great=bool(row["great"]), bm25=float(row["rank"]),
            ))
        return out

    def search(self, query: object, *, entity_types: Iterable[str] | None = None, limit: int = 20) -> list[SearchHit]:
        if limit <= 0 or len(normalize_search(query)) < 2:
            return []
        allowed = set(entity_types) if entity_types else None
        name_hits = self._name_hits(query, allowed)
        combined = {(h.entity_id, h.record_id): h for h in name_hits.values()}
        for hit in self._body_hits(query, allowed, limit):
            combined.setdefault((hit.entity_id, hit.record_id), hit)

        def key(hit: SearchHit):
            return (
                hit.score,
                0 if hit.entity_id in self._has_text else 1,
                0 if hit.great else 1,
                hit.bm25 if hit.bm25 is not None else 0.0,
                len(hit.title),
                normalize_search(hit.title),
                hit.record_id,
            )
        return sorted(combined.values(), key=key)[:limit]

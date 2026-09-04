import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oi_prototype.engine import PrototypeEngine  # noqa: E402
from oi_prototype.plithos_store import PlithosEvidenceStore  # noqa: E402
from oi_prototype.policy import BoundaryPolicy  # noqa: E402


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_install(root: Path) -> Path:
    install = root / "plithos"
    install.mkdir()
    db_path = install / "plithos-en.sqlite"
    db = sqlite3.connect(db_path)
    db.executescript(
        """
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
        CREATE TABLE entities (
            entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL,
            canonical_key TEXT NOT NULL, great INTEGER NOT NULL,
            metadata_json TEXT NOT NULL, upstream_json TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE names (
            name_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL,
            language TEXT NOT NULL, name TEXT NOT NULL,
            name_type TEXT NOT NULL, upstream_json TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY, label TEXT NOT NULL,
            source_class TEXT NOT NULL, rights_status TEXT NOT NULL,
            record_json TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE texts (
            text_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL,
            language TEXT NOT NULL, text_kind TEXT NOT NULL,
            content TEXT NOT NULL, sha256 TEXT NOT NULL,
            exact_text INTEGER NOT NULL, translation_status TEXT NOT NULL,
            upstream_json TEXT NOT NULL, metadata_json TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE text_sources (
            text_id TEXT NOT NULL, source_id TEXT NOT NULL,
            PRIMARY KEY (text_id, source_id)
        ) WITHOUT ROWID;
        CREATE VIRTUAL TABLE search_fts USING fts5(
            record_id UNINDEXED, entity_id UNINDEXED,
            language UNINDEXED, kind UNINDEXED,
            title, body, tokenize='unicode61 remove_diacritics 2'
        );
        """
    )

    entities = [
        ("saint:nicholas", "saint", "nicholas", 0, "St Nicholas"),
        ("work:incarnation", "work", "incarnation", 0, "On the Incarnation"),
        ("scripture:en:43", "scripture", "en:43", 0, "John"),
    ]
    for entity_id, entity_type, key, great, title in entities:
        db.execute(
            "INSERT INTO entities VALUES (?,?,?,?,?,?)",
            (entity_id, entity_type, key, great, "{}", '{"origin":"fixture"}'),
        )
        name_id = "name:" + entity_id
        db.execute(
            "INSERT INTO names VALUES (?,?,?,?,?,?)",
            (name_id, entity_id, "en", title, "canonical", '{"origin":"fixture"}'),
        )
        db.execute(
            "INSERT INTO search_fts VALUES (?,?,?,?,?,?)",
            (name_id, entity_id, "en", "name", title, ""),
        )

    sources = [
        ("source:hag", "Fixture Synaxarion", "hagiographic", "private"),
        ("source:pat", "Fixture Father", "patristic", "private"),
        ("source:scr", "Fixture Scripture", "scripture", "public_domain"),
    ]
    for source_id, label, source_class, rights in sources:
        record = {
            "source_id": source_id,
            "label": label,
            "source_class": source_class,
            "rights_status": rights,
            "locator": "fixture",
        }
        db.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?)",
            (source_id, label, source_class, rights, json.dumps(record)),
        )

    records = [
        (
            "text:nicholas", "saint:nicholas", "hagiography",
            "Saint Nicholas was bishop of Myra and is remembered for generosity.",
            0, "source:hag", {},
        ),
        (
            "text:incarnation", "work:incarnation", "patristic",
            "The Incarnation is treated here as the Word taking flesh for our salvation.",
            0, "source:pat", {"citation_anchor": "On the Incarnation §1"},
        ),
        (
            "text:john316", "scripture:en:43", "scripture",
            "For God so loved the world, that he gave his only begotten Son.",
            1, "source:scr", {"chapter": 3, "verse": 16, "citation_anchor": "John 3:16"},
        ),
    ]
    for text_id, entity_id, kind, content, exact, source_id, metadata in records:
        db.execute(
            "INSERT INTO texts VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                text_id, entity_id, "en", kind, content, _hash(content), exact,
                "source", '{"origin":"fixture"}', json.dumps(metadata),
            ),
        )
        db.execute("INSERT INTO text_sources VALUES (?,?)", (text_id, source_id))
        title = next(title for eid, _, _, _, title in entities if eid == entity_id)
        db.execute(
            "INSERT INTO search_fts VALUES (?,?,?,?,?,?)",
            (text_id, entity_id, "en", kind, title, content),
        )

    metadata = {
        "schema_version": "1",
        "language": "en",
        "upstream_commit": "fixture-upstream",
        "entity_count": "3",
        "text_count": "3",
    }
    for key, value in metadata.items():
        db.execute("INSERT INTO metadata VALUES (?,?)", (key, value))
    db.commit()
    db.close()

    db_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    (install / "installed.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_commit": "fixture-corpus",
                "upstream_commit": "fixture-upstream",
                "language": "en",
                "features": ["saints", "scripture", "library"],
                "counts": {"entities": 3, "texts": 3},
                "sqlite_sha256": db_hash,
            }
        ),
        encoding="utf-8",
    )
    return install


class PlithosRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.install = make_install(Path(self.temp.name))
        self.store = PlithosEvidenceStore(self.install)

    def tearDown(self):
        if self.store is not None:
            self.store.close()
        self.temp.cleanup()

    def test_alias_search_uses_ported_plithos_rules(self):
        hits = self.store.search("Nikola")
        self.assertTrue(hits)
        self.assertEqual("St Nicholas", hits[0].title)

    def test_library_text_is_retrievable(self):
        hits = self.store.search("Incarnation")
        self.assertTrue(hits)
        self.assertIn("Incarnation", hits[0].title)

    def test_scripture_reference_resolves_exact_text(self):
        hits = self.store.search("Quote John 3:16 exactly.")
        self.assertEqual(1, len(hits))
        self.assertTrue(hits[0].exact_text)
        self.assertEqual("John 3:16", hits[0].citation_label)

    def test_engine_uses_installed_exact_text_instead_of_demo_abstention(self):
        engine = PrototypeEngine(
            self.store,
            BoundaryPolicy(ROOT / "config" / "prototype_policy.v0.2.json"),
        )
        answer = engine.ask("Quote John 3:16 exactly.")
        self.assertEqual("evidence", answer.response_class)
        self.assertEqual("exact_text", answer.intent)
        self.assertTrue(answer.evidence[0].exact_text)

    def test_modified_database_is_refused(self):
        self.store.close()
        self.store = None
        with (self.install / "plithos-en.sqlite").open("ab") as handle:
            handle.write(b"x")
        with self.assertRaises(ValueError):
            PlithosEvidenceStore(self.install)


if __name__ == "__main__":
    unittest.main()

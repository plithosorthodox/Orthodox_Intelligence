import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_repository", ROOT / "tools" / "check_repository.py"
)
check_repository = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_repository)


class RepositoryTests(unittest.TestCase):
    def test_repository_checker(self):
        self.assertEqual([], check_repository.check())

    def test_schema_identifiers_are_unique(self):
        identifiers = []
        for path in sorted((ROOT / "schemas").glob("*.json")):
            identifiers.append(json.loads(path.read_text(encoding="utf-8"))["$id"])
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_acceptance_thresholds_are_explicitly_provisional(self):
        criteria = json.loads(
            (ROOT / "config" / "acceptance_criteria.v0.1.json").read_text(encoding="utf-8")
        )
        self.assertEqual("provisional", criteria["status"])
        self.assertTrue(criteria["ratification_required"])
        self.assertIsNone(criteria["ratification_record"])

    def test_training_schema_excludes_locked_evaluation_split(self):
        schema = json.loads(
            (ROOT / "schemas" / "training-example.schema.json").read_text(encoding="utf-8")
        )
        allowed = schema["properties"]["dataset_split"]["enum"]
        self.assertEqual(["training", "development"], allowed)

    def test_full_factorial_is_controlling_design(self):
        text = (
            ROOT / "docs" / "OI_RESEARCH_AND_TRAINING_SPECIFICATION_v0.1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("2 x 2 x 2", text)
        for marker in ("S0", "S1", "E0", "E1", "R0", "R1"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()


from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from scripts.validate_repository import validate_repository


class RepositoryValidationTest(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def copy_repository(self, destination: Path) -> None:
        for name in ["domains", "examples", "mappings", "packages", "profiles", "rules", "terms"]:
            shutil.copytree(self.root / name, destination / name)

    def test_repository_is_self_consistent(self):
        problems = validate_repository(self.root)
        self.assertEqual([], [str(problem) for problem in problems])

    def test_non_string_object_identifier_and_version_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            domain_path = root / "domains" / "core" / "domain.yaml"
            domain = yaml.safe_load(domain_path.read_text(encoding="utf-8"))
            domain["id"] = 123
            domain["version"] = 1.0
            domain_path.write_text(yaml.safe_dump(domain, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertIn("object identifier must be a string: 123", messages)
        self.assertIn("version must be a string: 1.0", messages)

    def test_term_versions_are_required_and_must_be_strings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            registry_path = root / "terms" / "registry.yaml"
            registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
            registry["terms"][0].pop("version")
            registry["terms"][1]["version"] = 1.0
            registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertTrue(any(message.startswith("term missing required key version:") for message in messages))
        self.assertIn(
            "Term version must be a string for relay.term.dataset-release: 1.0",
            messages,
        )

    def test_malformed_term_collects_a_diagnostic_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            registry_path = root / "terms" / "registry.yaml"
            registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
            registry["terms"].append("not-a-mapping")
            registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertIn("each term must be a mapping", messages)

    def test_mapping_entries_require_impact_and_reviewer_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            mapping_path = root / "mappings" / "isa" / "mapping.yaml"
            mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
            mapping["entries"] = [{
                "source": "relay.term.dataset",
                "target": "isa:Investigation",
                "relation": "close",
                "conditions": [],
                "transformation": None,
                "information_loss": [],
                "evidence": [],
                "review_status": "unreviewed",
            }]
            mapping_path.write_text(yaml.safe_dump(mapping, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertTrue(any("mapping entry missing key cardinality_or_datatype_impact" in message for message in messages))
        self.assertTrue(any("mapping entry missing key reviewer" in message for message in messages))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import json
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

    def test_malformed_nested_containers_are_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)

            domain_path = root / "domains" / "core" / "domain.yaml"
            domain = yaml.safe_load(domain_path.read_text(encoding="utf-8"))
            domain["dependencies"] = 1
            domain_path.write_text(yaml.safe_dump(domain, sort_keys=False), encoding="utf-8")

            profile_path = root / "profiles" / "core-exchange" / "profile.yaml"
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            profile["requirements"] = []
            profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

            mapping_path = root / "mappings" / "isa" / "mapping.yaml"
            mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
            mapping["entries"] = [1]
            mapping_path.write_text(yaml.safe_dump(mapping, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertIn("dependencies must be a list", messages)
        self.assertIn("document root must be a mapping", messages)

    def test_empty_descriptor_and_wrong_identifier_kind_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)

            mapping_path = root / "mappings" / "isa" / "mapping.yaml"
            mapping_path.write_text("{}\n", encoding="utf-8")

            other_mapping_path = root / "mappings" / "prov-o" / "mapping.yaml"
            mapping = yaml.safe_load(other_mapping_path.read_text(encoding="utf-8"))
            mapping["id"] = "relay.domain.not-a-mapping"
            other_mapping_path.write_text(
                yaml.safe_dump(mapping, sort_keys=False),
                encoding="utf-8",
            )

            messages = [problem.message for problem in validate_repository(root)]

        self.assertIn("missing required key: object_type", messages)
        self.assertIn("invalid mapping identifier: relay.domain.not-a-mapping", messages)

    def test_unknown_rule_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            registry_path = root / "rules" / "registry.yaml"
            registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
            registry["rules"][0]["scope"] = ["relay.domain.does-not-exist"]
            registry_path.write_text(
                yaml.safe_dump(registry, sort_keys=False),
                encoding="utf-8",
            )

            messages = [problem.message for problem in validate_repository(root)]

        self.assertIn(
            "Rule RELAY-CORE-001 has unknown scope: relay.domain.does-not-exist",
            messages,
        )

    def test_duplicate_yaml_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            mapping_path = root / "mappings" / "isa" / "mapping.yaml"
            mapping_path.write_text(
                "object_type: mapping\nobject_type: domain\n",
                encoding="utf-8",
            )

            messages = [problem.message for problem in validate_repository(root)]

        self.assertTrue(any("found duplicate key: 'object_type'" in message for message in messages))

    def test_semver_build_metadata_is_allowed_and_malformed_prerelease_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)
            core_path = root / "domains" / "core" / "domain.yaml"
            core = yaml.safe_load(core_path.read_text(encoding="utf-8"))
            core["version"] = "1.0.0+build.1"
            core_path.write_text(yaml.safe_dump(core, sort_keys=False), encoding="utf-8")

            isa_path = root / "domains" / "isa" / "domain.yaml"
            isa = yaml.safe_load(isa_path.read_text(encoding="utf-8"))
            isa["version"] = "1.0.0-alpha..1"
            isa_path.write_text(yaml.safe_dump(isa, sort_keys=False), encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertNotIn("version is not semantic versioning: 1.0.0+build.1", messages)
        self.assertIn("version is not semantic versioning: 1.0.0-alpha..1", messages)

    def test_json_is_strict_and_manifest_integrity_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_repository(root)

            nan_json = root / "examples" / "nan.json"
            nan_json.write_text('{"value": NaN}\n', encoding="utf-8")
            duplicate_json = root / "examples" / "duplicate.json"
            duplicate_json.write_text('{"value": 1, "value": 2}\n', encoding="utf-8")

            manifest_path = (
                root
                / "examples"
                / "draft"
                / "minimal-ro-crate"
                / "validation"
                / "relay-package-manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["entries"][0]["byte_size"] = 1
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            messages = [problem.message for problem in validate_repository(root)]

        self.assertTrue(any("non-standard JSON constant: NaN" in message for message in messages))
        self.assertTrue(any("duplicate JSON object key: value" in message for message in messages))
        self.assertTrue(
            any(
                message.startswith(
                    "package manifest byte_size mismatch for metadata/relay-core.json"
                )
                for message in messages
            )
        )


if __name__ == "__main__":
    unittest.main()

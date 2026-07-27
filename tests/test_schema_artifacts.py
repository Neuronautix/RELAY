from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml


class SchemaArtifactTest(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schemas" / "relay-descriptor.schema.json"

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(cls.schema_path.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def canonical_descriptor_paths(self):
        yield self.root / "terms" / "registry.yaml"
        yield from sorted(
            path
            for path in (self.root / "domains").glob("*/domain.yaml")
            if not path.parent.name.startswith("_")
        )
        yield from sorted(
            path
            for path in (self.root / "profiles").glob("*/profile.yaml")
            if not path.parent.name.startswith("_")
        )
        yield from sorted(
            path
            for path in (self.root / "packages").glob("*/package.yaml")
            if not path.parent.name.startswith("_")
        )
        yield from sorted(
            path
            for path in (self.root / "mappings").glob("*/mapping.yaml")
            if not path.parent.name.startswith("_")
        )
        yield self.root / "rules" / "registry.yaml"

    def test_schema_is_valid_json_schema_2020_12(self):
        Draft202012Validator.check_schema(self.schema)

    def test_every_canonical_descriptor_conforms(self):
        for path in self.canonical_descriptor_paths():
            with self.subTest(path=path.relative_to(self.root)):
                descriptor = yaml.safe_load(path.read_text(encoding="utf-8"))
                errors = sorted(
                    self.validator.iter_errors(descriptor),
                    key=lambda error: list(error.absolute_path),
                )
                self.assertEqual([], [error.message for error in errors])

    def test_every_first_class_object_template_conforms(self):
        template_paths = [
            "terms/_template.yaml",
            "domains/_template/domain.yaml",
            "profiles/_template/profile.yaml",
            "packages/_template/package.yaml",
            "mappings/_template/mapping.yaml",
            "rules/_template.yaml",
        ]
        for relative_path in template_paths:
            with self.subTest(path=relative_path):
                descriptor = yaml.safe_load(
                    (self.root / relative_path).read_text(encoding="utf-8")
                )
                errors = list(self.validator.iter_errors(descriptor))
                self.assertEqual([], [error.message for error in errors])

    def test_wrong_identifier_kind_and_missing_nested_requirement_fail(self):
        descriptor = yaml.safe_load(
            (self.root / "domains" / "core" / "domain.yaml").read_text(
                encoding="utf-8"
            )
        )
        descriptor["id"] = "relay.profile.core"
        descriptor["scope"].pop("includes")

        errors = list(self.validator.iter_errors(descriptor))

        self.assertTrue(errors)
        diagnostic = "\n".join(error.message for error in errors)
        self.assertIn("is not valid under any of the given schemas", diagnostic)

    def test_jsonld_and_shacl_use_the_same_provisional_vocabulary(self):
        context_path = (
            self.root / "schemas" / "contexts" / "relay-descriptor.context.jsonld"
        )
        context = json.loads(context_path.read_text(encoding="utf-8"))
        shacl = (
            self.root / "schemas" / "shacl" / "relay-descriptor.shacl.ttl"
        ).read_text(encoding="utf-8")
        namespace = yaml.safe_load(
            (self.root / "namespace.yaml").read_text(encoding="utf-8")
        )["namespace"]

        self.assertEqual(
            namespace["canonical_base_uri"],
            context["@context"]["relay"],
        )
        self.assertEqual(
            "proposed",
            context["x-relay-generation"]["namespace"]["status"],
        )
        self.assertIn(
            f"@prefix relay: <{namespace['canonical_base_uri']}> .",
            shacl,
        )
        self.assertEqual(
            context["x-relay-generation"],
            self.schema["x-relay-generation"],
        )
        self.assertIn("# x-relay-generation:", shacl)

    def test_source_hashes_and_registry_members_match_canonical_sources(self):
        metadata = self.schema["x-relay-generation"]
        sources = {source["path"]: source for source in metadata["sources"]}
        for relative_path, source in sources.items():
            with self.subTest(path=relative_path):
                text = (self.root / relative_path).read_text(encoding="utf-8")
                canonical_text = text.replace("\r\n", "\n").replace("\r", "\n")
                digest = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
                self.assertEqual(source["sha256_canonical_lf"], digest)

        registry_members = {
            "terms/registry.yaml": "terms",
            "rules/registry.yaml": "rules",
        }
        for relative_path, member_key in registry_members.items():
            registry = yaml.safe_load(
                (self.root / relative_path).read_text(encoding="utf-8")
            )
            expected = [
                {"id": member["id"], "version": member["version"]}
                for member in registry[member_key]
            ]
            self.assertEqual(expected, sources[relative_path]["objects"])

    def test_generated_artifacts_are_current(self):
        result = subprocess.run(
            [sys.executable, "schemas/generate.py", "--check"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

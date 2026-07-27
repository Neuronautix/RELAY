from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from relay.cli import main
from relay.package_validation import build_manifest, verify_package
from relay.profile_diff import compare_profiles


class RelayCliTest(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_repository_validation_emits_machine_readable_report(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main(
                [
                    "validate-repository",
                    str(self.root),
                    "--format",
                    "json",
                ]
            )

        report = json.loads(output.getvalue())
        self.assertEqual(0, status)
        self.assertEqual("pass", report["outcome"])
        self.assertEqual("relay.repository-validation", report["report_type"])

    def test_package_verification_detects_tampering(self):
        source = self.root / "examples" / "draft" / "minimal-ro-crate"
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "crate"
            shutil.copytree(source, package)
            metadata = package / "metadata" / "relay-core.json"
            metadata.write_text("{}\n", encoding="utf-8")

            report = verify_package(package)

        self.assertEqual("fail", report["outcome"])
        codes = {item["code"] for item in report["diagnostics"]}
        self.assertIn("RELAY-PACKAGE-SIZE", codes)
        self.assertIn("RELAY-PACKAGE-DIGEST", codes)

    def test_profile_diff_marks_new_required_term_as_breaking(self):
        source = self.root / "profiles" / "core-exchange" / "profile.yaml"
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "before.yaml"
            after = Path(directory) / "after.yaml"
            shutil.copyfile(source, before)
            profile = yaml.safe_load(source.read_text(encoding="utf-8"))
            term = "relay.term.note"
            profile["requirements"]["optional"].remove(term)
            profile["requirements"]["required"].append(term)
            profile["version"] = "0.2.0"
            after.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

            report = compare_profiles(before, after)

        self.assertEqual("breaking", report["compatibility"])
        change = next(item for item in report["changes"] if item["identifier"] == term)
        self.assertEqual("required", change["after"])
        self.assertIn("every conforming exchange", change["migration"])

    def test_manifest_builder_creates_verifiable_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            crate = Path(directory) / "crate"
            payload = crate / "data" / "result.csv"
            payload.parent.mkdir(parents=True)
            payload.write_text("value\n42\n", encoding="utf-8")

            manifest = build_manifest(
                crate,
                [Path("data/result.csv")],
                "urn:uuid:22222222-2222-4222-8222-222222222222",
            )
            report = verify_package(crate)

        self.assertEqual("relay-package-manifest.json", manifest.name)
        self.assertEqual("pass", report["outcome"])

    def test_invalid_profile_returns_cli_error_status(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.yaml"
            invalid.write_text("object_type: domain\n", encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                status = main(["profile-diff", str(invalid), str(invalid)])

        self.assertEqual(2, status)
        self.assertIn("is not a RELAY Profile descriptor", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

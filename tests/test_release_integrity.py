from __future__ import annotations

import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import yaml

from scripts.validate_release import build_lock, validate_release

ROOT = Path(__file__).resolve().parents[1]


class ReleaseIntegrityTests(unittest.TestCase):
    def test_checked_in_lock_is_current(self) -> None:
        self.assertEqual(validate_release(ROOT), [])

    def test_lock_has_one_pin_for_every_canonical_object(self) -> None:
        lock = build_lock(ROOT)
        identifiers = [item["id"] for item in lock["objects"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(
            {item["object_type"] for item in lock["objects"]},
            {"term", "domain", "profile", "package", "mapping", "rule"},
        )

    def test_missing_pin_is_reported(self) -> None:
        with self._repository_copy() as root:
            lock_path = root / "relay.lock.yaml"
            lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
            removed = lock["objects"].pop()
            lock_path.write_text(
                yaml.safe_dump(lock, sort_keys=False),
                encoding="utf-8",
                newline="\n",
            )
            messages = [problem.message for problem in validate_release(root)]
            self.assertIn(f"missing object pins: {removed['id']}", messages)

    def test_descriptor_checksum_drift_is_reported(self) -> None:
        with self._repository_copy() as root:
            path = root / "domains" / "core" / "domain.yaml"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
                newline="\n",
            )
            messages = [problem.message for problem in validate_release(root)]
            self.assertIn("source paths or SHA-256 digests are stale", messages)

    def test_lf_and_crlf_worktrees_have_identical_integrity(self) -> None:
        with self._repository_copy() as root:
            lock = yaml.safe_load((root / "relay.lock.yaml").read_text(encoding="utf-8"))
            paths = [source["path"] for source in lock["sources"]]
            paths.extend(["namespace.yaml", "release.yaml"])
            for relative_path in paths:
                path = root / relative_path
                path.write_text(
                    path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                    newline="\r\n",
                )
            self.assertEqual(validate_release(root), [])

    def test_pinned_version_drift_is_reported(self) -> None:
        with self._repository_copy() as root:
            lock_path = root / "relay.lock.yaml"
            lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
            lock["objects"][0]["version"] = "9.9.9"
            changed_id = lock["objects"][0]["id"]
            lock_path.write_text(
                yaml.safe_dump(lock, sort_keys=False),
                encoding="utf-8",
                newline="\n",
            )
            messages = [problem.message for problem in validate_release(root)]
            self.assertIn(f"stale object pins: {changed_id}", messages)

    def test_namespace_drift_is_reported(self) -> None:
        with self._repository_copy() as root:
            namespace_path = root / "namespace.yaml"
            namespace = yaml.safe_load(namespace_path.read_text(encoding="utf-8"))
            namespace["namespace"]["canonical_base_uri"] = "http://example.test/"
            namespace_path.write_text(
                yaml.safe_dump(namespace, sort_keys=False),
                encoding="utf-8",
                newline="\n",
            )
            messages = [problem.message for problem in validate_release(root)]
            self.assertIn(
                "canonical_base_uri must be an absolute HTTPS URI ending in '/'",
                messages,
            )
            self.assertIn("namespace snapshot is stale", messages)

    def test_lock_generation_is_deterministic(self) -> None:
        self.assertEqual(build_lock(ROOT), build_lock(ROOT))

    @contextmanager
    def _repository_copy(self) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for source in ("domains", "profiles", "packages", "mappings", "terms", "rules"):
                shutil.copytree(ROOT / source, target / source)
            for filename in ("namespace.yaml", "release.yaml", "relay.lock.yaml"):
                shutil.copy2(ROOT / filename, target / filename)
            yield target


if __name__ == "__main__":
    unittest.main()

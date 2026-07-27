#!/usr/bin/env python3
"""Build or validate the RELAY release lock and namespace configuration."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import yaml

SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
CANONICAL_PATHS = (
    ("domains", "domain.yaml", "domain"),
    ("profiles", "profile.yaml", "profile"),
    ("packages", "package.yaml", "package"),
    ("mappings", "mapping.yaml", "mapping"),
)
LOCK_NAME = "relay.lock.yaml"
NAMESPACE_NAME = "namespace.yaml"
RELEASE_NAME = "release.yaml"
ALLOWED_RELEASE_MATURITY = {
    "development",
    "proposal",
    "experimental",
    "candidate",
    "stable",
}


class UniqueKeySafeLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key: {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class ReleaseProblem:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)


def _source_digest(path: Path) -> str:
    # Canonical descriptors are Git text files with eol=lf. Normalizing before
    # hashing keeps a lock generated in an existing CRLF worktree identical to
    # one validated from a clean Linux checkout.
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _relative_source(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_source_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and "\\" not in value
        and ".." not in path.parts
        and path.as_posix() == value
    )


def _object_slug(object_type: str, object_id: str) -> str:
    if object_type == "rule":
        return object_id.lower()
    prefix = f"relay.{object_type}."
    if not object_id.startswith(prefix):
        raise ValueError(f"{object_id!r} does not match object type {object_type!r}")
    return object_id.removeprefix(prefix)


def _namespace(root: Path) -> dict[str, Any]:
    value = _load_yaml(root / NAMESPACE_NAME)
    if not isinstance(value, dict):
        raise ValueError("namespace document root must be a mapping")
    return value


def _release_configuration(root: Path) -> dict[str, Any]:
    value = _load_yaml(root / RELEASE_NAME)
    if not isinstance(value, dict):
        raise ValueError("release.yaml document root must be a mapping")
    if value.get("schema_version") != 1:
        raise ValueError("release.yaml schema_version must be 1")
    if value.get("id") != "relay.release.repository":
        raise ValueError("release.yaml id must be 'relay.release.repository'")
    version = value.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ValueError("release.yaml version must use semantic versioning")
    if value.get("maturity") not in ALLOWED_RELEASE_MATURITY:
        raise ValueError("release.yaml maturity is invalid")
    if value.get("namespace_configuration") != NAMESPACE_NAME:
        raise ValueError(f"release.yaml namespace_configuration must be {NAMESPACE_NAME}")
    return value


def _canonical_uri(
    namespace: dict[str, Any],
    object_type: str,
    object_id: str,
    version: str,
) -> str:
    namespace_data = namespace["namespace"]
    identifiers = namespace["identifiers"]
    return identifiers["versioned_uri_template"].format(
        base_uri=namespace_data["canonical_base_uri"],
        object_type=identifiers["object_type_segments"][object_type],
        slug=_object_slug(object_type, object_id),
        version=version,
    )


def _lock_entry(
    namespace: dict[str, Any],
    object_type: str,
    item: dict[str, Any],
    source: str,
) -> dict[str, str]:
    object_id = item.get("id")
    version = item.get("version")
    if not isinstance(object_id, str) or not isinstance(version, str):
        raise ValueError(f"{source} has an {object_type} without a string id and version")
    if not SEMVER.fullmatch(version):
        raise ValueError(f"{source} has a non-semantic {object_type} version: {version}")
    return {
        "id": object_id,
        "object_type": object_type,
        "version": version,
        "canonical_uri": _canonical_uri(namespace, object_type, object_id, version),
        "source": source,
    }


def _canonical_objects(root: Path, namespace: dict[str, Any]) -> list[dict[str, str]]:
    objects: list[dict[str, str]] = []

    for registry_name, list_key, object_type in (
        ("terms/registry.yaml", "terms", "term"),
        ("rules/registry.yaml", "rules", "rule"),
    ):
        document = _load_yaml(root / registry_name)
        if not isinstance(document, dict) or not isinstance(document.get(list_key), list):
            raise ValueError(f"{registry_name} must contain a {list_key} list")
        for item in document[list_key]:
            if not isinstance(item, dict):
                raise ValueError(f"{registry_name} contains a non-mapping {object_type}")
            objects.append(_lock_entry(namespace, object_type, item, registry_name))

    for folder, filename, object_type in CANONICAL_PATHS:
        for path in sorted((root / folder).rglob(filename)):
            if "_template" in path.parts:
                continue
            document = _load_yaml(path)
            if not isinstance(document, dict):
                raise ValueError(f"{_relative_source(root, path)} root must be a mapping")
            objects.append(
                _lock_entry(
                    namespace,
                    object_type,
                    document,
                    _relative_source(root, path),
                )
            )

    identifiers = [item["id"] for item in objects]
    duplicates = sorted(
        object_id for object_id in set(identifiers) if identifiers.count(object_id) > 1
    )
    if duplicates:
        raise ValueError(f"duplicate canonical object identifiers: {', '.join(duplicates)}")
    return sorted(objects, key=lambda item: item["id"])


def build_lock(root: Path) -> dict[str, Any]:
    """Build a deterministic release lock from canonical repository sources."""
    namespace = _namespace(root)
    release = _release_configuration(root)
    version = release["version"]

    objects = _canonical_objects(root, namespace)
    source_paths = sorted({item["source"] for item in objects})
    sources = [
        {
            "path": source,
            "sha256": _source_digest(root / PurePosixPath(source)),
        }
        for source in source_paths
    ]
    return {
        "lock_version": 1,
        "release": {
            "configuration": RELEASE_NAME,
            "configuration_sha256": _source_digest(root / RELEASE_NAME),
            "id": release["id"],
            "version": version,
            "maturity": release["maturity"],
        },
        "namespace": {
            "configuration": NAMESPACE_NAME,
            "configuration_sha256": _source_digest(root / NAMESPACE_NAME),
            "canonical_base_uri": namespace["namespace"]["canonical_base_uri"],
            "status": namespace["namespace"]["status"],
        },
        "sources": sources,
        "objects": objects,
    }


def _validate_namespace(root: Path, problems: list[ReleaseProblem]) -> dict[str, Any] | None:
    path = root / NAMESPACE_NAME
    try:
        document = _namespace(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        problems.append(ReleaseProblem(path, f"invalid namespace configuration: {exc}"))
        return None

    namespace = document.get("namespace")
    identifiers = document.get("identifiers")
    compatibility = document.get("compatibility")
    if document.get("schema_version") != 1:
        problems.append(ReleaseProblem(path, "schema_version must be 1"))
    if not isinstance(namespace, dict):
        problems.append(ReleaseProblem(path, "namespace must be a mapping"))
        return None
    base_uri = namespace.get("canonical_base_uri")
    parsed = urlparse(base_uri) if isinstance(base_uri, str) else None
    if parsed is None or parsed.scheme != "https" or not parsed.netloc or not base_uri.endswith("/"):
        problems.append(
            ReleaseProblem(path, "canonical_base_uri must be an absolute HTTPS URI ending in '/'")
        )
    if namespace.get("status") not in {"proposed", "active", "deprecated"}:
        problems.append(ReleaseProblem(path, "namespace status is invalid"))
    if not isinstance(identifiers, dict):
        problems.append(ReleaseProblem(path, "identifiers must be a mapping"))
        return document
    expected_types = {"term", "domain", "profile", "package", "mapping", "rule"}
    segments = identifiers.get("object_type_segments")
    if not isinstance(segments, dict) or set(segments) != expected_types:
        problems.append(
            ReleaseProblem(path, "object_type_segments must define all six canonical object types")
        )
    elif len(set(segments.values())) != len(segments):
        problems.append(ReleaseProblem(path, "object_type_segments values must be unique"))
    versioned = identifiers.get("versioned_uri_template")
    required_fields = {"{base_uri}", "{object_type}", "{slug}", "{version}"}
    if not isinstance(versioned, str) or not all(field in versioned for field in required_fields):
        problems.append(
            ReleaseProblem(path, "versioned_uri_template is missing a required placeholder")
        )
    if (
        not isinstance(compatibility, dict)
        or compatibility.get("legacy_compact_ids_remain_canonical") is not True
        or compatibility.get("compact_ids_resolve_through") != LOCK_NAME
    ):
        problems.append(
            ReleaseProblem(path, "compatibility must preserve compact IDs and resolve through the lock")
        )
    return document


def validate_release(root: Path) -> list[ReleaseProblem]:
    """Validate namespace configuration and the checked-in release lock."""
    problems: list[ReleaseProblem] = []
    namespace = _validate_namespace(root, problems)
    lock_path = root / LOCK_NAME
    try:
        actual = _load_yaml(lock_path)
    except (OSError, yaml.YAMLError) as exc:
        problems.append(ReleaseProblem(lock_path, f"invalid release lock: {exc}"))
        return problems
    if not isinstance(actual, dict):
        problems.append(ReleaseProblem(lock_path, "release lock root must be a mapping"))
        return problems
    if namespace is None:
        return problems

    try:
        expected = build_lock(root)
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        problems.append(ReleaseProblem(lock_path, f"cannot build expected release lock: {exc}"))
        return problems

    release = actual.get("release")
    release_config = _release_configuration(root)
    if not isinstance(release, dict) or not SEMVER.fullmatch(str(release.get("version", ""))):
        problems.append(ReleaseProblem(lock_path, "release.version must be semantic versioning"))
    elif release.get("version") != release_config.get("version"):
        problems.append(
            ReleaseProblem(lock_path, "release.version must match release.yaml version")
        )

    sources = actual.get("sources")
    if isinstance(sources, list):
        seen_sources: set[str] = set()
        for source in sources:
            if not isinstance(source, dict) or not _safe_source_path(source.get("path")):
                problems.append(ReleaseProblem(lock_path, f"unsafe source path in lock: {source!r}"))
                continue
            source_path = source["path"]
            if source_path in seen_sources:
                problems.append(ReleaseProblem(lock_path, f"duplicate source in lock: {source_path}"))
            seen_sources.add(source_path)
            digest = source.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                problems.append(
                    ReleaseProblem(lock_path, f"invalid SHA-256 for source: {source_path}")
                )
    else:
        problems.append(ReleaseProblem(lock_path, "sources must be a list"))

    actual_items = actual.get("objects")
    if isinstance(actual_items, list):
        object_ids = [
            item.get("id")
            for item in actual_items
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        duplicate_ids = sorted(
            object_id for object_id in set(object_ids) if object_ids.count(object_id) > 1
        )
        if duplicate_ids:
            problems.append(
                ReleaseProblem(lock_path, f"duplicate object pins: {', '.join(duplicate_ids)}")
            )
    else:
        problems.append(ReleaseProblem(lock_path, "objects must be a list"))

    if actual != expected:
        expected_objects = {item["id"]: item for item in expected["objects"]}
        actual_items = actual.get("objects", [])
        actual_objects = (
            {item.get("id"): item for item in actual_items if isinstance(item, dict)}
            if isinstance(actual_items, list)
            else {}
        )
        missing = sorted(set(expected_objects) - set(actual_objects))
        extra = sorted(set(actual_objects) - set(expected_objects))
        changed = sorted(
            object_id
            for object_id in set(expected_objects) & set(actual_objects)
            if expected_objects[object_id] != actual_objects[object_id]
        )
        if missing:
            problems.append(ReleaseProblem(lock_path, f"missing object pins: {', '.join(missing)}"))
        if extra:
            problems.append(ReleaseProblem(lock_path, f"unknown object pins: {', '.join(extra)}"))
        if changed:
            problems.append(ReleaseProblem(lock_path, f"stale object pins: {', '.join(changed)}"))
        if actual.get("sources") != expected["sources"]:
            problems.append(ReleaseProblem(lock_path, "source paths or SHA-256 digests are stale"))
        if actual.get("namespace") != expected["namespace"]:
            problems.append(ReleaseProblem(lock_path, "namespace snapshot is stale"))
        if actual.get("release") != expected["release"]:
            problems.append(ReleaseProblem(lock_path, "release metadata is stale"))
        if actual.get("lock_version") != expected["lock_version"]:
            problems.append(ReleaseProblem(lock_path, "lock_version is stale or unsupported"))
        if not problems:
            problems.append(ReleaseProblem(lock_path, "release lock differs from generated form"))
    return problems


def write_lock(root: Path) -> None:
    """Write the deterministic lock. Intended for an explicit maintainer workflow."""
    lock = build_lock(root)
    rendered = yaml.safe_dump(lock, sort_keys=False, allow_unicode=True, width=100)
    (root / LOCK_NAME).write_text(rendered, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="rebuild relay.lock.yaml before validating it",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.write:
        try:
            write_lock(root)
        except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            print(f"release lock generation failed: {exc}", file=sys.stderr)
            return 1
    problems = validate_release(root)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"release integrity failed with {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("release namespace and lock are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

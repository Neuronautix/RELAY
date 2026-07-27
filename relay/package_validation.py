"""Integrity validation for RELAY package manifests."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
import json
import mimetypes
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackageDiagnostic:
    code: str
    path: str
    message: str
    remediation: str


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_object,
    )


def verify_manifest(
    manifest_path: Path,
    manifest: Any | None = None,
) -> list[PackageDiagnostic]:
    manifest_path = manifest_path.resolve()
    crate_root = manifest_path.parents[1]
    diagnostics: list[PackageDiagnostic] = []

    def add(code: str, path: str, message: str, remediation: str) -> None:
        diagnostics.append(PackageDiagnostic(code, path, message, remediation))

    if manifest is None:
        try:
            manifest = load_strict_json(manifest_path)
        except Exception as exc:
            add(
                "RELAY-PACKAGE-JSON",
                str(manifest_path),
                f"invalid package manifest JSON: {exc}",
                "Correct the manifest JSON before checking its entries.",
            )
            return diagnostics
    if not isinstance(manifest, dict):
        add(
            "RELAY-PACKAGE-SHAPE",
            str(manifest_path),
            "package manifest root must be a JSON object",
            "Represent the manifest as an object with algorithm and entries fields.",
        )
        return diagnostics
    if manifest.get("algorithm") != "SHA-256":
        add(
            "RELAY-PACKAGE-ALGORITHM",
            str(manifest_path),
            "package manifest algorithm must be 'SHA-256'",
            "Set algorithm to SHA-256 and regenerate every digest.",
        )
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        add(
            "RELAY-PACKAGE-SHAPE",
            str(manifest_path),
            "package manifest entries must be a list",
            "Use one manifest entry object per immutable file.",
        )
        return diagnostics

    seen_paths: set[str] = set()
    for index, entry in enumerate(entries):
        entry_location = f"entries[{index}]"
        if not isinstance(entry, dict):
            add(
                "RELAY-PACKAGE-SHAPE",
                entry_location,
                f"package manifest entry must be an object: {entry!r}",
                "Replace the value with a manifest entry object.",
            )
            continue
        required = [
            "path",
            "content_role",
            "media_type",
            "byte_size",
            "sha256",
            "related_relay_entity",
        ]
        for key in required:
            if key not in entry:
                add(
                    "RELAY-PACKAGE-MISSING-FIELD",
                    entry_location,
                    f"package manifest entry missing key: {key}",
                    f"Add {key} to this manifest entry.",
                )
        relative = entry.get("path")
        if not isinstance(relative, str):
            add(
                "RELAY-PACKAGE-PATH",
                entry_location,
                f"package manifest path must be a string: {relative!r}",
                "Use a POSIX-style path relative to the crate root.",
            )
            continue
        if relative in seen_paths:
            add(
                "RELAY-PACKAGE-DUPLICATE",
                relative,
                f"duplicate package manifest path: {relative}",
                "Keep exactly one entry for each package file.",
            )
            continue
        seen_paths.add(relative)
        target = (crate_root / relative).resolve()
        try:
            target.relative_to(crate_root)
        except ValueError:
            add(
                "RELAY-PACKAGE-PATH",
                relative,
                f"package manifest path escapes crate root: {relative}",
                "Use a relative path that remains inside the crate root.",
            )
            continue
        if not target.is_file():
            add(
                "RELAY-PACKAGE-MISSING-FILE",
                relative,
                f"package manifest file does not exist: {relative}",
                "Add the file or remove the stale manifest entry.",
            )
            continue
        content = target.read_bytes()
        if entry.get("byte_size") != len(content):
            add(
                "RELAY-PACKAGE-SIZE",
                relative,
                f"package manifest byte_size mismatch for {relative}: "
                f"expected {entry.get('byte_size')!r}, got {len(content)}",
                "Regenerate the manifest after finalizing the file.",
            )
        digest = hashlib.sha256(content).hexdigest()
        if entry.get("sha256") != digest:
            add(
                "RELAY-PACKAGE-DIGEST",
                relative,
                f"package manifest sha256 mismatch for {relative}: "
                f"expected {entry.get('sha256')!r}, got {digest}",
                "Regenerate the manifest after finalizing the file.",
            )
    return diagnostics


def verify_package(path: Path) -> dict[str, Any]:
    path = path.resolve()
    manifest_path = (
        path
        if path.is_file()
        else path / "validation" / "relay-package-manifest.json"
    )
    if not manifest_path.is_file():
        diagnostics = [
            PackageDiagnostic(
                "RELAY-PACKAGE-MISSING-MANIFEST",
                str(manifest_path),
                "RELAY package manifest was not found",
                "Add validation/relay-package-manifest.json or pass its exact path.",
            )
        ]
    else:
        diagnostics = verify_manifest(manifest_path)
    return {
        "report_type": "relay.package-validation",
        "report_version": "1.0",
        "package": str(path),
        "manifest": str(manifest_path),
        "outcome": "fail" if diagnostics else "pass",
        "summary": {"problems": len(diagnostics)},
        "diagnostics": [asdict(item) for item in diagnostics],
    }


def build_manifest(
    crate_root: Path,
    files: list[Path],
    related_entity: str,
    output: Path | None = None,
    content_role: str = "payload",
    force: bool = False,
) -> Path:
    crate_root = crate_root.resolve()
    if not crate_root.is_dir():
        raise ValueError(f"crate root is not a directory: {crate_root}")
    output = (
        output.resolve()
        if output is not None
        else crate_root / "validation" / "relay-package-manifest.json"
    )
    try:
        output.relative_to(crate_root)
    except ValueError as exc:
        raise ValueError("manifest output must remain inside the crate root") from exc
    if output.exists() and not force:
        raise ValueError(f"manifest already exists; pass --force to replace it: {output}")

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for supplied in files:
        target = supplied if supplied.is_absolute() else crate_root / supplied
        target = target.resolve()
        try:
            relative = target.relative_to(crate_root)
        except ValueError as exc:
            raise ValueError(f"payload file escapes crate root: {supplied}") from exc
        if target == output:
            raise ValueError("the manifest cannot inventory itself")
        if not target.is_file():
            raise ValueError(f"payload file does not exist: {supplied}")
        relative_posix = relative.as_posix()
        if relative_posix in seen:
            raise ValueError(f"payload file was selected more than once: {relative_posix}")
        seen.add(relative_posix)
        content = target.read_bytes()
        media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        entries.append(
            {
                "path": relative_posix,
                "content_role": content_role,
                "media_type": media_type,
                "byte_size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "related_relay_entity": related_entity,
            }
        )

    manifest = {
        "algorithm": "SHA-256",
        "entries": sorted(entries, key=lambda entry: entry["path"]),
        "note": (
            "Generated by relay build-manifest. The manifest and "
            "ro-crate-metadata.json are package control files."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output

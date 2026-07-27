"""Semantic requiredness diff and migration planning for RELAY Profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from relay.validation import UniqueKeySafeLoader


CATEGORIES = ["required", "recommended", "optional", "conditional", "excluded"]


@dataclass(frozen=True)
class ProfileChange:
    severity: str
    subject: str
    identifier: str
    before: str | None
    after: str | None
    migration: str


def _load_profile(path: Path) -> dict[str, Any]:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
    if not isinstance(value, dict) or value.get("object_type") != "profile":
        raise ValueError(f"{path} is not a RELAY Profile descriptor")
    return value


def _classifications(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    result: dict[str, str] = {}
    for category in CATEGORIES:
        entries = value.get(category, [])
        if not isinstance(entries, list):
            raise ValueError(f"{label}.{category} must be a list")
        if category == "conditional":
            for condition in entries:
                if not isinstance(condition, dict):
                    raise ValueError(f"{label}.conditional entries must be mappings")
                required = condition.get("require", [])
                if not isinstance(required, list):
                    raise ValueError(f"{label}.conditional.require must be a list")
                for identifier in required:
                    if isinstance(identifier, str):
                        if identifier in result:
                            raise ValueError(
                                f"{identifier} appears in multiple {label} categories"
                            )
                        result[identifier] = category
        else:
            for identifier in entries:
                if isinstance(identifier, str):
                    if identifier in result:
                        raise ValueError(
                            f"{identifier} appears in multiple {label} categories"
                        )
                    result[identifier] = category
    return result


def _identifier_set(value: Any, label: str) -> set[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of identifiers")
    return set(value)


def _classification_change(
    subject: str,
    identifier: str,
    before: str | None,
    after: str | None,
) -> ProfileChange:
    severity = "info"
    if after in {"required", "excluded"} and before != after:
        severity = "breaking"
    elif before == "required" and after != "required":
        severity = "warning"
    elif before is not None and after is None:
        severity = "warning"
    elif before in {"optional", "recommended"} and after == "conditional":
        severity = "warning"

    if before is None:
        migration = f"Add handling for the newly selected {subject.lower()}."
    elif after is None:
        migration = f"Remove assumptions that this Profile selects the {subject.lower()}."
    elif after == "required":
        migration = "Populate this value for every conforming exchange."
    elif after == "excluded":
        migration = "Remove this value from exchanges claiming the new Profile."
    elif after == "conditional":
        migration = "Evaluate the documented condition and populate the value when it applies."
    else:
        migration = f"Update handling from {before} to {after}."
    return ProfileChange(severity, subject, identifier, before, after, migration)


def compare_profiles(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = _load_profile(before_path)
    after = _load_profile(after_path)
    changes: list[ProfileChange] = []

    for subject, key in [("Term", "requirements"), ("Rule", "rule_requirements")]:
        before_items = _classifications(before.get(key, {}), key)
        after_items = _classifications(after.get(key, {}), key)
        for identifier in sorted(before_items.keys() | after_items.keys()):
            old = before_items.get(identifier)
            new = after_items.get(identifier)
            if old != new:
                changes.append(_classification_change(subject, identifier, old, new))

    before_domains = _identifier_set(before.get("domains", []), "domains")
    after_domains = _identifier_set(after.get("domains", []), "domains")
    for identifier in sorted(before_domains - after_domains):
        changes.append(
            ProfileChange(
                "breaking",
                "Domain",
                identifier,
                "selected",
                None,
                "Stop relying on semantics imported only through this Domain.",
            )
        )
    for identifier in sorted(after_domains - before_domains):
        changes.append(
            ProfileChange(
                "info",
                "Domain",
                identifier,
                None,
                "selected",
                "Review the newly imported Domain and its applicable Rules.",
            )
        )
    if before.get("package") != after.get("package"):
        changes.append(
            ProfileChange(
                "breaking",
                "Package",
                str(after.get("package")),
                str(before.get("package")),
                str(after.get("package")),
                "Migrate serialization and packaging to the newly selected Package.",
            )
        )

    breaking = sum(change.severity == "breaking" for change in changes)
    warnings = sum(change.severity == "warning" for change in changes)
    return {
        "report_type": "relay.profile-diff",
        "report_version": "1.0",
        "before": {
            "path": str(before_path.resolve()),
            "id": before.get("id"),
            "version": before.get("version"),
        },
        "after": {
            "path": str(after_path.resolve()),
            "id": after.get("id"),
            "version": after.get("version"),
        },
        "compatibility": "breaking" if breaking else "compatible",
        "summary": {
            "changes": len(changes),
            "breaking": breaking,
            "warnings": warnings,
        },
        "changes": [asdict(change) for change in changes],
    }

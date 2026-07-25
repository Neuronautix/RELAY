#!/usr/bin/env python3
"""Validate RELAY canonical repository objects and parse example JSON files."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_STATUS = {"proposal", "experimental", "candidate", "stable", "deprecated", "withdrawn"}
ALLOWED_CLASSIFICATION = {"normative", "informative"}
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
RULE_ID = re.compile(r"^RELAY-[A-Z0-9]+-[0-9]{3}$")
OBJECT_ID = re.compile(r"^relay\.(term|domain|profile|package|mapping)\.[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Problem:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_yaml(path: Path, problems: list[Problem]) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - parser detail
        problems.append(Problem(path, f"invalid YAML: {exc}"))
        return None


def require_mapping(path: Path, value: Any, problems: list[Problem]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        problems.append(Problem(path, "document root must be a mapping"))
        return None
    return value


def check_common(path: Path, obj: dict[str, Any], expected_type: str, problems: list[Problem]) -> None:
    required = ["object_type", "id", "title", "version", "status", "classification"]
    for key in required:
        if key not in obj:
            problems.append(Problem(path, f"missing required key: {key}"))
    if obj.get("object_type") != expected_type:
        problems.append(Problem(path, f"object_type must be {expected_type!r}"))
    oid = obj.get("id")
    if "id" in obj and not isinstance(oid, str):
        problems.append(Problem(path, f"object identifier must be a string: {oid!r}"))
    elif isinstance(oid, str) and not OBJECT_ID.match(oid):
        problems.append(Problem(path, f"invalid object identifier: {oid}"))
    version = obj.get("version")
    if "version" in obj and not isinstance(version, str):
        problems.append(Problem(path, f"version must be a string: {version!r}"))
    elif isinstance(version, str) and not SEMVER.match(version):
        problems.append(Problem(path, f"version is not semantic versioning: {version}"))
    if obj.get("status") not in ALLOWED_STATUS:
        problems.append(Problem(path, f"invalid status: {obj.get('status')!r}"))
    if obj.get("classification") not in ALLOWED_CLASSIFICATION:
        problems.append(Problem(path, f"invalid classification: {obj.get('classification')!r}"))


def validate_repository(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    objects: dict[str, tuple[Path, dict[str, Any]]] = {}
    term_ids: set[str] = set()
    rule_ids: set[str] = set()

    def register(path: Path, oid: str, obj: dict[str, Any]) -> None:
        if oid in objects:
            problems.append(Problem(path, f"duplicate identifier {oid}; first declared in {objects[oid][0]}"))
        else:
            objects[oid] = (path, obj)

    # Term registry and individual Term objects inside it.
    term_path = root / "terms" / "registry.yaml"
    term_doc = require_mapping(term_path, load_yaml(term_path, problems), problems)
    if term_doc:
        if term_doc.get("object_type") != "term_registry":
            problems.append(Problem(term_path, "object_type must be 'term_registry'"))
        for key in ["id", "title", "version", "status", "classification", "terms"]:
            if key not in term_doc:
                problems.append(Problem(term_path, f"missing required key: {key}"))
        registry_version = term_doc.get("version")
        if "version" in term_doc and not isinstance(registry_version, str):
            problems.append(Problem(term_path, f"registry version must be a string: {registry_version!r}"))
        elif isinstance(registry_version, str) and not SEMVER.match(registry_version):
            problems.append(Problem(term_path, "registry version is not semantic versioning"))
        for term in term_doc.get("terms", []) or []:
            if not isinstance(term, dict):
                problems.append(Problem(term_path, "each term must be a mapping"))
                continue
            for key in ["id", "label", "version", "kind", "domain", "status", "definition"]:
                if key not in term:
                    problems.append(Problem(term_path, f"term missing required key {key}: {term}"))
            tid = term.get("id")
            if "id" in term and not isinstance(tid, str):
                problems.append(Problem(term_path, f"Term identifier must be a string: {tid!r}"))
            elif isinstance(tid, str):
                if not tid.startswith("relay.term.") or not OBJECT_ID.match(tid):
                    problems.append(Problem(term_path, f"invalid Term identifier: {tid}"))
                if tid in term_ids:
                    problems.append(Problem(term_path, f"duplicate Term identifier: {tid}"))
                term_ids.add(tid)
                register(term_path, tid, term)
            term_version = term.get("version")
            if "version" in term and not isinstance(term_version, str):
                problems.append(Problem(term_path, f"Term version must be a string for {tid}: {term_version!r}"))
            elif isinstance(term_version, str) and not SEMVER.match(term_version):
                problems.append(Problem(term_path, f"invalid Term version for {tid}: {term_version}"))
            if term.get("status") not in ALLOWED_STATUS:
                problems.append(Problem(term_path, f"invalid Term status for {tid}: {term.get('status')!r}"))

    # Conformance Rule registry and individual Rule objects inside it.
    rule_path = root / "rules" / "registry.yaml"
    rule_doc = require_mapping(rule_path, load_yaml(rule_path, problems), problems)
    if rule_doc:
        if rule_doc.get("object_type") != "conformance_rule_registry":
            problems.append(Problem(rule_path, "object_type must be 'conformance_rule_registry'"))
        for rule in rule_doc.get("rules", []) or []:
            if not isinstance(rule, dict):
                problems.append(Problem(rule_path, "each rule must be a mapping"))
                continue
            for key in ["id", "title", "version", "status", "scope", "level", "statement", "rationale", "testability"]:
                if key not in rule:
                    problems.append(Problem(rule_path, f"rule missing required key {key}: {rule}"))
            rid = rule.get("id")
            if isinstance(rid, str):
                if not RULE_ID.match(rid):
                    problems.append(Problem(rule_path, f"invalid Rule identifier: {rid}"))
                if rid in rule_ids:
                    problems.append(Problem(rule_path, f"duplicate Rule identifier: {rid}"))
                rule_ids.add(rid)
            if rule.get("version") and not SEMVER.match(str(rule["version"])):
                problems.append(Problem(rule_path, f"invalid Rule version for {rid}"))
            if rule.get("status") not in ALLOWED_STATUS:
                problems.append(Problem(rule_path, f"invalid Rule status for {rid}"))

    path_specs = [
        ("domains", "domain.yaml", "domain"),
        ("profiles", "profile.yaml", "profile"),
        ("packages", "package.yaml", "package"),
        ("mappings", "mapping.yaml", "mapping"),
    ]
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for folder, filename, expected in path_specs:
        for path in sorted((root / folder).rglob(filename)):
            if "_template" in path.parts:
                continue
            obj = require_mapping(path, load_yaml(path, problems), problems)
            if not obj:
                continue
            check_common(path, obj, expected, problems)
            oid = obj.get("id")
            if isinstance(oid, str):
                register(path, oid, obj)
            loaded.append((path, obj))

    domain_ids = {oid for oid in objects if oid.startswith("relay.domain.")}
    profile_ids = {oid for oid in objects if oid.startswith("relay.profile.")}
    package_ids = {oid for oid in objects if oid.startswith("relay.package.")}

    # Term references, including broader/related links and owning Domains.
    if term_doc:
        for term in term_doc.get("terms", []) or []:
            if not isinstance(term, dict):
                continue
            tid = term.get("id", "<unknown>")
            domain = term.get("domain")
            if domain not in domain_ids:
                problems.append(Problem(term_path, f"Term {tid} references unknown Domain {domain}"))
            for relation in ["broader", "related"]:
                for ref in term.get(relation, []) or []:
                    if ref not in term_ids:
                        problems.append(Problem(term_path, f"Term {tid} has unknown {relation} reference {ref}"))

    domain_dependencies: dict[str, list[str]] = {}
    for path, obj in loaded:
        otype = obj.get("object_type")
        oid = obj.get("id", "<unknown>")
        if otype == "domain":
            deps = obj.get("dependencies", []) or []
            domain_dependencies[str(oid)] = list(deps)
            for ref in deps:
                if ref not in domain_ids:
                    problems.append(Problem(path, f"unknown Domain dependency: {ref}"))
            for ref in obj.get("terms", []) or []:
                if ref not in term_ids:
                    problems.append(Problem(path, f"unknown Term reference: {ref}"))
            for ref in obj.get("rules", []) or []:
                if ref not in rule_ids:
                    problems.append(Problem(path, f"unknown Rule reference: {ref}"))
        elif otype == "profile":
            for ref in obj.get("domains", []) or []:
                if ref not in domain_ids:
                    problems.append(Problem(path, f"unknown Domain reference: {ref}"))
            package = obj.get("package")
            if package is not None and package not in package_ids:
                problems.append(Problem(path, f"unknown Package reference: {package}"))
            reqs = obj.get("requirements", {}) or {}
            for category in ["required", "recommended", "optional", "excluded"]:
                for ref in reqs.get(category, []) or []:
                    if ref not in term_ids:
                        problems.append(Problem(path, f"unknown Term in {category}: {ref}"))
            for conditional in reqs.get("conditional", []) or []:
                for ref in conditional.get("require", []) or []:
                    if ref not in term_ids:
                        problems.append(Problem(path, f"unknown conditional Term: {ref}"))
            for ref in obj.get("rules", []) or []:
                if ref not in rule_ids:
                    problems.append(Problem(path, f"unknown Rule reference: {ref}"))
        elif otype == "package":
            root_entity = obj.get("root_entity")
            if root_entity not in term_ids:
                problems.append(Problem(path, f"unknown root Term: {root_entity}"))
            profile = obj.get("profile_identifier")
            if profile is not None and profile not in profile_ids:
                problems.append(Problem(path, f"unknown Profile reference: {profile}"))
            for ref in obj.get("conformance_rules", []) or []:
                if ref not in rule_ids:
                    problems.append(Problem(path, f"unknown Rule reference: {ref}"))
        elif otype == "mapping":
            for key in ["source", "target", "direction", "entries"]:
                if key not in obj:
                    problems.append(Problem(path, f"Mapping missing required key: {key}"))
            for entry in obj.get("entries", []) or []:
                for key in [
                    "source",
                    "target",
                    "relation",
                    "conditions",
                    "transformation",
                    "information_loss",
                    "cardinality_or_datatype_impact",
                    "evidence",
                    "review_status",
                    "reviewer",
                ]:
                    if key not in entry:
                        problems.append(Problem(path, f"mapping entry missing key {key}: {entry}"))

    # Domain dependency graph must be acyclic.
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dep in domain_dependencies.get(node, []):
            if state.get(dep, 0) == 0:
                visit(dep)
            elif state.get(dep) == 1:
                cycle = " -> ".join(stack[stack.index(dep):] + [dep])
                problems.append(Problem(root / "domains", f"cyclic Domain dependency: {cycle}"))
        stack.pop()
        state[node] = 2

    for node in sorted(domain_dependencies):
        if state.get(node, 0) == 0:
            visit(node)

    # All committed JSON examples must parse.
    for path in sorted((root / "examples").rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(Problem(path, f"invalid JSON: {exc}"))

    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems = validate_repository(root)
    if problems:
        print(f"RELAY repository validation failed with {len(problems)} problem(s):", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("RELAY repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

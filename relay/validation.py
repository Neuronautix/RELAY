"""Validate RELAY canonical repository objects and parse example JSON files."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from relay.package_validation import verify_manifest

ALLOWED_STATUS = {"proposal", "experimental", "candidate", "stable", "deprecated", "withdrawn"}
ALLOWED_CLASSIFICATION = {"normative", "informative"}
ALLOWED_RULE_LEVEL = {"MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY"}
ALLOWED_TESTABILITY = {"automated", "hybrid", "manual"}
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
RULE_ID = re.compile(r"^RELAY-[A-Z0-9]+-[0-9]{3}$")
OBJECT_ID = re.compile(r"^relay\.(term|domain|profile|package|mapping)\.[a-z0-9]+(?:-[a-z0-9]+)*$")


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found an unhashable key: {key!r}",
                key_node.start_mark,
            ) from exc
        if duplicate:
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
    construct_unique_mapping,
)


@dataclass
class Problem:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_yaml(path: Path, problems: list[Problem]) -> Any:
    try:
        return yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=UniqueKeySafeLoader,
        )
    except Exception as exc:  # pragma: no cover - parser detail
        problems.append(Problem(path, f"invalid YAML: {exc}"))
        return None


def require_mapping(path: Path, value: Any, problems: list[Problem]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        problems.append(Problem(path, "document root must be a mapping"))
        return None
    return value


def require_list(path: Path, value: Any, field: str, problems: list[Problem]) -> list[Any]:
    if not isinstance(value, list):
        problems.append(Problem(path, f"{field} must be a list"))
        return []
    return value


def string_list(path: Path, value: Any, field: str, problems: list[Problem]) -> list[str]:
    result: list[str] = []
    for item in require_list(path, value, field, problems):
        if not isinstance(item, str):
            problems.append(Problem(path, f"{field} entries must be strings: {item!r}"))
        else:
            result.append(item)
    return result


def check_registry_common(path: Path, obj: dict[str, Any], problems: list[Problem]) -> None:
    for key in ["id", "title", "version", "status", "classification", "maintainers"]:
        if key not in obj:
            problems.append(Problem(path, f"missing required key: {key}"))
    version = obj.get("version")
    if "version" in obj and not isinstance(version, str):
        problems.append(Problem(path, f"registry version must be a string: {version!r}"))
    elif isinstance(version, str) and not SEMVER.fullmatch(version):
        problems.append(Problem(path, f"registry version is not semantic versioning: {version}"))
    if obj.get("status") not in ALLOWED_STATUS:
        problems.append(Problem(path, f"invalid registry status: {obj.get('status')!r}"))
    if obj.get("classification") not in ALLOWED_CLASSIFICATION:
        problems.append(Problem(path, f"invalid registry classification: {obj.get('classification')!r}"))
    string_list(path, obj.get("maintainers", []), "maintainers", problems)


def check_common(path: Path, obj: dict[str, Any], expected_type: str, problems: list[Problem]) -> None:
    required = [
        "object_type",
        "id",
        "title",
        "version",
        "status",
        "classification",
        "description",
        "maintainers",
    ]
    for key in required:
        if key not in obj:
            problems.append(Problem(path, f"missing required key: {key}"))
    if obj.get("object_type") != expected_type:
        problems.append(Problem(path, f"object_type must be {expected_type!r}"))
    oid = obj.get("id")
    if "id" in obj and not isinstance(oid, str):
        problems.append(Problem(path, f"object identifier must be a string: {oid!r}"))
    elif isinstance(oid, str):
        expected_id = re.compile(
            rf"^relay\.{re.escape(expected_type)}\.[a-z0-9]+(?:-[a-z0-9]+)*$"
        )
        if not expected_id.fullmatch(oid):
            problems.append(Problem(path, f"invalid {expected_type} identifier: {oid}"))
    version = obj.get("version")
    if "version" in obj and not isinstance(version, str):
        problems.append(Problem(path, f"version must be a string: {version!r}"))
    elif isinstance(version, str) and not SEMVER.fullmatch(version):
        problems.append(Problem(path, f"version is not semantic versioning: {version}"))
    if obj.get("status") not in ALLOWED_STATUS:
        problems.append(Problem(path, f"invalid status: {obj.get('status')!r}"))
    if obj.get("classification") not in ALLOWED_CLASSIFICATION:
        problems.append(Problem(path, f"invalid classification: {obj.get('classification')!r}"))
    for key in ["title", "description"]:
        value = obj.get(key)
        if key in obj and (not isinstance(value, str) or not value.strip()):
            problems.append(Problem(path, f"{key} must be a non-empty string"))
    string_list(path, obj.get("maintainers", []), "maintainers", problems)


def validate_repository(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    objects: dict[str, tuple[Path, dict[str, Any]]] = {}
    term_ids: set[str] = set()
    rule_ids: set[str] = set()
    term_domains: dict[str, str] = {}
    rule_scopes: dict[str, list[str]] = {}

    def register(path: Path, oid: str, obj: dict[str, Any]) -> None:
        if oid in objects:
            problems.append(Problem(path, f"duplicate identifier {oid}; first declared in {objects[oid][0]}"))
        else:
            objects[oid] = (path, obj)

    # Term registry and individual Term objects inside it.
    term_path = root / "terms" / "registry.yaml"
    term_doc = require_mapping(term_path, load_yaml(term_path, problems), problems)
    if term_doc is not None:
        if term_doc.get("object_type") != "term_registry":
            problems.append(Problem(term_path, "object_type must be 'term_registry'"))
        check_registry_common(term_path, term_doc, problems)
        if "terms" not in term_doc:
            problems.append(Problem(term_path, "missing required key: terms"))
        terms = require_list(term_path, term_doc.get("terms", []), "terms", problems)
        for term in terms:
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
                if not tid.startswith("relay.term.") or not OBJECT_ID.fullmatch(tid):
                    problems.append(Problem(term_path, f"invalid Term identifier: {tid}"))
                if tid in term_ids:
                    problems.append(Problem(term_path, f"duplicate Term identifier: {tid}"))
                elif tid.startswith("relay.term.") and OBJECT_ID.fullmatch(tid):
                    term_ids.add(tid)
                register(term_path, tid, term)
            term_version = term.get("version")
            if "version" in term and not isinstance(term_version, str):
                problems.append(Problem(term_path, f"Term version must be a string for {tid}: {term_version!r}"))
            elif isinstance(term_version, str) and not SEMVER.fullmatch(term_version):
                problems.append(Problem(term_path, f"invalid Term version for {tid}: {term_version}"))
            if term.get("status") not in ALLOWED_STATUS:
                problems.append(Problem(term_path, f"invalid Term status for {tid}: {term.get('status')!r}"))
            domain = term.get("domain")
            if "domain" in term and not isinstance(domain, str):
                problems.append(Problem(term_path, f"Term domain must be a string for {tid}: {domain!r}"))
            elif isinstance(tid, str) and isinstance(domain, str):
                term_domains[tid] = domain
            for relation in ["broader", "related"]:
                if relation in term:
                    string_list(
                        term_path,
                        term[relation],
                        f"Term {tid} {relation}",
                        problems,
                    )

    # Conformance Rule registry and individual Rule objects inside it.
    rule_path = root / "rules" / "registry.yaml"
    rule_doc = require_mapping(rule_path, load_yaml(rule_path, problems), problems)
    if rule_doc is not None:
        if rule_doc.get("object_type") != "conformance_rule_registry":
            problems.append(Problem(rule_path, "object_type must be 'conformance_rule_registry'"))
        check_registry_common(rule_path, rule_doc, problems)
        if "rules" not in rule_doc:
            problems.append(Problem(rule_path, "missing required key: rules"))
        rules = require_list(rule_path, rule_doc.get("rules", []), "rules", problems)
        for rule in rules:
            if not isinstance(rule, dict):
                problems.append(Problem(rule_path, "each rule must be a mapping"))
                continue
            for key in ["id", "title", "version", "status", "scope", "level", "statement", "rationale", "testability"]:
                if key not in rule:
                    problems.append(Problem(rule_path, f"rule missing required key {key}: {rule}"))
            rid = rule.get("id")
            if "id" in rule and not isinstance(rid, str):
                problems.append(Problem(rule_path, f"Rule identifier must be a string: {rid!r}"))
            elif isinstance(rid, str):
                if not RULE_ID.match(rid):
                    problems.append(Problem(rule_path, f"invalid Rule identifier: {rid}"))
                if rid in rule_ids:
                    problems.append(Problem(rule_path, f"duplicate Rule identifier: {rid}"))
                elif RULE_ID.fullmatch(rid):
                    rule_ids.add(rid)
            rule_version = rule.get("version")
            if "version" in rule and not isinstance(rule_version, str):
                problems.append(Problem(rule_path, f"Rule version must be a string for {rid}: {rule_version!r}"))
            elif isinstance(rule_version, str) and not SEMVER.fullmatch(rule_version):
                problems.append(Problem(rule_path, f"invalid Rule version for {rid}: {rule_version}"))
            if rule.get("status") not in ALLOWED_STATUS:
                problems.append(Problem(rule_path, f"invalid Rule status for {rid}"))
            if rule.get("level") not in ALLOWED_RULE_LEVEL:
                problems.append(Problem(rule_path, f"invalid Rule level for {rid}: {rule.get('level')!r}"))
            if rule.get("testability") not in ALLOWED_TESTABILITY:
                problems.append(
                    Problem(rule_path, f"invalid Rule testability for {rid}: {rule.get('testability')!r}")
                )
            scopes = string_list(
                rule_path,
                rule.get("scope", []),
                f"Rule {rid} scope",
                problems,
            )
            if isinstance(rid, str):
                rule_scopes[rid] = scopes

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
            if obj is None:
                continue
            check_common(path, obj, expected, problems)
            oid = obj.get("id")
            if isinstance(oid, str):
                register(path, oid, obj)
            loaded.append((path, obj))

    def valid_ids(expected_type: str) -> set[str]:
        pattern = re.compile(
            rf"^relay\.{re.escape(expected_type)}\.[a-z0-9]+(?:-[a-z0-9]+)*$"
        )
        return {
            oid
            for _, obj in loaded
            if obj.get("object_type") == expected_type
            and isinstance((oid := obj.get("id")), str)
            and pattern.fullmatch(oid)
        }

    domain_ids = valid_ids("domain")
    profile_ids = valid_ids("profile")
    package_ids = valid_ids("package")
    mapping_ids = valid_ids("mapping")

    # Term references, including broader/related links and owning Domains.
    if term_doc is not None:
        for term in require_list(term_path, term_doc.get("terms", []), "terms", []):
            if not isinstance(term, dict):
                continue
            tid = term.get("id", "<unknown>")
            domain = term.get("domain")
            if isinstance(domain, str) and domain not in domain_ids:
                problems.append(Problem(term_path, f"Term {tid} references unknown Domain {domain}"))
            for relation in ["broader", "related"]:
                refs = term.get(relation, [])
                if not isinstance(refs, list):
                    continue
                for ref in refs:
                    if not isinstance(ref, str):
                        continue
                    if ref not in term_ids:
                        problems.append(Problem(term_path, f"Term {tid} has unknown {relation} reference {ref}"))

    domain_dependencies: dict[str, list[str]] = {}
    for path, obj in loaded:
        otype = obj.get("object_type")
        oid = obj.get("id", "<unknown>")
        if otype == "domain":
            for key in ["dependencies", "terms", "rules", "scope"]:
                if key not in obj:
                    problems.append(Problem(path, f"Domain missing required key: {key}"))
            deps = string_list(path, obj.get("dependencies", []), "dependencies", problems)
            if isinstance(oid, str) and oid in domain_ids:
                domain_dependencies[oid] = deps
            for ref in deps:
                if ref not in domain_ids:
                    problems.append(Problem(path, f"unknown Domain dependency: {ref}"))
            domain_terms = string_list(path, obj.get("terms", []), "terms", problems)
            for ref in domain_terms:
                if ref not in term_ids:
                    problems.append(Problem(path, f"unknown Term reference: {ref}"))
                elif isinstance(oid, str) and term_domains.get(ref) != oid:
                    problems.append(
                        Problem(
                            path,
                            f"Term {ref} is owned by {term_domains.get(ref)}, not {oid}",
                        )
                    )
            for ref in string_list(path, obj.get("rules", []), "rules", problems):
                if ref not in rule_ids:
                    problems.append(Problem(path, f"unknown Rule reference: {ref}"))
        elif otype == "profile":
            for key in ["domains", "package", "requirements", "rule_requirements"]:
                if key not in obj:
                    problems.append(Problem(path, f"Profile missing required key: {key}"))
            selected_domains = string_list(path, obj.get("domains", []), "domains", problems)
            for ref in selected_domains:
                if ref not in domain_ids:
                    problems.append(Problem(path, f"unknown Domain reference: {ref}"))
            package = obj.get("package")
            if package is not None and not isinstance(package, str):
                problems.append(Problem(path, f"Package reference must be a string or null: {package!r}"))
            elif isinstance(package, str) and package not in package_ids:
                problems.append(Problem(path, f"unknown Package reference: {package}"))
            reqs = require_mapping(path, obj.get("requirements", {}), problems)
            reqs = reqs if reqs is not None else {}
            categorized_terms: dict[str, str] = {}
            for category in ["required", "recommended", "optional", "excluded"]:
                for ref in string_list(
                    path,
                    reqs.get(category, []),
                    f"requirements.{category}",
                    problems,
                ):
                    if ref not in term_ids:
                        problems.append(Problem(path, f"unknown Term in {category}: {ref}"))
                    elif term_domains.get(ref) not in selected_domains:
                        problems.append(
                            Problem(path, f"Term in {category} is outside selected Domains: {ref}")
                        )
                    if ref in categorized_terms:
                        problems.append(
                            Problem(
                                path,
                                f"Term {ref} appears in both {categorized_terms[ref]} and {category}",
                            )
                        )
                    categorized_terms[ref] = category
            conditionals = require_list(
                path,
                reqs.get("conditional", []),
                "requirements.conditional",
                problems,
            )
            for conditional in conditionals:
                conditional_obj = require_mapping(path, conditional, problems)
                if conditional_obj is None:
                    continue
                for ref in string_list(
                    path,
                    conditional_obj.get("require", []),
                    "conditional.require",
                    problems,
                ):
                    if ref not in term_ids:
                        problems.append(Problem(path, f"unknown conditional Term: {ref}"))
                    elif term_domains.get(ref) not in selected_domains:
                        problems.append(
                            Problem(path, f"conditional Term is outside selected Domains: {ref}")
                        )
                    if ref in categorized_terms:
                        problems.append(
                            Problem(
                                path,
                                f"Term {ref} appears in both {categorized_terms[ref]} and conditional",
                            )
                        )
                    categorized_terms[ref] = "conditional"
            rule_reqs = require_mapping(path, obj.get("rule_requirements", {}), problems)
            rule_reqs = rule_reqs if rule_reqs is not None else {}
            categorized_rules: dict[str, str] = {}
            for category in ["required", "recommended", "optional", "excluded"]:
                for ref in string_list(
                    path,
                    rule_reqs.get(category, []),
                    f"rule_requirements.{category}",
                    problems,
                ):
                    if ref not in rule_ids:
                        problems.append(Problem(path, f"unknown Rule in {category}: {ref}"))
                    if ref in categorized_rules:
                        problems.append(
                            Problem(
                                path,
                                f"Rule {ref} appears in both {categorized_rules[ref]} and {category}",
                            )
                        )
                    categorized_rules[ref] = category
            rule_conditionals = require_list(
                path,
                rule_reqs.get("conditional", []),
                "rule_requirements.conditional",
                problems,
            )
            for conditional in rule_conditionals:
                conditional_obj = require_mapping(path, conditional, problems)
                if conditional_obj is None:
                    continue
                for ref in string_list(
                    path,
                    conditional_obj.get("require", []),
                    "conditional.require",
                    problems,
                ):
                    if ref not in rule_ids:
                        problems.append(Problem(path, f"unknown conditional Rule: {ref}"))
                    if ref in categorized_rules:
                        problems.append(
                            Problem(
                                path,
                                f"Rule {ref} appears in both {categorized_rules[ref]} and conditional",
                            )
                        )
                    categorized_rules[ref] = "conditional"
        elif otype == "package":
            for key in [
                "base_specification",
                "root_entity",
                "distribution_modes",
                "required_components",
                "conformance_rules",
            ]:
                if key not in obj:
                    problems.append(Problem(path, f"Package missing required key: {key}"))
            root_entity = obj.get("root_entity")
            if not isinstance(root_entity, str):
                problems.append(Problem(path, f"root Term must be a string: {root_entity!r}"))
            elif root_entity not in term_ids:
                problems.append(Problem(path, f"unknown root Term: {root_entity}"))
            profile = obj.get("profile_identifier")
            if profile is not None and not isinstance(profile, str):
                problems.append(
                    Problem(path, f"Profile reference must be a string or null: {profile!r}")
                )
            elif isinstance(profile, str) and profile not in profile_ids:
                problems.append(Problem(path, f"unknown Profile reference: {profile}"))
            string_list(path, obj.get("distribution_modes", []), "distribution_modes", problems)
            string_list(path, obj.get("required_components", []), "required_components", problems)
            for ref in string_list(
                path,
                obj.get("conformance_rules", []),
                "conformance_rules",
                problems,
            ):
                if ref not in rule_ids:
                    problems.append(Problem(path, f"unknown Rule reference: {ref}"))
        elif otype == "mapping":
            for key in ["source", "target", "direction", "entries"]:
                if key not in obj:
                    problems.append(Problem(path, f"Mapping missing required key: {key}"))
            entries = require_list(path, obj.get("entries", []), "entries", problems)
            for entry in entries:
                entry_obj = require_mapping(path, entry, problems)
                if entry_obj is None:
                    continue
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
                    if key not in entry_obj:
                        problems.append(Problem(path, f"mapping entry missing key {key}: {entry_obj}"))

    for tid, domain in term_domains.items():
        if tid not in term_ids or domain not in domain_ids:
            continue
        owning_domain = next(
            (
                obj
                for _, obj in loaded
                if obj.get("object_type") == "domain" and obj.get("id") == domain
            ),
            {},
        )
        owning_terms = owning_domain.get("terms", [])
        if not isinstance(owning_terms, list) or tid not in owning_terms:
            problems.append(
                Problem(term_path, f"Term {tid} is not listed by its owning Domain {domain}")
            )

    known_scope_ids = term_ids | domain_ids | profile_ids | package_ids | mapping_ids
    for rid, scopes in rule_scopes.items():
        for scope in scopes:
            if scope not in known_scope_ids:
                problems.append(Problem(rule_path, f"Rule {rid} has unknown scope: {scope}"))

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

    # All committed JSON examples must parse as strict JSON with unique keys.
    parsed_examples: dict[Path, Any] = {}

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON constant: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    for path in sorted((root / "examples").rglob("*.json")):
        try:
            parsed_examples[path] = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=reject_constant,
                object_pairs_hook=unique_object,
            )
        except Exception as exc:
            problems.append(Problem(path, f"invalid JSON: {exc}"))

    # Draft and normative package manifests must agree with the committed bytes.
    for path, manifest in parsed_examples.items():
        if path.name != "relay-package-manifest.json":
            continue
        for diagnostic in verify_manifest(path, manifest):
            problems.append(Problem(path, diagnostic.message))

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

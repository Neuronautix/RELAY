#!/usr/bin/env python3
"""Generate RELAY descriptor schema, JSON-LD context, and SHACL foundations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_NAME = "relay-schema-foundations"
GENERATOR_VERSION = "0.1.0"
GENERATION_DATE = "2026-07-27"
STATUS = ["proposal", "experimental", "candidate", "stable", "deprecated", "withdrawn"]
CLASSIFICATION = ["normative", "informative"]
RULE_LEVEL = ["MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY"]
TESTABILITY = ["automated", "hybrid", "manual"]
SEMVER = (
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def _load_yaml(relative_path: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative_path} must contain a mapping")
    return value


def _canonical_lf_sha256(relative_path: str) -> str:
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    canonical_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def source_metadata() -> dict[str, Any]:
    """Return the canonical descriptor versions represented by these artifacts."""
    namespace = _load_yaml("namespace.yaml")["namespace"]
    paths = [
        "terms/registry.yaml",
        *sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in (ROOT / "domains").glob("*/domain.yaml")
            if not path.parent.name.startswith("_")
        ),
        *sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in (ROOT / "profiles").glob("*/profile.yaml")
            if not path.parent.name.startswith("_")
        ),
        *sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in (ROOT / "packages").glob("*/package.yaml")
            if not path.parent.name.startswith("_")
        ),
        *sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in (ROOT / "mappings").glob("*/mapping.yaml")
            if not path.parent.name.startswith("_")
        ),
        "rules/registry.yaml",
    ]
    return {
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "generated_on": GENERATION_DATE,
        "namespace": {
            "path": "namespace.yaml",
            "canonical_base_uri": namespace["canonical_base_uri"],
            "status": namespace["status"],
        },
        "sources": [_source_entry(path) for path in paths],
    }


def _source_entry(path: str) -> dict[str, Any]:
    document = _load_yaml(path)
    entry = {
        "path": path,
        "id": document.get("id"),
        "version": document.get("version"),
        "sha256_canonical_lf": _canonical_lf_sha256(path),
    }
    member_key = {
        "term_registry": "terms",
        "conformance_rule_registry": "rules",
    }.get(document.get("object_type"))
    if member_key is not None:
        entry["objects"] = [
            {"id": member.get("id"), "version": member.get("version")}
            for member in document.get(member_key, [])
        ]
    return entry


def _array(item: dict[str, Any], *, unique: bool = False) -> dict[str, Any]:
    value: dict[str, Any] = {"type": "array", "items": item}
    if unique:
        value["uniqueItems"] = True
    return value


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def _descriptor(
    object_type: str,
    identifier: str,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:
    common = {
        "object_type": {"const": object_type},
        "id": {"type": "string", "pattern": identifier},
        "title": _ref("nonEmptyString"),
        "version": _ref("semver"),
        "status": _ref("status"),
        "classification": _ref("classification"),
        "description": _ref("nonEmptyString"),
        "maintainers": _ref("maintainers"),
    }
    return {
        "type": "object",
        "properties": {**common, **properties},
        "required": [
            "object_type",
            "id",
            "title",
            "version",
            "status",
            "classification",
            "description",
            "maintainers",
            *required,
        ],
        "additionalProperties": False,
    }


def descriptor_schema(metadata: dict[str, Any]) -> dict[str, Any]:
    string_array = _array(_ref("nonEmptyString"), unique=True)
    term_id_array = _array(_ref("termId"), unique=True)
    rule_id_array = _array(_ref("ruleId"), unique=True)
    requirement_set = {
        "type": "object",
        "properties": {
            "required": term_id_array,
            "recommended": term_id_array,
            "optional": term_id_array,
            "conditional": _array(_ref("conditionalRequirement")),
            "excluded": term_id_array,
        },
        "required": ["required", "recommended", "optional", "conditional", "excluded"],
        "additionalProperties": False,
    }
    rule_requirement_set = {
        "type": "object",
        "properties": {
            name: rule_id_array
            for name in ["required", "recommended", "optional", "conditional", "excluded"]
        },
        "required": ["required", "recommended", "optional", "conditional", "excluded"],
        "additionalProperties": False,
    }
    term_core = {
        "type": "object",
        "properties": {
            "id": _ref("termId"),
            "label": _ref("nonEmptyString"),
            "version": _ref("semver"),
            "kind": _ref("nonEmptyString"),
            "domain": _ref("domainId"),
            "status": _ref("status"),
            "definition": _ref("nonEmptyString"),
            "broader": term_id_array,
            "related": term_id_array,
            "notes": string_array,
        },
        "required": ["id", "label", "version", "kind", "domain", "status", "definition"],
        "additionalProperties": False,
    }
    rule_core = {
        "type": "object",
        "properties": {
            "id": _ref("ruleId"),
            "title": _ref("nonEmptyString"),
            "version": _ref("semver"),
            "status": _ref("status"),
            "scope": _array(
                {
                    "type": "string",
                    "pattern": r"^relay\.(?:domain|profile|package|mapping)\.[a-z0-9]+(?:-[a-z0-9]+)*$",
                },
                unique=True,
            ),
            "level": {"enum": RULE_LEVEL},
            "statement": _ref("nonEmptyString"),
            "rationale": _ref("nonEmptyString"),
            "testability": {"enum": TESTABILITY},
        },
        "required": [
            "id",
            "title",
            "version",
            "status",
            "scope",
            "level",
            "statement",
            "rationale",
            "testability",
        ],
        "additionalProperties": False,
    }
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            metadata["namespace"]["canonical_base_uri"]
            + "schema/descriptor/"
            + GENERATOR_VERSION
        ),
        "title": "RELAY canonical descriptor",
        "description": (
            "Structural schema for RELAY Terms, Domains, Profiles, Packages, Mappings, "
            "Conformance Rules, and their canonical registries."
        ),
        "x-relay-generation": metadata,
        "oneOf": [
            _ref(name)
            for name in [
                "termRegistry",
                "term",
                "domain",
                "profile",
                "package",
                "mapping",
                "ruleRegistry",
                "conformanceRule",
            ]
        ],
        "$defs": {
            "nonEmptyString": {"type": "string", "minLength": 1},
            "semver": {"type": "string", "pattern": SEMVER},
            "status": {"enum": STATUS},
            "classification": {"enum": CLASSIFICATION},
            "maintainers": _array(_ref("nonEmptyString"), unique=True),
            "termId": {
                "type": "string",
                "pattern": r"^relay\.term\.[a-z0-9]+(?:-[a-z0-9]+)*$",
            },
            "domainId": {
                "type": "string",
                "pattern": r"^relay\.domain\.[a-z0-9]+(?:-[a-z0-9]+)*$",
            },
            "profileId": {
                "type": "string",
                "pattern": r"^relay\.profile\.[a-z0-9]+(?:-[a-z0-9]+)*$",
            },
            "packageId": {
                "type": "string",
                "pattern": r"^relay\.package\.[a-z0-9]+(?:-[a-z0-9]+)*$",
            },
            "mappingId": {
                "type": "string",
                "pattern": r"^relay\.mapping\.[a-z0-9]+(?:-[a-z0-9]+)*$",
            },
            "ruleId": {"type": "string", "pattern": r"^RELAY-[A-Z0-9]+(?:-[A-Z0-9]+)+$"},
            "termCore": term_core,
            "term": {
                **term_core,
                "properties": {
                    "object_type": {"const": "term"},
                    **term_core["properties"],
                },
                "required": ["object_type", *term_core["required"]],
            },
            "termRegistry": {
                "type": "object",
                "properties": {
                    "object_type": {"const": "term_registry"},
                    "id": {"const": "relay.terms"},
                    "title": _ref("nonEmptyString"),
                    "version": _ref("semver"),
                    "status": _ref("status"),
                    "classification": _ref("classification"),
                    "maintainers": _ref("maintainers"),
                    "terms": _array(_ref("termCore")),
                },
                "required": [
                    "object_type",
                    "id",
                    "title",
                    "version",
                    "status",
                    "classification",
                    "maintainers",
                    "terms",
                ],
                "additionalProperties": False,
            },
            "conditionalRequirement": {
                "type": "object",
                "properties": {
                    "when": _ref("nonEmptyString"),
                    "require": term_id_array,
                },
                "required": ["when", "require"],
                "additionalProperties": False,
            },
            "domain": _descriptor(
                "domain",
                r"^relay\.domain\.[a-z0-9]+(?:-[a-z0-9]+)*$",
                {
                    "dependencies": _array(_ref("domainId"), unique=True),
                    "terms": term_id_array,
                    "rules": rule_id_array,
                    "scope": {
                        "type": "object",
                        "properties": {
                            "includes": string_array,
                            "excludes": string_array,
                        },
                        "required": ["includes", "excludes"],
                        "additionalProperties": False,
                    },
                },
                ["dependencies", "terms", "rules", "scope"],
            ),
            "profile": _descriptor(
                "profile",
                r"^relay\.profile\.[a-z0-9]+(?:-[a-z0-9]+)*$",
                {
                    "domains": _array(_ref("domainId"), unique=True),
                    "package": {"oneOf": [_ref("packageId"), {"type": "null"}]},
                    "requirements": requirement_set,
                    "rule_requirements": rule_requirement_set,
                },
                ["domains", "package", "requirements", "rule_requirements"],
            ),
            "package": _descriptor(
                "package",
                r"^relay\.package\.[a-z0-9]+(?:-[a-z0-9]+)*$",
                {
                    "base_specification": {
                        "type": "object",
                        "properties": {
                            "name": _ref("nonEmptyString"),
                            "version": _ref("nonEmptyString"),
                            "uri": {"type": "string", "format": "uri"},
                        },
                        "required": ["name", "version", "uri"],
                        "additionalProperties": False,
                    },
                    "root_entity": _ref("termId"),
                    "distribution_modes": string_array,
                    "persistent_profile_uri": {
                        "oneOf": [{"type": "string", "format": "uri"}, {"type": "null"}]
                    },
                    "persistent_profile_uri_status": _ref("nonEmptyString"),
                    "required_components": string_array,
                    "optional_components": string_array,
                    "conformance_rules": rule_id_array,
                },
                [
                    "base_specification",
                    "root_entity",
                    "distribution_modes",
                    "required_components",
                    "conformance_rules",
                ],
            ),
            "mappingEndpoint": {
                "type": "object",
                "properties": {
                    "name": _ref("nonEmptyString"),
                    "version": _ref("nonEmptyString"),
                    "uri": {"type": "string", "format": "uri"},
                },
                "required": ["name", "version"],
                "additionalProperties": False,
            },
            "mappingEntry": {
                "type": "object",
                "properties": {
                    "source": _ref("nonEmptyString"),
                    "target": _ref("nonEmptyString"),
                    "relation": _ref("nonEmptyString"),
                    "conditions": string_array,
                    "transformation": {
                        "oneOf": [_ref("nonEmptyString"), {"type": "null"}]
                    },
                    "information_loss": string_array,
                    "cardinality_or_datatype_impact": string_array,
                    "evidence": string_array,
                    "review_status": _ref("nonEmptyString"),
                    "reviewer": {
                        "oneOf": [_ref("nonEmptyString"), {"type": "null"}]
                    },
                },
                "required": [
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
                ],
                "additionalProperties": False,
            },
            "mapping": _descriptor(
                "mapping",
                r"^relay\.mapping\.[a-z0-9]+(?:-[a-z0-9]+)*$",
                {
                    "source": _ref("mappingEndpoint"),
                    "target": _ref("mappingEndpoint"),
                    "direction": _ref("nonEmptyString"),
                    "entries": _array(_ref("mappingEntry")),
                    "review": {
                        "type": "object",
                        "properties": {
                            "status": _ref("nonEmptyString"),
                            "notes": _ref("nonEmptyString"),
                        },
                        "required": ["status", "notes"],
                        "additionalProperties": False,
                    },
                },
                ["source", "target", "direction", "entries"],
            ),
            "ruleCore": rule_core,
            "conformanceRule": {
                **rule_core,
                "properties": {
                    "object_type": {"const": "conformance_rule"},
                    **rule_core["properties"],
                },
                "required": ["object_type", *rule_core["required"]],
            },
            "ruleRegistry": {
                "type": "object",
                "properties": {
                    "object_type": {"const": "conformance_rule_registry"},
                    "id": {"const": "relay.rules"},
                    "title": _ref("nonEmptyString"),
                    "version": _ref("semver"),
                    "status": _ref("status"),
                    "classification": _ref("classification"),
                    "maintainers": _ref("maintainers"),
                    "rules": _array(_ref("ruleCore")),
                },
                "required": [
                    "object_type",
                    "id",
                    "title",
                    "version",
                    "status",
                    "classification",
                    "maintainers",
                    "rules",
                ],
                "additionalProperties": False,
            },
        },
    }
    return schema


def jsonld_context(metadata: dict[str, Any]) -> dict[str, Any]:
    relay = metadata["namespace"]["canonical_base_uri"]
    schema = "https://schema.org/"
    return {
        "@context": {
            "@version": 1.1,
            "relay": relay,
            "schema": schema,
            "id": "@id",
            "object_type": "@type",
            "title": "schema:name",
            "label": "schema:name",
            "description": "schema:description",
            "definition": "schema:description",
            "version": "schema:version",
            "maintainers": {"@id": "schema:maintainer", "@container": "@set"},
            "status": "relay:status",
            "classification": "relay:classification",
            "kind": "relay:kind",
            "domain": {"@id": "relay:domain", "@type": "@id"},
            "dependencies": {
                "@id": "relay:dependency",
                "@type": "@id",
                "@container": "@set",
            },
            "terms": {"@id": "relay:term", "@type": "@id", "@container": "@set"},
            "rules": {"@id": "relay:rule", "@type": "@id", "@container": "@set"},
            "scope": "relay:scope",
            "statement": "relay:statement",
            "rationale": "relay:rationale",
            "level": "relay:level",
            "testability": "relay:testability",
            "Term": "relay:Term",
            "Domain": "relay:Domain",
            "Profile": "relay:Profile",
            "Package": "relay:Package",
            "Mapping": "relay:Mapping",
            "ConformanceRule": "relay:ConformanceRule",
        },
        "x-relay-generation": metadata,
    }


def shacl_foundations(metadata: dict[str, Any]) -> str:
    metadata_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=True)
    relay = metadata["namespace"]["canonical_base_uri"]
    return f"""# Generated by {GENERATOR_NAME} {GENERATOR_VERSION} on {GENERATION_DATE}.
# x-relay-generation: {metadata_json}
@prefix relay: <{relay}> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

relay:DescriptorShape
    a sh:NodeShape ;
    sh:targetClass relay:Term, relay:Domain, relay:Profile, relay:Package,
        relay:Mapping, relay:ConformanceRule ;
    sh:property [
        sh:path relay:status ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:in ( "proposal" "experimental" "candidate" "stable" "deprecated" "withdrawn" )
    ] .

relay:VersionedDescriptorShape
    a sh:NodeShape ;
    sh:targetClass relay:Term, relay:Domain, relay:Profile, relay:Package,
        relay:Mapping, relay:ConformanceRule ;
    sh:property [
        sh:path <https://schema.org/version> ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:pattern "{SEMVER.replace(chr(92), chr(92) * 2)}"
    ] .

relay:DomainShape
    a sh:NodeShape ;
    sh:targetClass relay:Domain ;
    sh:property [
        sh:path relay:term ;
        sh:class relay:Term
    ] ;
    sh:property [
        sh:path relay:rule ;
        sh:class relay:ConformanceRule
    ] .

relay:ConformanceRuleShape
    a sh:NodeShape ;
    sh:targetClass relay:ConformanceRule ;
    sh:property [
        sh:path relay:level ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:in ( "MUST" "MUST NOT" "SHOULD" "SHOULD NOT" "MAY" )
    ] ;
    sh:property [
        sh:path relay:testability ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:in ( "automated" "hybrid" "manual" )
    ] .
"""


def artifact_content() -> dict[Path, str]:
    metadata = source_metadata()
    return {
        Path("relay-descriptor.schema.json"): json.dumps(
            descriptor_schema(metadata), indent=2, ensure_ascii=True
        )
        + "\n",
        Path("contexts/relay-descriptor.context.jsonld"): json.dumps(
            jsonld_context(metadata), indent=2, ensure_ascii=True
        )
        + "\n",
        Path("shacl/relay-descriptor.shacl.ttl"): shacl_foundations(metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="artifact output directory (default: schemas/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report stale or missing artifacts without writing",
    )
    args = parser.parse_args()

    stale: list[str] = []
    for relative_path, content in artifact_content().items():
        output_path = args.output / relative_path
        if args.check:
            if not output_path.is_file() or output_path.read_text(encoding="utf-8") != content:
                stale.append(str(relative_path).replace("\\", "/"))
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8", newline="\n")

    if stale:
        print("stale schema artifacts: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

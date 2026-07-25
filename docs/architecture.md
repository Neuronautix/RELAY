# RELAY architecture

**Classification:** normative draft  
**Status:** proposal  
**Version:** 0.1.0

## Architectural unit

RELAY is one canonical semantic model assembled through six first-class objects:

1. **Term** — a uniquely identified concept, property, relationship, controlled value, or datatype.
2. **Domain** — a reusable semantic module that owns a coherent area of research metadata.
3. **Profile** — a versioned set of constraints over selected Terms and Domains for one use case.
4. **Package** — a transfer representation containing a dataset release, profile declarations, metadata, files or references, provenance, and integrity information.
5. **Mapping** — a version-pinned, directional relationship between RELAY and an external standard, ontology, schema, file format, database, or software system.
6. **Conformance Rule** — a stable, identifiable requirement with a defined scope and test method.

## Dependency direction

```text
Terms → Domains → Profiles → Packages → Serializations and implementations
```

Mappings and validation operate across these layers. They do not change the meaning of Terms or Domains.

## Object contracts

Every first-class object MUST declare:

```text
object type
stable identifier
human-readable title
version
maturity status
description
normative or informative classification
maintainer or responsible group
explicit dependencies
```

Additional contracts are object-specific:

* A Term defines one meaning and may list broader or related Terms.
* A Domain declares its included Terms, dependencies, scope, exclusions, and Rules.
* A Profile imports Domains and states required, recommended, optional, conditional, and excluded elements without redefining them.
* A Package declares its base packaging standard, represented root entity, included profile declarations, integrity requirements, and permitted distribution modes.
* A Mapping declares source and target versions, direction, relation type, conditions, transformations, information loss, evidence, and review status.
* A Conformance Rule declares normative level, scope, statement, rationale, and testability.

## Source-of-truth hierarchy

* Stable semantic identifiers and machine-readable object metadata are authored in canonical YAML descriptors.
* Normative requirements are authored in `rules/registry.yaml` and referenced by identifier from narrative specifications.
* Human-readable documentation explains the model but MUST NOT introduce hidden normative requirements.
* JSON Schema, SHACL, RDF, JSON-LD contexts, tabular templates, and implementation models are derived representations.
* A contradiction between canonical descriptors and normative documentation is a specification defect; implementations must not silently choose one.

## Model versus exchange

The semantic model is independent of packaging. The same DatasetRelease may be represented through RO-Crate, an API, a database export, or a tabular bundle, provided the selected RELAY Package and Profile rules are met.

RO-Crate is the initial preferred package technology, but it is not the semantic source of truth. ISA remains a major model and serialization target; RELAY may embed ISA-JSON or ISA-Tab and map to ISA RO-Crate conventions without making the ISA-Crate structure the only RELAY representation.

## Definitions and executions

Reusable definitions and actual executions are distinct. This applies to protocols, protocol segments, instruments, acquisition configurations, analytical methods, and software environments.

```text
ProtocolDefinition → ProtocolSegmentDefinition → ProtocolExecution
                                              ↘ ProtocolDeviation
```

The planned procedure and the execution record may be compared, but neither replaces the other.

## Units of inference

RELAY represents assignment, experimental, observational, biological, and analytical units explicitly. A profile must not assume these are identical. This is required to prevent invalid attribution and pseudoreplication in cage-, group-, sample-, and subject-level data.

## Anti-patterns

RELAY rejects:

* a single monolithic universal schema;
* copied profile schemas that drift from shared semantics;
* prose-only mappings;
* hidden requirements inside validator code;
* generated schemas as the semantic authority;
* profiles that silently redefine Core terms;
* treating the comprehensive model as universally mandatory;
* equating technical conformance with scientific validity or FAIR certification.

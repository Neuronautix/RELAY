# RELAY

> **R&D scope (October 2026):** RELAY is an experimental interoperability design, not a certified universal metadata standard. New work should be justified by a concrete exchange between two named systems, ideally using versioned mappings and loss-aware fixtures, rather than expanding the abstract model by default. See [agent guidance](AGENTS.md).


**RELAY — Research Exchange Layer for All laboratorY metadata**

[![Validate RELAY repository](https://github.com/Neuronautix/RELAY/actions/workflows/validate.yml/badge.svg)](https://github.com/Neuronautix/RELAY/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

RELAY is an open, profile-driven standard for representing, validating, packaging, and exchanging the metadata and research context associated with laboratory studies.

It is intended to provide a common exchange contract between laboratory information systems, acquisition platforms, analysis environments, repositories, electronic laboratory notebooks, data-management systems, and downstream reuse applications.

> **Status:** experimental community specification and tooling. The object
> architecture, repository validator, release lock, generated schema
> foundations, package-integrity tooling, and Profile migration analysis are
> implemented. Scientific Domains, operational Terms, mappings, and Profiles
> remain proposals and must mature independently before a candidate release.

## Quick start

RELAY supports Python 3.10 and later.

```text
python -m pip install .
relay validate-repository .
relay verify-package examples/draft/minimal-ro-crate
relay profile-diff old-profile.yaml new-profile.yaml
relay capabilities
```

Commands return meaningful exit codes and can emit explainable JSON reports for
CI and other tools:

```text
relay validate-repository . --format json --output relay-report.json
```

See the [tooling guide](docs/tooling.md) for package-manifest construction,
Profile migration reports, the GitHub Action, report formats, and capability
boundaries.

## What is implemented

| Capability | Status |
|---|---|
| Canonical descriptor and cross-reference validation | Available |
| Explainable text and JSON diagnostics | Available |
| Version-pinned release lock for all 52 registered objects | Available |
| JSON Schema 2020-12, JSON-LD context, and SHACL foundations | Available |
| Package-manifest construction and SHA-256 verification | Available |
| Profile requiredness diff and migration planning | Available |
| Reusable GitHub validation Action | Available |
| Complete RO-Crate builder and persistent Profile Crate | Planned |
| ISA round-trip translation with a loss ledger | Blocked on reviewed mappings |
| Research-design and pseudoreplication linting | Blocked on operational Terms |
| Interactive provenance and integrity graph | Planned |

The machine-readable version of these boundaries is available through
`relay capabilities --format json`. Planned or blocked features are not
presented as conformance capabilities.

## Architectural model

RELAY is organized around six first-class objects:

1. **Term** — a uniquely identified concept, property, relationship, controlled value, or datatype.
2. **Domain** — a reusable semantic module representing a coherent area of laboratory research metadata.
3. **Profile** — a versioned set of use-case constraints over selected Terms and Domains.
4. **Package** — a transferable research object containing a dataset release, metadata, files or references, provenance, integrity information, and profile declarations.
5. **Mapping** — an explicit, version-pinned relationship between RELAY and an external standard, ontology, schema, format, database, or software system.
6. **Conformance Rule** — a stable, identifiable requirement that can be tested manually or automatically.

```text
RELAY Terms
    ↓
Domains
    ↓
Profiles
    ↓
Exchange Packages
    ├── Mappings
    └── Conformance
```

Mappings and validation operate across these layers but do not redefine their semantics.

## Repository layout

```text
terms/       Canonical RELAY terms and controlled values
  ↓
domains/     Reusable semantic modules
  ↓
profiles/    Use-case constraints over domains
  ↓
packages/    Transfer and packaging specifications

mappings/     Explicit crosswalks to standards and systems
rules/        Stable conformance requirements

docs/         Architecture, policies, and implementation guidance
schemas/      Derived schemas; never the semantic source of truth
examples/     Draft examples and, later, valid/invalid fixtures
relay/        Installable Python package and command-line tooling
scripts/      Repository and conformance tooling
tests/        Automated checks and fixtures

namespace.yaml     Proposed persistent namespace and resolution policy
release.yaml       Repository snapshot version and maturity
relay.lock.yaml    Version, path, URI, and digest pins for registered objects
```

Start with the [architecture](docs/architecture.md),
[repository conventions](docs/repository-conventions.md),
[namespace and resolution policy](docs/namespace-and-resolution.md),
[release-integrity model](docs/release-integrity.md),
[Core domain](domains/core/README.md),
[package strategy](docs/package-strategy.md), and
[conformance model](docs/conformance.md).

## Versioning, schemas, and integrity

RELAY objects carry independent semantic versions. Repository snapshots are
versioned separately in `release.yaml`; `relay.lock.yaml` pins the exact
version, canonical URI, source path, and canonical-LF SHA-256 digest of every
registered Term, Domain, Profile, Package, Mapping, and Rule.

The proposed persistent namespace is `https://w3id.org/relay/`. It remains
explicitly marked `proposed` until the external redirect is registered and
tested.

JSON Schema, JSON-LD, and SHACL artifacts are reproducibly generated under
`schemas/`. They are validation and interoperability views of the canonical
YAML—not parallel semantic authorities:

```text
python schemas/generate.py --check
python scripts/validate_release.py
```

## Scope

RELAY is designed to represent the full lifecycle of laboratory research, including:

- objectives, investigations, studies, assays, and study design;
- agents, organizations, software agents, and automated services;
- biological subjects, experimental units, samples, and biological materials;
- housing, cages, environmental conditions, stable locations, and physical resources;
- protocol definitions, protocol segments, execution records, interventions, and deviations;
- instruments, sensors, software, acquisition systems, observations, and measurements;
- raw, primary, processed, and derived data assets;
- analysis, quality control, provenance, compliance, welfare, and dataset releases.

The initial focus is preclinical research, while the architecture is intended to remain applicable to in vivo, in vitro, ex vivo, organoid, imaging, omics, toxicology, computational, and other laboratory contexts.

## Design principles

- **Comprehensive model, selective profiles.** RELAY can represent a broad metadata landscape, but no exchange is expected to contain every defined element.
- **Semantics before serialization.** JSON, JSON-LD, RDF, tabular formats, JSON Schema, and SHACL are representations of the model, not the semantic authority.
- **Reuse before reinvention.** Existing standards and identifier systems are reused when they adequately represent the required concept.
- **Explicit mappings.** Mappings declare direction, relation type, conditions, transformations, information loss, target versions, evidence, and review status.
- **Definition and execution are distinct.** Planned protocols, instruments, or analytical methods are separate from their actual execution or use.
- **Units are explicit.** Assignment, experimental, observational, biological, and analysis units may differ and must not be silently conflated.
- **Extensible without semantic fragmentation.** Profiles and extensions may constrain or add semantics but must not silently redefine existing RELAY identifiers.
- **Versioned and testable.** Domains, profiles, packages, mappings, rules, examples, and generated schemas are versioned and checked in continuous integration.

## Initial exchange strategy

RELAY defines a proposed dedicated profile of **RO-Crate 1.3** as its first
exchange package. The RO-Crate root represents one immutable `DatasetRelease`;
the stable conceptual `Dataset` remains distinct. ISA-JSON and ISA-Tab may be
included or generated, while mappings to ISA RO-Crate/ISA-Crate are maintained
as explicit Mapping objects rather than allowed to determine RELAY's entire
model.

The current example demonstrates package structure and integrity handling; it
is intentionally not presented as a complete conformance fixture. A persistent
Profile Crate, reviewed mapping entries, and complete operational Profile remain
release-gate work.

## Non-goals

RELAY does not aim to replace ISA, RO-Crate, ISA-Crate, PROV-O, SEND, schema.org, Bioschemas, domain ontologies, or laboratory software. It does not prescribe one universal workflow or require every element in every exchange.

RELAY conformance indicates that information is represented and exchanged according to declared RELAY rules. It does **not** certify scientific validity, reproducibility, ethical acceptability, regulatory compliance, animal-welfare quality, or FAIRness.

## Development

Current development covers both semantic architecture and the tooling needed to
test it. See the [roadmap](ROADMAP.md), [contribution guide](CONTRIBUTING.md),
[governance model](GOVERNANCE.md), and [release procedure](RELEASES.md).

RELAY's validation tooling supports Python 3.10 and later. Install the
development dependencies and run the complete local checks with:

```text
python -m pip install -r requirements-dev.txt
ruff check relay scripts schemas tests
python schemas/generate.py --check
python scripts/validate_repository.py
python scripts/validate_release.py
python -m unittest discover -s tests -p "test_*.py"
python -m pip wheel . --no-deps --wheel-dir dist
```

CI runs these checks on Python 3.10 and 3.14. Tag builds additionally verify
release metadata and produce source archives, `relay.lock.yaml`, and
`SHA256SUMS`; they do not publish a GitHub Release or DOI automatically.

## Community and support

Security-sensitive issues should follow the private reporting process in
[SECURITY.md](SECURITY.md).

Project accountability is recorded in [MAINTAINERS.md](MAINTAINERS.md).
Feature requests, support questions, specification defects, and semantic object
proposals use dedicated GitHub issue forms. Repository versions, immutable tag
conventions, release checks, and archival guidance are documented in
[RELEASES.md](RELEASES.md).

Contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Third-party
material and its licensing are governed by
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Citation

If RELAY contributes to published work, cite the project using
[CITATION.cff](CITATION.cff). Release-specific archival identifiers will be
added when versioned releases are deposited.

## License

RELAY specification text, machine-readable metadata, examples, and software
are licensed under the [MIT License](LICENSE).

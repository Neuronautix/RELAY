# RELAY

**RELAY — Research Exchange Layer for All laboratorY metadata**

RELAY is an open, profile-driven standard for representing, validating, packaging, and exchanging the metadata and research context associated with laboratory studies.

It is intended to provide a common exchange contract between laboratory information systems, acquisition platforms, analysis environments, repositories, electronic laboratory notebooks, data-management systems, and downstream reuse applications.

> **Status:** experimental community specification. The repository currently establishes the architecture, governance, and object contracts; scientific domains and operational profiles will mature independently.

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
scripts/      Repository and conformance tooling
tests/        Automated checks and fixtures
```

Start with the [architecture](docs/architecture.md), [repository conventions](docs/repository-conventions.md), [Core domain](domains/core/README.md), [package strategy](docs/package-strategy.md), [conformance model](docs/conformance.md), and [tooling guide](docs/tooling.md).

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

RELAY will define a dedicated profile of **RO-Crate 1.3** as its first normative exchange package. The RO-Crate root represents one immutable `DatasetRelease`; the stable conceptual `Dataset` remains distinct. ISA-JSON and ISA-Tab may be included or generated, while mappings to ISA RO-Crate/ISA-Crate are maintained as explicit Mapping objects rather than allowed to determine RELAY's entire model.

## Non-goals

RELAY does not aim to replace ISA, RO-Crate, ISA-Crate, PROV-O, SEND, schema.org, Bioschemas, domain ontologies, or laboratory software. It does not prescribe one universal workflow or require every element in every exchange.

RELAY conformance indicates that information is represented and exchanged according to declared RELAY rules. It does **not** certify scientific validity, reproducibility, ethical acceptability, regulatory compliance, animal-welfare quality, or FAIRness.

## Development

The first phase prioritizes architecture and semantics over application tooling. See the [roadmap](ROADMAP.md), [contribution guide](CONTRIBUTING.md), and [governance model](GOVERNANCE.md).

RELAY's validation tooling supports Python 3.10 and later. Install the
development dependency and run the complete local checks with:

```text
python -m pip install -r requirements-dev.txt
ruff check relay scripts schemas tests
python schemas/generate.py --check
python scripts/validate_repository.py
python scripts/validate_release.py
python -m unittest discover -s tests -p "test_*.py"
```

Install the experimental `relay` command with `python -m pip install .`.
It provides explainable repository validation, package-manifest construction
and verification, and Profile migration analysis; see the
[tooling guide](docs/tooling.md).

Security-sensitive issues should follow the private reporting process in
[SECURITY.md](SECURITY.md).

Project accountability is recorded in [MAINTAINERS.md](MAINTAINERS.md).
Feature requests, support questions, specification defects, and semantic object
proposals use dedicated GitHub issue forms. Repository versions, immutable tag
conventions, release checks, and archival guidance are documented in
[RELEASES.md](RELEASES.md).

## Citation

If RELAY contributes to published work, cite the project using
[CITATION.cff](CITATION.cff). Release-specific archival identifiers will be
added when versioned releases are deposited.

## License

RELAY specification text, machine-readable metadata, examples, and software
are licensed under the [MIT License](LICENSE).

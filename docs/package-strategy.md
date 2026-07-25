# RELAY exchange-package strategy

**Classification:** normative draft with informative implementation guidance  
**Status:** proposal  
**Target base specification:** RO-Crate 1.3

## Decision

RELAY will define its own RO-Crate profile as the initial normative exchange package. The semantic model remains independent of RO-Crate, and other Package objects may be added later.

RO-Crate 1.3 is the current long-term release and supports domain profiles and Profile Crates. RELAY will use those mechanisms rather than embedding RELAY semantics only in ad hoc JSON-LD.

## Root entity

The RO-Crate Root Data Entity represents one immutable `DatasetRelease`.

```text
Dataset              conceptual identity
DatasetRelease       versioned scientific content and RO-Crate root
ExchangePackage      one attached or detached distribution of that release
```

The ZIP archive is not the DatasetRelease. Regenerating the same release in another package form does not change the release identity.

## Distribution modes

* **Attached crate** — metadata and selected payload files are transferred together, normally as `.crate.zip`.
* **Detached crate** — metadata references resolvable external data assets and repositories.

A Profile may require one mode or permit both.

## RELAY profile declaration

The Root Data Entity declares conformance to:

1. RO-Crate 1.3; and
2. the exact version of the selected RELAY RO-Crate Profile; and
3. applicable RELAY application Profiles.

A persistent profile URI and Profile Crate will be published before candidate release. Local GitHub paths are provisional and must not be treated as permanent identifiers.

## Manifest and integrity

Base RO-Crate metadata are not assumed to be an exhaustive integrity manifest. RELAY packages therefore require each included payload file to declare:

```text
path or URI
content role
media type
byte size
SHA-256 checksum for included immutable files
related RELAY entity or data asset
```

The package's own outer archive checksum is recorded by the transfer system or repository because an archive cannot reliably contain its final self-checksum.

## ISA and ISA-Crate

RELAY preserves the Investigation–Study–Assay organization through the `relay.domain.isa` Domain. ISA-JSON and ISA-Tab may be embedded as package payloads or generated as exchange views.

ISA RO-Crate/ISA-Crate conventions are treated as versioned mapping targets. RELAY does not require an ISA Investigation to be the crate root because a DatasetRelease may contain multiple investigations, shared resources, or cross-study analyses. Where strict ISA-Crate compatibility is needed, a derived investigation-scoped crate may be generated and its transformation and information loss declared.

## Informative draft layout

```text
crate-root/
├── ro-crate-metadata.json
├── README.md
├── metadata/
│   ├── core/
│   ├── isa/
│   ├── subjects/
│   ├── housing/
│   └── ...
├── protocols/
├── data/
├── software/
└── validation/
    ├── relay-validation-report.json
    └── relay-package-manifest.json
```

Directory names are informative. Graph relations, identifiers, declared Profiles, and Rules carry the semantics.

## Official references

* RO-Crate 1.3: https://w3id.org/ro/crate/1.3
* RO-Crate profiles: https://www.researchobject.org/ro-crate/specification/1.3/profiles.html
* ISA framework: https://isa-tools.org/
* ISA abstract model: https://isa-specs.readthedocs.io/en/latest/isamodel.html

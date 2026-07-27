# RELAY roadmap

The roadmap is ordered by dependency, not by calendar date.

## Phase 0 — Repository foundation

* Establish the six first-class objects: Term, Domain, Profile, Package, Mapping, and Conformance Rule.
* Establish source-of-truth, identifier, versioning, maturity, and governance policies.
* Add automated structural validation.

## Phase 1 — Core semantic model

* Finalize Dataset and immutable DatasetRelease semantics.
* Finalize Agent, Person, Organization, SoftwareAgent, AutomatedService, Affiliation, RoleAssignment, and identifier semantics.
* Finalize stable Location, PhysicalResource, and ResourcePlacement boundaries.
* Define metadata provenance and registry declarations.

## Phase 2 — Exchange package

* Publish the first RELAY RO-Crate profile against RO-Crate 1.3.
* Define attached and detached package modes.
* Define package manifests, integrity requirements, profile declarations, and validation reports.
* Test optional ISA-JSON and ISA-Tab payloads and mappings to ISA RO-Crate/ISA-Crate conventions.

## Phase 3 — General preclinical domains

* ISA context and study design.
* Subjects, biospecimens, housing and cages, and environment.
* Protocol definitions, protocol segments, execution records, interventions, assays, and acquisition.
* Observations, data assets, analyses, quality control, compliance, and welfare.

## Phase 4 — Operational profiles

* Complete one general preclinical study-exchange profile.
* Complete one technology- or assay-specific profile using real datasets.
* Define required, recommended, optional, conditional, and excluded elements.

## Phase 5 — Mappings and conformance

* Review mappings to ISA, RO-Crate, and PROV-O.
* Add valid and invalid normative fixtures.
* Add profile and package validators.
* Publish machine-readable schemas derived from the canonical model.

## Release gate

A candidate public release requires documented MIT license compliance, a
stable namespace policy, at least one complete profile, at least one validated
RO-Crate package, migration notes, and independent review of normative rules.

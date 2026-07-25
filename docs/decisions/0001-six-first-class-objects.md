# ADR 0001 — Six first-class RELAY objects

**Status:** accepted  
**Date:** 2026-07-25

## Context

Laboratory metadata standards often combine semantic definitions, use-case requirements, serialization schemas, system mappings, and validation logic in one artifact. This causes duplication, hidden requirements, and incompatible profile forks.

## Decision

RELAY is organized around six first-class objects: Term, Domain, Profile, Package, Mapping, and Conformance Rule.

The dependency direction is Terms → Domains → Profiles → Packages. Mappings and conformance operate across those layers without redefining them.

## Consequences

* Shared semantics are defined once and constrained by Profiles.
* Package technology can evolve without changing the conceptual model.
* Mappings become versioned, reviewable artifacts rather than prose appendices.
* Normative rules receive stable identifiers and can be tested independently.
* Generated schemas remain derived outputs.
* The repository requires explicit cross-object references and automated integrity checks.

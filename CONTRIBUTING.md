# Contributing to RELAY

RELAY is a semantic specification. Contributions should preserve meaning, provenance, and version history rather than only making a serialization pass validation.

## Before opening a pull request

1. Identify the affected first-class object: Term, Domain, Profile, Package, Mapping, or Conformance Rule.
2. Open an object-proposal issue for new semantics or a breaking change.
3. Reuse an existing identifier when the meaning is unchanged. Never create a new identifier only to rename a label.
4. Add or update the canonical YAML descriptor and the associated human-readable documentation.
5. Add explicit conformance rules for every normative requirement.
6. Add mapping entries when external interoperability is affected.
7. Add valid and invalid fixtures when the change is testable.
8. Run `python scripts/validate_repository.py` and the unit tests.

## Pull-request scope

Prefer one coherent semantic change per pull request. A pull request may change several object types when the dependency is explicit, for example a new Term, its Domain inclusion, a Profile constraint, and corresponding rules.

A pull request must state:

* what meaning changes;
* whether the change is normative or informative;
* affected stable identifiers and versions;
* compatibility and migration consequences;
* mappings or information loss introduced;
* validation performed.

## Normative wording

Use MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY only in normative content. Every normative statement must be represented by a stable rule identifier from `rules/registry.yaml`.

## Generated content

Do not manually edit generated schemas or exports. Change the canonical Term, Domain, Profile, Package, Mapping, or Rule source and regenerate the derivative.

## Licensing

A project license has not yet been selected. Do not contribute third-party text, schemas, or code unless its license is compatible with the license decision recorded by the maintainers.

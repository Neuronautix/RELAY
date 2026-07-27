# Contributing to RELAY

RELAY is a semantic specification. Contributions should preserve meaning, provenance, and version history rather than only making a serialization pass validation.

Use the dedicated GitHub forms for specification defects, semantic object
proposals, feature requests, and support questions. Security-sensitive reports
must follow [SECURITY.md](SECURITY.md) and must not be filed publicly.

## Before opening a pull request

1. Identify the affected first-class object: Term, Domain, Profile, Package, Mapping, or Conformance Rule.
2. Open an object-proposal issue for new semantics or a breaking change.
3. Reuse an existing identifier when the meaning is unchanged. Never create a new identifier only to rename a label.
4. Add or update the canonical YAML descriptor and the associated human-readable documentation.
5. Add explicit conformance rules for every normative requirement.
6. Add mapping entries when external interoperability is affected.
7. Add valid and invalid fixtures when the change is testable.
8. Using Python 3.10 or later, install `requirements-dev.txt`, run
   `ruff check relay scripts schemas tests`, run
   `python schemas/generate.py --check`, run
   `python scripts/validate_repository.py`, run
   `python scripts/validate_release.py`, and run
   `python -m unittest discover -s tests -p "test_*.py"`.

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

RELAY is licensed under the [MIT License](LICENSE). By submitting a
contribution, you agree that it may be distributed under that license and
that you have the right to submit it. Identify third-party material and its
license in the pull request; do not copy material whose terms are incompatible
with MIT distribution.

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

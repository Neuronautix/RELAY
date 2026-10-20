# Agent guidance — RELAY

## Status and mission
RELAY is **experimental R&D**, not an accepted universal scientific metadata standard or a deployed exchange infrastructure. Current tools validate repository structure, pinned descriptors, packages and certain migration properties; the scientific domain vocabularies, mappings and operational profiles remain proposals. Aim to prove a **specific interoperability need** between a named producer and consumer before extending the general model.

## Ownership boundaries
- Scientific concepts remain owned by their source standards or applications (e.g. HCMO, ISA, DWB, ORW, Metadatapp). Do not silently redefine them as RELAY terms.
- RELAY may describe explicit, version-pinned *exchange profiles and mappings*, including mapping direction, preconditions, units, missingness, information loss and source/target identity.
- RO-Crate is a packaging option, not the semantic source of truth; do not claim validated conformance on the basis of syntactic export alone.
- Treat examples, draft mappings and planned features as non-normative. An absent or unknown mapping stays unknown; never guess it.

## Before proposing a change
Identify: (1) actual producer and consumer; (2) a fixture of each real format, with redistribution clearance; (3) a precise round-trip or one-way exchange question; (4) a measurable pass/fail criterion; (5) possible information loss; and (6) why existing standards/adapters are insufficient. Prefer a small adapter or mapping over a new universal abstraction. Ask for explicit scope approval before adding a domain or promising compatibility.

## Repository authorities
Canonical object descriptors are in `terms/`, `domains/`, `profiles/`, `packages/`, `mappings/` and `rules/`. `namespace.yaml`, `release.yaml` and `relay.lock.yaml` record namespace/release identity and pins. `schemas/` are derived artifacts; do not edit generated artifacts as independent authority. See `docs/architecture.md`, `docs/conformance.md`, `README.md`, and `ROADMAP.md`.

## Validation for changes
```bash
python -m pip install -r requirements-dev.txt
ruff check relay scripts schemas tests
python schemas/generate.py --check
python scripts/validate_repository.py
python scripts/validate_release.py
python -m unittest discover -s tests -p 'test_*.py'
```
For proposed mappings, include positive/negative fixtures and explicit evidence of compatibility. Do not upgrade a proposed feature to a supported claim without tests and a reviewed decision. Never silently alter pinned contract semantics.

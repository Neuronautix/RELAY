## Object scope

- [ ] Term
- [ ] Domain
- [ ] Profile
- [ ] Package
- [ ] Mapping
- [ ] Conformance Rule
- [ ] Informative documentation/tooling only

## Change

Describe the semantic or implementation change.

## Normative impact

List affected stable identifiers, rule identifiers, versions, requiredness, and compatibility consequences. State `None` for an informative-only change.

## Interoperability impact

Describe mappings, transformations, version constraints, and any information loss.

## Validation

- [ ] `python scripts/validate_repository.py`
- [ ] `python -m unittest discover -s tests`
- [ ] Valid fixture added or updated when applicable
- [ ] Invalid fixture added or updated when applicable
- [ ] Migration note added for a breaking change

## Guardrails

- [ ] No profile silently redefines a Core term.
- [ ] No generated schema is treated as the semantic source of truth.
- [ ] RELAY conformance is not presented as FAIR or scientific certification.

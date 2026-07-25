# Repository conventions

**Classification:** normative draft  
**Status:** proposal

## Canonical paths

| Object | Canonical path |
|---|---|
| Term | `terms/registry.yaml` initially; may later be split without changing identifiers |
| Domain | `domains/<domain-id>/domain.yaml` |
| Profile | `profiles/<profile-id>/profile.yaml` |
| Package | `packages/<package-id>/package.yaml` |
| Mapping | `mappings/<mapping-id>/mapping.yaml` |
| Conformance Rule | `rules/registry.yaml` initially; may later be split without changing identifiers |

A neighboring `README.md` provides human-readable scope and rationale. Templates beginning with `_template` are informative and are not registered objects.

## Identifiers

Repository object identifiers use the provisional local pattern:

```text
relay.term.<slug>
relay.domain.<slug>
relay.profile.<slug>
relay.package.<slug>
relay.mapping.<slug>
RELAY-<SCOPE>-<NNN>
```

These identifiers are semantic identifiers, not file paths. Moving a file does not create a new object. A persistent web namespace will be selected before candidate release; existing identifiers will be migrated explicitly rather than silently replaced.

## Files and names

* Paths and identifiers use lower-case ASCII kebab-case except stable Rule identifiers.
* YAML keys use lower-case snake_case.
* Human labels may change without identifier changes when meaning is preserved.
* Every text file is UTF-8 with LF line endings.
* Dates use ISO 8601. Instants include `Z` or an explicit UTC offset.
* Semantic versions use `MAJOR.MINOR.PATCH`.

## Normative content

Normative requirements are represented by stable Rule objects. Markdown uses rule IDs and may quote the requirement but does not create unregistered obligations.

## Generated outputs

Derived schemas and serializations belong under `schemas/` or a future `dist/` directory. Generated files must identify their source object versions and generator version. They must not be manually maintained as parallel semantic definitions.

## Extensions

Extensions use a declared namespace and dependencies. An extension may add Terms, Domains, Profile constraints, Mappings, and Rules. It must not reuse a RELAY identifier for different meaning or weaken a requirement while claiming conformance to the original Profile.

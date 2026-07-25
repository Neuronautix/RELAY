# RELAY conformance

RELAY validation is layered. A validator should report each layer separately rather than collapsing all outcomes into one score.

## Validation layers

1. **Repository/object validation** — canonical descriptors, identifiers, references, versions, and dependency cycles.
2. **Serialization validation** — JSON, JSON-LD, RDF, YAML, CSV, or other syntax and datatype requirements.
3. **Semantic validation** — term use, entity relations, cardinality, temporal consistency, and controlled values.
4. **Profile validation** — required, recommended, optional, conditional, and excluded content for a declared use case.
5. **Package validation** — root entity, profile declarations, manifests, files or references, integrity, and access conditions.
6. **Mapping validation** — source/target versions, transformations, round-trip expectations, and declared information loss.

## Outcomes

```text
pass
fail
warning
not_applicable
not_tested
```

A package must not receive `pass` for an untested rule. Critical failures are reported independently from completeness.

## Conformance claims

A conformance claim identifies:

```text
RELAY object or profile identifier and version
package identifier and dataset release
validator name and version
validation date
rule-set version
per-rule outcomes
```

RELAY conformance means that metadata are represented and exchanged according to the declared RELAY rules. It does not certify scientific validity, reproducibility, ethical acceptability, animal-welfare quality, regulatory compliance, or FAIRness.

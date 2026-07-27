# Derived schemas

This directory contains reproducible implementation artifacts derived from the
canonical YAML descriptors. They help tools exchange and validate RELAY object
metadata; they do not replace the descriptors as the semantic source of truth.

## Available foundations

| Artifact | Purpose |
|---|---|
| `relay-descriptor.schema.json` | JSON Schema 2020-12 structure for all six first-class descriptors and the Term and Rule registries |
| `contexts/relay-descriptor.context.jsonld` | Minimal JSON-LD 1.1 mapping for shared descriptor metadata |
| `shacl/relay-descriptor.shacl.ttl` | Initial SHACL constraints for versioned descriptors, Domains, and Conformance Rules |

The JSON-LD and SHACL files use the configured `https://w3id.org/relay/`
canonical base for RELAY-specific IRIs. Its namespace status is `proposed`
until the external W3ID redirect is activated. Generic metadata maps to
Schema.org where the meaning is compatible.

JSON Schema validates descriptor structure only. Cross-file references,
dependency integrity, and repository policy remain the responsibility of the
repository validator.

## Reproducible generation

Every artifact records its source descriptor identifiers and versions,
generator name and version, generation date, and a SHA-256 digest of every
canonical source file. Term and Rule registry metadata also enumerates the ID
and version of each contained first-class object. Digests cover UTF-8 text
normalized to LF, making staleness checks independent of worktree line endings.
Rebuild after changing a canonical descriptor:

```console
python schemas/generate.py
```

Confirm that committed artifacts are current without changing files:

```console
python schemas/generate.py --check
```

The generator is deterministic. Tests validate the schema against every
canonical descriptor, check representative invalid input, verify JSON-LD/SHACL
vocabulary alignment, and fail when an artifact is stale.

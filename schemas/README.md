# Derived schemas

This directory is reserved for generated JSON Schema, SHACL, JSON-LD context, RDF, tabular templates, and other implementation artifacts.

Generated schemas are not the semantic source of truth. Each generated artifact must record:

```text
source Term, Domain, Profile, Package, Mapping, and Rule versions
generator name and version
generation date
```

No generated schema is committed until a reproducible generator and regression tests are present.

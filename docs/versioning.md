# Versioning and maturity

RELAY repository releases and RELAY objects are distinct versioning layers.

Each repository release records its complete object-version graph in
`relay.lock.yaml`. Compact cross-object references resolve through that lock,
so existing descriptors remain valid while consumers receive an exact version,
source path, canonical URI, and integrity digest. See
[Release lock and integrity](release-integrity.md).

## Object versions

Terms, Domains, Profiles, Packages, Mappings, and Rule sets declare semantic versions independently.

* **PATCH** — clarification or defect correction that does not change valid meaning or conformance.
* **MINOR** — backward-compatible additions, new optional terms, or additional mappings.
* **MAJOR** — breaking semantic, structural, requiredness, or conformance changes.

Stable identifiers are not reassigned. Deprecated objects remain resolvable with replacement and migration guidance.

## Maturity

```text
proposal → experimental → candidate → stable → deprecated | withdrawn
```

Maturity and semantic version are independent. A `0.x` version is not automatically experimental, and an experimental object can have several reviewed versions.

## Dataset releases

DatasetRelease versioning describes scientific content, not RELAY schema versions or package formats. Re-serializing the same DatasetRelease as another supported Package does not create a new DatasetRelease.

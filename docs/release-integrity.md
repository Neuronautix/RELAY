# Release lock and integrity

**Classification:** normative draft  
**Status:** proposal

RELAY objects version independently, while a repository release publishes one
coherent graph of those versions. `relay.lock.yaml` records that graph without
requiring every existing descriptor reference to be migrated immediately.

## Consumer contract

When a compact identifier appears in a descriptor, package, or validation
claim, consumers resolve it through the release lock. The resolved tuple is:

```text
(compact identifier, object type, semantic version, canonical URI,
 source path, source SHA-256)
```

The source digest protects the complete descriptor after the repository's
required UTF-8/LF text normalization. This makes the digest identical in clean
Windows and Linux checkouts. Terms and Rules share registry files, so multiple
pins intentionally refer to the same protected source. The lock also protects
the normalized `release.yaml` and `namespace.yaml` configuration bytes used to
construct its metadata.

The lock is complete rather than selective: every canonical Term, Domain,
Profile, Package, Mapping, and Rule in the repository must have exactly one
entry. Templates are excluded.

## Maintainer workflow

After intentionally changing a canonical descriptor or object version:

```text
python scripts/validate_release.py --write
python scripts/validate_release.py
```

`--write` deterministically rebuilds the lock from canonical sources.
Validation fails for missing or additional pins, version drift, source-path
drift, checksum drift, invalid namespace configuration, unsafe paths, or a
repository release version inconsistent with `release.yaml`.

The lock is a generated release catalog, not a substitute for semantic review.
A changed object meaning still requires the appropriate semantic-version
increment described in `docs/versioning.md`.

## Tagged releases

Before publishing a release, maintainers must:

1. update `release.yaml` and canonical object versions as needed;
2. rebuild and validate the lock;
3. create the immutable `v<release-version>` tag used by namespace resolution;
4. verify that the tag contains exactly the bytes protected by the lock; and
5. publish the lock beside any release bundle.

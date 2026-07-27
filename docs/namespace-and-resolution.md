# Namespace and identifier resolution

**Classification:** normative draft  
**Status:** proposal

RELAY preserves the existing compact identifiers, such as
`relay.term.dataset-release` and `RELAY-PACKAGE-002`. They remain canonical
semantic identifiers and do not acquire new meanings.

`namespace.yaml` configures `https://w3id.org/relay/` as the proposed
persistent web namespace. Its versioned URI pattern is:

```text
https://w3id.org/relay/<object-type>/<slug>/<version>
```

For example, the proposed versioned URI for `relay.domain.core` version
`0.1.0` is:

```text
https://w3id.org/relay/domain/core/0.1.0
```

Rule slugs preserve the lower-cased rule identifier, for example
`https://w3id.org/relay/rule/relay-package-002/0.1.0`.

## Resolution model

The checked-in `relay.lock.yaml` is the authoritative resolver for a
repository release. It maps every compact Term, Domain, Profile, Package,
Mapping, and Rule identifier to:

- its exact semantic version;
- its canonical versioned URI;
- its canonical source path; and
- the SHA-256 digest of that source.

An unversioned web URI is a discovery alias for the latest non-withdrawn
version. It must redirect or link to a versioned URI and must not be stored as
an immutable conformance target.

Versioned releases resolve source files through an immutable `v<version>` Git
tag. Development snapshots may resolve through a full Git commit. Branch URLs
are not immutable and cannot substantiate a released lock.

## Activation gate

The namespace is intentionally marked `proposed` until the external W3ID
redirect is registered and tested. Candidate or stable RELAY releases must
not advertise the namespace as active before all of the following hold:

1. Neuronautix controls the W3ID redirect configuration.
2. Versioned object URIs resolve without relying on a mutable branch.
3. Content negotiation provides human-readable HTML and a machine-readable
   representation where available.
4. Redirect behavior has an automated availability check.

Changing the namespace status is a release decision. It does not rewrite
compact IDs; aliases are recorded explicitly in `namespace.yaml`.

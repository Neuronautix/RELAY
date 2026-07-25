# RELAY governance

## Status

RELAY is an experimental community specification maintained in the open. The Neuronautix organization currently administers the repository. Governance may be expanded as independent maintainers and domain editors join.

## Roles

**Maintainers** manage releases, repository settings, normative approvals, and compatibility policy.

**Domain editors** review terms, boundaries, and rules within one or more domains.

**Mapping editors** review cross-standard mappings, transformations, and information-loss declarations.

**Contributors** propose and review changes through issues and pull requests.

## Decision process

1. New semantics or breaking changes begin with an issue.
2. The proposal identifies affected objects, use cases, alternatives, and migration impact.
3. A pull request provides canonical descriptors, normative rules, documentation, and tests.
4. At least one maintainer and, when available, one relevant domain or mapping editor review the change.
5. The merge decision and unresolved uncertainty are recorded in the pull request.

Maintainers may merge non-semantic corrections directly. Stable semantics must not change without a versioned proposal and migration note.

## Maturity progression

Objects progress independently through:

```text
proposal → experimental → candidate → stable
```

They may later become `deprecated` or `withdrawn`. Promotion requires documented evidence, examples, validation, and review appropriate to the object.

## Compatibility

* Labels and documentation may improve without changing an identifier when meaning is preserved.
* A semantic broadening, narrowing, or redefinition requires a new version and explicit migration guidance.
* Stable rule identifiers are never reassigned to a different requirement.
* Profiles may constrain Core semantics but may not redefine them.
* Mappings are version-pinned and reviewed independently from source and target standards.

## Conflicts of interest and provenance

Reviewers should disclose material involvement in a vendor system, standard, or implementation when reviewing a mapping or requirement that directly affects it. Decisions should preserve the provenance of proposals, evidence, and dissent.

## License decision

The repository must select and document licenses for specification text, machine-readable metadata, examples, and software before the first candidate release. Until then, no license is implied.

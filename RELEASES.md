# RELAY release procedure

RELAY repository releases snapshot the specification, examples, and tooling.
`release.yaml` is the source of truth for the repository snapshot version and
maturity. `relay.lock.yaml` records the exact object graph and source digests
for that snapshot. Repository versions do not replace the independent versions
carried by Terms, Domains, Profiles, Packages, Mappings, and Conformance Rules.

## Version and tag convention

Repository releases use Semantic Versioning and an immutable annotated tag:

```text
vMAJOR.MINOR.PATCH
```

The only supported prerelease suffixes are `-alpha.N`, `-beta.N`, and `-rc.N`,
where `N` starts at 1. Examples are `v0.2.0-alpha.1` and `v1.0.0-rc.1`.

While RELAY remains experimental, repository versions stay below `1.0.0`.
Reaching `1.0.0` means the maintainers have declared the repository-level
contracts stable; it does not automatically promote every RELAY object.

Repository release maturity is `development`, `proposal`, `experimental`,
`candidate`, or `stable`. `development` identifies the untagged working
snapshot and must not be published. Proposal and experimental GitHub Releases
must be marked as prereleases; a candidate may also be marked as a prerelease.

Tags are never moved or reused. A correction to a published release receives a
new version.

## Release gate

Before tagging, the release owner must:

- confirm the scope and maturity claims against [ROADMAP.md](ROADMAP.md);
- resolve or explicitly defer release-blocking issues;
- verify that all normative changes have stable rule identifiers, tests,
  compatibility notes, and the required review;
- confirm third-party material and notices are compatible with the MIT License;
- update the version and maturity in `release.yaml`;
- update canonical object versions where their meaning changed, then run
  `python scripts/validate_release.py --write` to regenerate `relay.lock.yaml`;
- update `CHANGELOG.md`, replacing relevant Unreleased entries with
  `## [VERSION] - YYYY-MM-DD`;
- synchronize `version` and `date-released` in `CITATION.cff` for the citable
  release; this is citation metadata rather than version authority, and a DOI
  is added only when it has actually been assigned or reserved;
- run `ruff check relay scripts schemas tests`,
  `python schemas/generate.py --check`,
  `python scripts/validate_repository.py`, and `python scripts/validate_release.py`,
  followed by
  `python -m unittest discover -s tests -p "test_*.py"`;
- confirm the main-branch validation workflow succeeds on the release commit;
- obtain the review required by [GOVERNANCE.md](GOVERNANCE.md).

Candidate and stable releases additionally require the release gate in
[ROADMAP.md](ROADMAP.md). An experimental release must be described as
experimental in its release notes.

## Tagging and packaging

From an up-to-date, clean `main` branch:

```text
git tag -s vVERSION -m "RELAY vVERSION"
git push origin vVERSION
```

Use a signed annotated tag when the release owner has a configured signing key;
otherwise use `git tag -a` and record that the tag is unsigned in the release
notes.

Pushing a correctly formatted tag runs the release-artifact workflow. The
workflow repeats validation, requires the tag, `release.yaml`, release lock,
and changelog metadata to agree, and creates source archives plus `SHA256SUMS`
as a short-lived workflow artifact. It deliberately does not publish a GitHub
Release.

After the workflow succeeds:

1. Download and verify the generated archives and checksums.
2. Create a GitHub Release for the existing tag, marking prereleases and all
   pre-`1.0.0` releases accurately.
3. Attach the generated archives, `relay.lock.yaml`, and `SHA256SUMS`.
4. Copy the changelog entry into the release notes and describe known
   limitations and migration requirements.
5. If archival integration is configured, confirm the deposit completed before
   citing its identifier.

## Archival identifiers and DOI

GitHub Releases are distribution records, not a preservation guarantee.
Neuronautix should connect the repository to a preservation service such as
Zenodo before the first release intended for citation. This is an organization
administrator action and is not performed by repository workflows.

For an archival deposit:

- upload the exact release archives and checksums generated from the tag;
- use the repository release version and release date in the deposit metadata;
- retain both the version-specific DOI and, when provided, the concept DOI;
- cite the version DOI for reproducible use of one release;
- use the concept DOI only when referring to RELAY across all versions;
- record the assigned version DOI in `CITATION.cff` as `doi`;
- record the concept DOI in `CITATION.cff` under `identifiers`, with a
  description that distinguishes it from the version DOI;
- add identifiers only after assignment or reservation—never add illustrative
  or placeholder DOI values.

If a DOI is assigned only after publication, update the default branch and the
release description with the real identifier. Do not move the release tag or
alter an archived payload to retrofit metadata; include the identifier in the
next immutable release snapshot.

## Recovery

If validation fails after a tag is pushed, do not publish a release for that
tag. Diagnose the failure, make a normal corrective commit, and create a new
tag. If a published release is later found defective, preserve it, document
the issue prominently, and publish a corrected patch release.

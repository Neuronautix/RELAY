# RELAY tooling

**Status:** experimental

The `relay-metadata` Python distribution provides the `relay` command. Install
the current checkout with:

```text
python -m pip install .
```

## Repository validation

```text
relay validate-repository .
relay validate-repository . --format json --output relay-report.json
```

JSON reports include stable diagnostic categories, exact paths, evidence, and
remediation guidance. They distinguish repository validity from scientific or
FAIR certification.

## Package integrity

Build a deterministic manifest for explicitly selected immutable files:

```text
relay build-manifest crate-root data/results.csv metadata/relay-core.json \
  --related-entity urn:uuid:22222222-2222-4222-8222-222222222222
relay verify-package crate-root
```

The builder refuses files outside the crate root, duplicate selections,
self-inventory, missing files, and accidental replacement unless `--force` is
given. It is an integrity-manifest builder, not yet a complete RO-Crate builder.

## Profile migration planning

```text
relay profile-diff profile-0.1.yaml profile-0.2.yaml
relay profile-diff profile-0.1.yaml profile-0.2.yaml --format json
```

The diff classifies requiredness changes, Domain and Package changes, identifies
potentially breaking transitions, and emits migration guidance. Conditions are
reported structurally; the tool does not attempt to interpret free-text
scientific conditions.

## GitHub Action

Use the repository's root `action.yml` from another workflow:

```yaml
- uses: Neuronautix/RELAY@<pinned-release>
  with:
    path: .
    report: relay-validation-report.json
```

Pin a released tag or commit rather than `main`. Upload the report with
`actions/upload-artifact` when it should be retained.

## Exit codes

* `0` — validation passed or no breaking Profile change was found;
* `1` — validation failed or a breaking Profile change was found;
* `2` — invalid input, unreadable files, or command usage error.

Run `relay capabilities` for an honest machine-readable boundary between
implemented and roadmap capabilities.

# Security policy

## Supported versions

RELAY is currently an experimental specification without a stable release.
Security and integrity fixes are applied to the latest revision on the
`main` branch.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or a flaw that could
compromise research-package integrity.

Report it privately through a
[GitHub security advisory](https://github.com/Neuronautix/RELAY/security/advisories/new).
Include the affected revision, a minimal reproduction, the expected impact,
and any suggested mitigation. The maintainers will acknowledge actionable
reports, coordinate a fix, and credit reporters who wish to be named.

Ordinary validation defects that do not create a confidentiality, integrity,
or availability risk can use the public defect issue template.

## Scope

Security reports may cover the repository validator, dependency and workflow
risks, malicious or unexpectedly expensive input, checksum or package-integrity
handling, and misleading conformance results. RELAY conformance does not certify
the security of a laboratory system or dataset.

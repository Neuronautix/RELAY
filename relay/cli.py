"""Command-line interface for RELAY tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from relay.package_validation import build_manifest, verify_package
from relay.profile_diff import compare_profiles
from relay.reporting import render_repository_text, repository_report
from relay.validation import validate_repository


CAPABILITIES = {
    "repository_validation": "available",
    "explainable_json_reports": "available",
    "package_manifest_integrity": "available",
    "profile_diff_and_migration": "available",
    "package_manifest_builder": "available",
    "full_ro_crate_builder": "planned",
    "isa_round_trip_translation": "blocked_pending_reviewed_mappings",
    "research_design_linting": "blocked_pending_operational_terms",
    "provenance_graph_ui": "planned",
}


def _write_output(payload: dict[str, Any], output_format: str, output: Path | None) -> None:
    if output_format == "json":
        rendered = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    elif payload["report_type"] == "relay.repository-validation":
        rendered = render_repository_text(payload) + "\n"
    else:
        lines = [
            f"{payload['report_type']}: {payload.get('outcome', payload.get('compatibility'))}",
            f"Summary: {json.dumps(payload['summary'], sort_keys=True)}",
        ]
        for diagnostic in payload.get("diagnostics", []):
            lines.append(
                f"- [{diagnostic['code']}] {diagnostic['path']}: {diagnostic['message']}"
            )
            lines.append(f"  Remediation: {diagnostic['remediation']}")
        for change in payload.get("changes", []):
            lines.append(
                f"- [{change['severity']}] {change['subject']} {change['identifier']}: "
                f"{change['before']} -> {change['after']}"
            )
            lines.append(f"  Migration: {change['migration']}")
        rendered = "\n".join(lines) + "\n"
    if output is None:
        sys.stdout.write(rendered)
    else:
        output.write_text(rendered, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="relay",
        description="Validate and evolve RELAY metadata specifications and packages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    repository = subparsers.add_parser(
        "validate-repository",
        help="Validate canonical descriptors, references, examples, and integrity metadata.",
    )
    repository.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    repository.add_argument("--format", choices=["text", "json"], default="text")
    repository.add_argument("--output", type=Path)

    package = subparsers.add_parser(
        "verify-package",
        help="Verify a RELAY package manifest and its files.",
    )
    package.add_argument("path", type=Path)
    package.add_argument("--format", choices=["text", "json"], default="text")
    package.add_argument("--output", type=Path)

    manifest = subparsers.add_parser(
        "build-manifest",
        help="Build a deterministic SHA-256 inventory for selected package files.",
    )
    manifest.add_argument("crate_root", type=Path)
    manifest.add_argument("files", nargs="+", type=Path)
    manifest.add_argument("--related-entity", required=True)
    manifest.add_argument("--content-role", default="payload")
    manifest.add_argument("--output", type=Path)
    manifest.add_argument("--force", action="store_true")

    profile = subparsers.add_parser(
        "profile-diff",
        help="Compare Profile requiredness and emit migration guidance.",
    )
    profile.add_argument("before", type=Path)
    profile.add_argument("after", type=Path)
    profile.add_argument("--format", choices=["text", "json"], default="text")
    profile.add_argument("--output", type=Path)

    capability = subparsers.add_parser(
        "capabilities",
        help="Show implemented features and explicit capability boundaries.",
    )
    capability.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-repository":
            report = repository_report(args.root, validate_repository(args.root))
            _write_output(report, args.format, args.output)
            return 0 if report["outcome"] == "pass" else 1
        if args.command == "verify-package":
            report = verify_package(args.path)
            _write_output(report, args.format, args.output)
            return 0 if report["outcome"] == "pass" else 1
        if args.command == "build-manifest":
            output = build_manifest(
                args.crate_root,
                args.files,
                args.related_entity,
                output=args.output,
                content_role=args.content_role,
                force=args.force,
            )
            print(output)
            return 0
        if args.command == "profile-diff":
            report = compare_profiles(args.before, args.after)
            _write_output(report, args.format, args.output)
            return 0 if report["compatibility"] == "compatible" else 1
        if args.command == "capabilities":
            if args.format == "json":
                sys.stdout.write(json.dumps(CAPABILITIES, indent=2) + "\n")
            else:
                for capability, status in CAPABILITIES.items():
                    sys.stdout.write(f"{capability}: {status}\n")
            return 0
    except (OSError, TypeError, ValueError) as exc:
        print(f"relay: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

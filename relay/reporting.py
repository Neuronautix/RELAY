"""Structured, explainable diagnostics for RELAY tooling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from relay.validation import Problem


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str
    remediation: str


DIAGNOSTIC_PATTERNS = [
    ("duplicate", "RELAY-DUPLICATE", "Remove or rename the duplicate declaration."),
    ("unknown", "RELAY-UNKNOWN-REFERENCE", "Declare the referenced object or correct the identifier."),
    ("missing required key", "RELAY-MISSING-FIELD", "Add the required field using the relevant template."),
    ("must be a list", "RELAY-INVALID-SHAPE", "Use a YAML sequence for this field."),
    ("must be a mapping", "RELAY-INVALID-SHAPE", "Use a YAML or JSON object for this field."),
    ("semantic version", "RELAY-INVALID-VERSION", "Use a valid SemVer 2.0 version."),
    ("sha256 mismatch", "RELAY-INTEGRITY", "Regenerate the manifest after finalizing file bytes."),
    ("byte_size mismatch", "RELAY-INTEGRITY", "Regenerate the manifest after finalizing file bytes."),
    ("invalid json", "RELAY-INVALID-JSON", "Use strict JSON with finite numbers and unique object keys."),
    ("invalid yaml", "RELAY-INVALID-YAML", "Correct the YAML syntax and remove duplicate keys."),
    ("cyclic", "RELAY-DEPENDENCY-CYCLE", "Remove a dependency edge to restore an acyclic graph."),
]


def explain_problem(problem: Problem, root: Path) -> Diagnostic:
    message_lower = problem.message.lower()
    code = "RELAY-REPOSITORY"
    remediation = "Review the descriptor contract and correct the reported value."
    for pattern, candidate_code, candidate_remediation in DIAGNOSTIC_PATTERNS:
        if pattern in message_lower:
            code = candidate_code
            remediation = candidate_remediation
            break
    try:
        display_path = str(problem.path.resolve().relative_to(root.resolve()))
    except ValueError:
        display_path = str(problem.path)
    return Diagnostic(code, display_path.replace("\\", "/"), problem.message, remediation)


def repository_report(root: Path, problems: Iterable[Problem]) -> dict[str, Any]:
    diagnostics = [explain_problem(problem, root) for problem in problems]
    return {
        "report_type": "relay.repository-validation",
        "report_version": "1.0",
        "root": str(root.resolve()),
        "outcome": "fail" if diagnostics else "pass",
        "summary": {
            "problems": len(diagnostics),
            "errors": len(diagnostics),
            "warnings": 0,
        },
        "diagnostics": [asdict(item) for item in diagnostics],
    }


def render_repository_text(report: dict[str, Any]) -> str:
    if report["outcome"] == "pass":
        return "RELAY repository validation passed."
    lines = [
        f"RELAY repository validation failed with {report['summary']['problems']} problem(s):"
    ]
    for item in report["diagnostics"]:
        lines.extend(
            [
                f"- [{item['code']}] {item['path']}: {item['message']}",
                f"  Remediation: {item['remediation']}",
            ]
        )
    return "\n".join(lines)

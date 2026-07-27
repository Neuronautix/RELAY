#!/usr/bin/env python3
"""Compatibility entry point for RELAY repository validation."""

from pathlib import Path
import sys


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from relay.validation import Problem, main, validate_repository

__all__ = ["Problem", "main", "validate_repository"]


if __name__ == "__main__":
    raise SystemExit(main())

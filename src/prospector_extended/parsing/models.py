"""Pydantic models for parsing tool outputs.

These models are used at runtime for validation and at build-time for
schema generation. The fingerprints are used for drift detection.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, field_validator

# =============================================================================
# MYPY OUTPUT MODELS
# =============================================================================


class MypyJsonOutput(BaseModel):
    """Official mypy JSON output schema (mypy 1.13+).

    The JSON output format is documented in mypy PR #11396.
    """

    file: str
    line: int  # 1-indexed
    column: int  # 0-indexed
    message: str
    hint: str | None = None
    code: str | None = None
    severity: Literal["error", "note"]

    @field_validator("line", mode="before")
    @classmethod
    def ensure_positive_line(cls, v: int) -> int:
        """Ensure line number is at least 1."""
        return max(1, v) if v else 1

    @field_validator("column", mode="before")
    @classmethod
    def ensure_non_negative_column(cls, v: int) -> int:
        """Ensure column is at least 0."""
        return max(0, v) if v else 0


# Known fingerprint for mypy schema - update when schema changes intentionally
# This is computed from the JSON Schema representation of MypyJsonOutput
MYPY_SCHEMA_FINGERPRINT = "da92ebf2ae80d1f9"


def get_mypy_json_schema() -> dict[str, object]:
    """Get the JSON Schema for mypy output."""
    return MypyJsonOutput.model_json_schema()


# =============================================================================
# MYPY TEXT FALLBACK PARSER
# =============================================================================

# Regex for mypy text output: file:line:col: severity: message [code]
# Or: file:line: severity: message [code] (without column)
_MYPY_TEXT_PATTERN = re.compile(
    r"^(.+?):(\d+):(?:(\d+):)?\s*(error|warning|note):\s*(.+?)(?:\s*\[([^\]]+)\])?$"
)


def parse_mypy_text_line(line: str) -> MypyJsonOutput | None:
    """Parse mypy's text output format as fallback.

    Mypy outputs text format for syntax errors even with --output json.
    This parser handles those cases.

    Args:
        line: A line of mypy output.

    Returns:
        Parsed MypyJsonOutput if line matches, None otherwise.
    """
    # Skip summary and status lines
    if line.startswith(("Found ", "Success:", "mypy:", "error:", "note:")):
        return None

    if not (match := _MYPY_TEXT_PATTERN.match(line)):
        return None

    # Map severity to valid Literal values
    # Regex captures: error, warning, note
    # Model accepts: error, note (warning maps to error)
    severity_str = match.group(4)
    severity: Literal["error", "note"] = "note" if severity_str == "note" else "error"

    return MypyJsonOutput(
        file=match.group(1),
        line=int(match.group(2)),
        column=int(match.group(3) or 0),
        message=match.group(5),
        hint=None,
        code=match.group(6),
        severity=severity,
    )


# =============================================================================
# COMBINED MYPY PARSER
# =============================================================================


def parse_mypy_output(stdout: str, stderr: str = "") -> list[MypyJsonOutput]:
    """Parse mypy output into validated MypyJsonOutput objects.

    Handles:
    - JSON output (--output json)
    - Text output fallback (syntax errors bypass JSON formatter)
    - stderr messages (file not found, etc.)

    Args:
        stdout: The stdout from mypy.
        stderr: The stderr from mypy.

    Returns:
        List of parsed MypyJsonOutput objects.
    """
    results: list[MypyJsonOutput] = []

    for line in stdout.strip().split("\n"):
        if not line:
            continue

        # JSON path (preferred)
        if line.startswith("{"):
            try:
                data = json.loads(line)
                results.append(MypyJsonOutput.model_validate(data))
                continue
            except (json.JSONDecodeError, ValueError):
                pass  # Fall through to text parser

        # Text path (fallback)
        if parsed := parse_mypy_text_line(line):
            results.append(parsed)

    # Handle stderr (mypy-level errors)
    for line in stderr.strip().split("\n"):
        if not line:
            continue
        if line.startswith("mypy:") or line.startswith("error:"):
            results.append(
                MypyJsonOutput(
                    file="",
                    line=1,
                    column=0,
                    message=line,
                    code="mypy-error",
                    severity="error",
                )
            )

    return results

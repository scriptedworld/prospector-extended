"""Vulture whitelist for false positives.

This file references code that vulture incorrectly flags as unused.
Run vulture with: vulture src/ vulture_whitelist.py

Items listed here are used in public API (dataclass fields, Pydantic model
attributes) but appear unused to static analysis.
"""

from prospector_extended.parsing.models import MypyJsonOutput
from prospector_extended.parsing.registry import ValidationFailure

# Pydantic model fields used in public API
MypyJsonOutput.column
MypyJsonOutput.line
MypyJsonOutput.message
MypyJsonOutput.severity

# Dataclass fields used in public API
ValidationFailure.schema_name
ValidationFailure.raw
ValidationFailure.reason

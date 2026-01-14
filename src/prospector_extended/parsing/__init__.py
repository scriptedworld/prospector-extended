"""Parsing infrastructure for tool output.

This module provides:
- Type registry for polymorphic JSON parsing
- Pydantic models for tool outputs
- Text fallback parsers for non-JSON output
"""

from prospector_extended.parsing.models import (
    MYPY_SCHEMA_FINGERPRINT,
    MypyJsonOutput,
    get_mypy_json_schema,
    parse_mypy_output,
    parse_mypy_text_line,
)
from prospector_extended.parsing.registry import (
    AlwaysMatcher,
    DiscriminatorMatcher,
    ParsedRecord,
    ParseResult,
    PredicateMatcher,
    RegisteredSchema,
    RequiredFieldsMatcher,
    SchemaMatcher,
    TypeRegistry,
    TypeTagMatcher,
    UnparsedLine,
    ValidationFailure,
    compute_fingerprint,
    schema_from_fields,
)

__all__ = [
    # Registry
    "TypeRegistry",
    "RegisteredSchema",
    "ParseResult",
    "ParsedRecord",
    "UnparsedLine",
    "ValidationFailure",
    # Matchers
    "SchemaMatcher",
    "TypeTagMatcher",
    "DiscriminatorMatcher",
    "RequiredFieldsMatcher",
    "PredicateMatcher",
    "AlwaysMatcher",
    # Utilities
    "compute_fingerprint",
    "schema_from_fields",
    # Mypy models
    "MypyJsonOutput",
    "MYPY_SCHEMA_FINGERPRINT",
    "get_mypy_json_schema",
    "parse_mypy_output",
    "parse_mypy_text_line",
]

"""Type Registry for JSON Line Parsing.

Provides a flexible registry for parsing JSON lines with support for:
- Explicit type tags ({"$type": "Error", ...})
- Discriminator fields ({"severity": "error", ...})
- Structural matching (required fields)
- Custom predicate matchers

Inspired by cattrs structure hooks, YAML tags, and Pydantic discriminated unions.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

# =============================================================================
# SCHEMA DEFINITION
# =============================================================================


@dataclass
class RegisteredSchema:
    """A schema registered with the type registry."""

    name: str
    schema: dict[str, Any]
    fingerprint: str
    matcher: SchemaMatcher | None = None

    _validator: Draft7Validator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the JSON Schema validator."""
        self._validator = Draft7Validator(self.schema)

    def validate(self, data: dict[str, Any]) -> list[str]:
        """Return validation errors (empty list means valid)."""
        return [e.message for e in self._validator.iter_errors(data)]

    def is_valid(self, data: dict[str, Any]) -> bool:
        """Quick check if data validates against this schema."""
        return bool(self._validator.is_valid(data))


# =============================================================================
# MATCHERS
# =============================================================================


class SchemaMatcher(ABC):
    """Determines if a schema should be tried for given data."""

    @abstractmethod
    def matches(self, data: dict[str, Any]) -> bool:
        """Return True if this schema should be tried."""
        ...

    @abstractmethod
    def priority(self) -> int:
        """Higher priority matchers are tried first."""
        ...


@dataclass
class TypeTagMatcher(SchemaMatcher):
    """Match by explicit type tag field (e.g., {"$type": "ErrorRecord"})."""

    tag_field: str  # e.g., "$type", "__type__", "recordType"
    tag_value: str  # e.g., "ErrorRecord"

    def matches(self, data: dict[str, Any]) -> bool:
        """Check if data has the expected type tag."""
        return bool(data.get(self.tag_field) == self.tag_value)

    def priority(self) -> int:
        """Highest priority - explicit tags are definitive."""
        return 100


@dataclass
class DiscriminatorMatcher(SchemaMatcher):
    """Match by discriminator field value (e.g., {"severity": "error"})."""

    field_name: str
    value: Any

    def matches(self, data: dict[str, Any]) -> bool:
        """Check if data has the expected discriminator value."""
        return bool(data.get(self.field_name) == self.value)

    def priority(self) -> int:
        """High priority - discriminators are fairly definitive."""
        return 80


@dataclass
class RequiredFieldsMatcher(SchemaMatcher):
    """Match by presence of required fields."""

    required_fields: frozenset[str]
    forbidden_fields: frozenset[str] = field(default_factory=frozenset)

    def matches(self, data: dict[str, Any]) -> bool:
        """Check if data has all required fields and no forbidden fields."""
        has_required = all(f in data for f in self.required_fields)
        has_forbidden = any(f in data for f in self.forbidden_fields)
        return has_required and not has_forbidden

    def priority(self) -> int:
        """Medium priority - structural matching."""
        return 50


@dataclass
class PredicateMatcher(SchemaMatcher):
    """Match by custom predicate function."""

    predicate: Callable[[dict[str, Any]], bool]
    _priority: int = 60

    def matches(self, data: dict[str, Any]) -> bool:
        """Check if predicate returns True."""
        return self.predicate(data)

    def priority(self) -> int:
        """Return configured priority."""
        return self._priority


class AlwaysMatcher(SchemaMatcher):
    """Always matches - used as fallback."""

    def matches(self, data: dict[str, Any]) -> bool:  # noqa: ARG002 - interface requires parameter
        """Always returns True."""
        return True

    def priority(self) -> int:
        """Lowest priority - try last."""
        return 0


# =============================================================================
# PARSE RESULTS
# =============================================================================


@dataclass
class ParsedRecord:
    """Successfully parsed and validated record."""

    schema_name: str
    data: dict[str, Any]
    raw: str


@dataclass
class UnparsedLine:
    """Line that couldn't be parsed as JSON."""

    raw: str
    reason: str


@dataclass
class ValidationFailure:
    """JSON parsed but failed validation against all schemas."""

    data: dict[str, Any]
    raw: str
    attempted: list[tuple[str, list[str]]]  # [(schema_name, errors), ...]


ParseResult = ParsedRecord | UnparsedLine | ValidationFailure


# =============================================================================
# TYPE REGISTRY
# =============================================================================


class TypeRegistry:
    """Registry of schemas with smart dispatch.

    Usage:
        registry = TypeRegistry()

        # Register with discriminator
        registry.register(
            "MypyError",
            error_schema,
            DiscriminatorMatcher("severity", "error")
        )

        # Register with structural matching
        registry.register(
            "MypyNote",
            note_schema,
            RequiredFieldsMatcher(frozenset({"file", "line", "message"}))
        )

        # Parse output
        for result in registry.parse_output(stdout):
            if isinstance(result, ParsedRecord):
                print(f"Parsed: {result.schema_name}")
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._schemas: list[RegisteredSchema] = []
        self._by_name: dict[str, RegisteredSchema] = {}

    def register(
        self,
        name: str,
        schema: dict[str, Any],
        matcher: SchemaMatcher | None = None,
        fingerprint: str | None = None,
    ) -> TypeRegistry:
        """Register a schema. Returns self for chaining."""
        if fingerprint is None:
            fingerprint = compute_fingerprint(schema)

        registered = RegisteredSchema(
            name=name,
            schema=schema,
            fingerprint=fingerprint,
            matcher=matcher,
        )

        self._schemas.append(registered)
        self._by_name[name] = registered

        # Keep sorted by matcher priority (highest first)
        self._schemas.sort(key=lambda s: -(s.matcher.priority() if s.matcher else 0))

        return self

    def get_schema(self, name: str) -> RegisteredSchema | None:
        """Get a schema by name."""
        return self._by_name.get(name)

    def parse_line(self, line: str) -> ParseResult:
        """Parse a single line of output."""
        line = line.strip()
        if not line:
            return UnparsedLine(raw=line, reason="empty")

        # Fast path: JSON always starts with {
        if not line.startswith("{"):
            return UnparsedLine(raw=line, reason="not JSON")

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            return UnparsedLine(raw=line, reason=f"JSON decode error: {e}")

        # Try schemas in priority order
        attempted: list[tuple[str, list[str]]] = []

        for schema in self._schemas:
            # If schema has a matcher, check it first
            if schema.matcher and not schema.matcher.matches(data):
                continue

            # Validate against schema
            errors = schema.validate(data)
            if not errors:
                return ParsedRecord(schema_name=schema.name, data=data, raw=line)

            attempted.append((schema.name, errors))

        return ValidationFailure(data=data, raw=line, attempted=attempted)

    def parse_output(self, output: str) -> list[ParseResult]:
        """Parse complete output, returning all results."""
        return [self.parse_line(line) for line in output.strip().split("\n") if line.strip()]

    def fingerprints(self) -> dict[str, str]:
        """Get all fingerprints for drift detection."""
        return {s.name: s.fingerprint for s in self._schemas}

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry (schemas only, not matchers)."""
        return {
            "schemas": [
                {
                    "name": s.name,
                    "schema": s.schema,
                    "fingerprint": s.fingerprint,
                }
                for s in self._schemas
            ]
        }

    def save(self, path: Path) -> None:
        """Save registry to file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> TypeRegistry:
        """Load registry from file (matchers must be re-registered)."""
        data = json.loads(path.read_text())
        registry = cls()
        for s in data["schemas"]:
            registry.register(s["name"], s["schema"], fingerprint=s["fingerprint"])
        return registry


# =============================================================================
# UTILITIES
# =============================================================================


def compute_fingerprint(schema: dict[str, Any]) -> str:
    """Generate fingerprint for drift detection."""
    content = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def schema_from_fields(
    required: dict[str, str],
    optional: dict[str, str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Build JSON Schema from field definitions.

    Types: "string", "integer", "number", "boolean", "null", "array", "object"
    Use "string|null" for nullable strings.
    Use "enum:a,b,c" for enumerations.

    Args:
        required: Dict of required field names to JSON types.
        optional: Dict of optional field names to JSON types.
        title: Optional schema title.

    Returns:
        JSON Schema dict.
    """
    properties: dict[str, Any] = {}
    required_fields: list[str] = []

    def parse_type(type_str: str) -> dict[str, Any]:
        """Parse type string to JSON Schema type definition.

        Args:
            type_str: Type string like "string", "string|null", "enum:a,b,c".

        Returns:
            JSON Schema type definition dict.
        """
        if "|" in type_str:
            types = [t.strip() for t in type_str.split("|")]
            return {"anyOf": [{"type": t} for t in types]}
        if type_str.startswith("enum:"):
            values = [v.strip() for v in type_str[5:].split(",")]
            return {"type": "string", "enum": values}
        return {"type": type_str}

    for name, type_str in required.items():
        properties[name] = parse_type(type_str)
        required_fields.append(name)

    if optional:
        for name, type_str in optional.items():
            properties[name] = parse_type(type_str)

    schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required_fields,
    }

    if title:
        schema["title"] = title

    return schema

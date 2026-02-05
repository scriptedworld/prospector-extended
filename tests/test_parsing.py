"""Tests for the parsing module."""

from __future__ import annotations

import json

import pytest

from prospector_extended.parsing import (
    AlwaysMatcher,
    DiscriminatorMatcher,
    MypyJsonOutput,
    ParsedRecord,
    RequiredFieldsMatcher,
    TypeRegistry,
    TypeTagMatcher,
    UnparsedLine,
    ValidationFailure,
    compute_fingerprint,
    parse_mypy_output,
    parse_mypy_text_line,
    schema_from_fields,
)


class TestMypyJsonOutput:
    """Tests for the MypyJsonOutput model."""

    def test_valid_error(self) -> None:
        """Test parsing a valid mypy error."""
        data = {
            "file": "test.py",
            "line": 10,
            "column": 5,
            "message": "Incompatible return type",
            "hint": None,
            "code": "return-value",
            "severity": "error",
        }
        result = MypyJsonOutput.model_validate(data)
        assert result.file == "test.py"
        assert result.line == 10
        assert result.column == 5
        assert result.code == "return-value"
        assert result.severity == "error"

    def test_valid_note(self) -> None:
        """Test parsing a valid mypy note."""
        data = {
            "file": "test.py",
            "line": 10,
            "column": 0,
            "message": "Expected type here",
            "severity": "note",
        }
        result = MypyJsonOutput.model_validate(data)
        assert result.severity == "note"

    def test_line_validation(self) -> None:
        """Test that line numbers are at least 1."""
        data = {
            "file": "test.py",
            "line": 0,
            "column": 0,
            "message": "Error",
            "severity": "error",
        }
        result = MypyJsonOutput.model_validate(data)
        assert result.line == 1

    def test_column_validation(self) -> None:
        """Test that column numbers are at least 0."""
        data = {
            "file": "test.py",
            "line": 1,
            "column": -5,
            "message": "Error",
            "severity": "error",
        }
        result = MypyJsonOutput.model_validate(data)
        assert result.column == 0


class TestMypyTextParsing:
    """Tests for mypy text output parsing."""

    def test_parse_error_with_code(self) -> None:
        """Test parsing text error with code."""
        line = 'test.py:10:5: error: Incompatible types [arg-type]'
        result = parse_mypy_text_line(line)
        assert result is not None
        assert result.file == "test.py"
        assert result.line == 10
        assert result.column == 5
        assert result.code == "arg-type"

    def test_parse_error_without_column(self) -> None:
        """Test parsing text error without column."""
        line = 'test.py:10: error: Missing return'
        result = parse_mypy_text_line(line)
        assert result is not None
        assert result.file == "test.py"
        assert result.line == 10
        assert result.column == 0

    def test_skip_summary_lines(self) -> None:
        """Test that summary lines are skipped."""
        assert parse_mypy_text_line("Found 3 errors in 1 file") is None
        assert parse_mypy_text_line("Success: no issues found") is None
        assert parse_mypy_text_line("mypy: error: ...") is None


class TestParseMypyOutput:
    """Tests for combined mypy output parsing."""

    def test_json_output(self) -> None:
        """Test parsing JSON output."""
        stdout = '{"file": "test.py", "line": 1, "column": 0, "message": "Error", "severity": "error"}\n'
        results = parse_mypy_output(stdout)
        assert len(results) == 1
        assert results[0].file == "test.py"

    def test_mixed_output(self) -> None:
        """Test parsing mixed JSON and text output."""
        stdout = """{"file": "a.py", "line": 1, "column": 0, "message": "JSON error", "severity": "error"}
b.py:5:10: error: Text error [arg-type]
Found 2 errors"""
        results = parse_mypy_output(stdout)
        # Should have 2 errors (JSON and text), summary line skipped
        assert len(results) == 2

    def test_stderr_handling(self) -> None:
        """Test that stderr errors are captured."""
        stdout = ""
        stderr = "mypy: error: No files to check"
        results = parse_mypy_output(stdout, stderr)
        assert len(results) == 1
        assert results[0].code == "mypy-error"


class TestTypeRegistry:
    """Tests for the TypeRegistry."""

    def test_register_and_parse(self) -> None:
        """Test registering a schema and parsing."""
        schema = schema_from_fields(
            required={"name": "string", "value": "integer"},
            title="TestRecord",
        )
        registry = TypeRegistry().register("TestRecord", schema)

        line = '{"name": "test", "value": 42}'
        result = registry.parse_line(line)

        assert isinstance(result, ParsedRecord)
        assert result.schema_name == "TestRecord"
        assert result.data["name"] == "test"

    def test_discriminator_matching(self) -> None:
        """Test discriminator-based schema matching."""
        error_schema = schema_from_fields(
            required={"type": "string", "message": "string"},
            title="Error",
        )
        warning_schema = schema_from_fields(
            required={"type": "string", "message": "string"},
            title="Warning",
        )

        registry = TypeRegistry()
        registry.register("Error", error_schema, DiscriminatorMatcher("type", "error"))
        registry.register("Warning", warning_schema, DiscriminatorMatcher("type", "warning"))

        error_result = registry.parse_line('{"type": "error", "message": "oops"}')
        warning_result = registry.parse_line('{"type": "warning", "message": "careful"}')

        assert isinstance(error_result, ParsedRecord)
        assert error_result.schema_name == "Error"
        assert isinstance(warning_result, ParsedRecord)
        assert warning_result.schema_name == "Warning"

    def test_unparsed_line(self) -> None:
        """Test handling of non-JSON lines."""
        registry = TypeRegistry()
        result = registry.parse_line("not json at all")
        assert isinstance(result, UnparsedLine)
        assert result.reason == "not JSON"

    def test_validation_failure(self) -> None:
        """Test handling of invalid JSON."""
        schema = schema_from_fields(required={"required_field": "string"})
        registry = TypeRegistry().register("Test", schema, AlwaysMatcher())

        result = registry.parse_line('{"wrong_field": "value"}')
        assert isinstance(result, ValidationFailure)


class TestMatchers:
    """Tests for schema matchers."""

    def test_type_tag_matcher(self) -> None:
        """Test TypeTagMatcher."""
        matcher = TypeTagMatcher("$type", "ErrorRecord")
        assert matcher.matches({"$type": "ErrorRecord", "data": 123})
        assert not matcher.matches({"$type": "OtherRecord", "data": 123})
        assert not matcher.matches({"data": 123})

    def test_discriminator_matcher(self) -> None:
        """Test DiscriminatorMatcher."""
        matcher = DiscriminatorMatcher("severity", "error")
        assert matcher.matches({"severity": "error", "msg": "test"})
        assert not matcher.matches({"severity": "note", "msg": "test"})

    def test_required_fields_matcher(self) -> None:
        """Test RequiredFieldsMatcher."""
        matcher = RequiredFieldsMatcher(
            required_fields=frozenset({"a", "b"}),
            forbidden_fields=frozenset({"c"}),
        )
        assert matcher.matches({"a": 1, "b": 2})
        assert not matcher.matches({"a": 1})  # Missing b
        assert not matcher.matches({"a": 1, "b": 2, "c": 3})  # Has forbidden c


class TestUtilities:
    """Tests for utility functions."""

    def test_compute_fingerprint(self) -> None:
        """Test fingerprint computation is deterministic."""
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}
        fp1 = compute_fingerprint(schema)
        fp2 = compute_fingerprint(schema)
        assert fp1 == fp2
        assert len(fp1) == 16

    def test_schema_from_fields(self) -> None:
        """Test schema generation from field definitions."""
        schema = schema_from_fields(
            required={"name": "string", "count": "integer"},
            optional={"tag": "string|null"},
            title="TestSchema",
        )
        assert schema["title"] == "TestSchema"
        assert "name" in schema["required"]
        assert "count" in schema["required"]
        assert "tag" not in schema["required"]

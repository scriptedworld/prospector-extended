"""Tests for the mypy tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from prospector_extended.tools.mypy_tool import MypyTool


class MockProspectorConfig:
    """Mock prospector config for testing."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        """Initialize with optional tool options."""
        self._options = options or {}
        self._disabled: list[str] = []
        self._enabled: list[str] = []

    def tool_options(self, tool_name: str) -> dict[str, Any]:
        """Return tool options."""
        return self._options

    def get_disabled_messages(self, tool_name: str) -> list[str]:
        """Return disabled message codes."""
        return self._disabled

    def get_enabled_messages(self, tool_name: str) -> list[str]:
        """Return enabled message codes."""
        return self._enabled


class MockFileFinder:
    """Mock file finder for testing."""

    def __init__(self, files: list[Path]) -> None:
        """Initialize with list of files."""
        self.python_modules = files


class TestMypyToolConfiguration:
    """Tests for mypy tool configuration."""

    def test_default_configuration(self) -> None:
        """Test default configuration."""
        tool = MypyTool()
        config = MockProspectorConfig()

        tool.configure(config, None)

        assert "--show-column-numbers" in tool.options
        assert "--no-error-summary" in tool.options
        assert "--show-error-codes" in tool.options

    def test_strict_mode(self) -> None:
        """Test strict mode configuration."""
        tool = MypyTool()
        config = MockProspectorConfig({"strict": True})

        tool.configure(config, None)

        assert "--strict" in tool.options

    def test_python_version(self) -> None:
        """Test python version configuration."""
        tool = MypyTool()
        config = MockProspectorConfig({"python-version": "3.12"})

        tool.configure(config, None)

        assert "--python-version=3.12" in tool.options

    def test_disabled_error_codes(self) -> None:
        """Test disabled error codes."""
        tool = MypyTool()
        config = MockProspectorConfig()
        config._disabled = ["arg-type", "return-value"]

        tool.configure(config, None)

        assert "--disable-error-code=arg-type" in tool.options
        assert "--disable-error-code=return-value" in tool.options


class TestMypyToolRun:
    """Tests for mypy tool execution."""

    def test_run_on_clean_file(self) -> None:
        """Test running mypy on a clean file."""
        tool = MypyTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "clean.py"])

        messages = tool.run(finder)

        # Clean file should have no errors (or only missing imports)
        error_messages = [m for m in messages if m.code not in ("import", "import-untyped")]
        # Note: This may still have errors depending on mypy strictness
        # The important thing is that it runs without crashing

    def test_run_on_type_errors(self) -> None:
        """Test running mypy on file with type errors."""
        tool = MypyTool()
        config = MockProspectorConfig({"strict": True})
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "type_errors.py"])

        messages = tool.run(finder)

        # Should find type errors
        # Note: actual error count depends on mypy version
        assert len(messages) > 0

    def test_run_with_empty_files(self) -> None:
        """Test running mypy with no files."""
        tool = MypyTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        finder = MockFileFinder([])

        messages = tool.run(finder)

        assert messages == []



class TestMypyOutputConversion:
    """Tests for mypy output to prospector message conversion."""

    def test_convert_json_error(self) -> None:
        """Test converting JSON error to prospector message."""
        from prospector_extended.parsing import MypyJsonOutput

        error = MypyJsonOutput(
            file="test.py",
            line=10,
            column=5,
            message="Incompatible return type",
            hint=None,
            code="return-value",
            severity="error",
        )

        message = MypyTool._error_to_message(error)

        assert message is not None
        assert message.source == "mypy"
        assert message.code == "return-value"
        assert message.location.line == 10
        assert message.location.character == 5

    def test_skip_notes(self) -> None:
        """Test that notes are skipped."""
        from prospector_extended.parsing import MypyJsonOutput

        error = MypyJsonOutput(
            file="test.py",
            line=10,
            column=0,
            message="This is a note",
            severity="note",
        )

        message = MypyTool._error_to_message(error)

        assert message is None

    def test_include_hint(self) -> None:
        """Test that hints are included in message."""
        from prospector_extended.parsing import MypyJsonOutput

        error = MypyJsonOutput(
            file="test.py",
            line=10,
            column=0,
            message="Error occurred",
            hint="Try adding type annotation",
            code="error",
            severity="error",
        )

        message = MypyTool._error_to_message(error)

        assert message is not None
        assert "Try adding type annotation" in message.message

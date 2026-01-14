"""Tests for the complexipy tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from prospector_extended.tools.complexipy_tool import CODE_COMPLEXITY, ComplexipyTool


class MockProspectorConfig:
    """Mock prospector config for testing."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        """Initialize with optional tool options."""
        self._options = options or {}
        self._disabled: list[str] = []

    def tool_options(self, tool_name: str) -> dict[str, Any]:
        """Return tool options."""
        return self._options

    def get_disabled_messages(self, tool_name: str) -> list[str]:
        """Return disabled message codes."""
        return self._disabled


class MockFileFinder:
    """Mock file finder for testing."""

    def __init__(self, files: list[Path]) -> None:
        """Initialize with list of files."""
        self.python_modules = files


class TestComplexipyToolConfiguration:
    """Tests for complexipy tool configuration."""

    def test_default_threshold(self) -> None:
        """Test default complexity threshold."""
        tool = ComplexipyTool()
        config = MockProspectorConfig()

        tool.configure(config, None)

        assert tool.max_complexity == 15

    def test_custom_threshold(self) -> None:
        """Test custom complexity threshold."""
        tool = ComplexipyTool()
        config = MockProspectorConfig({"max-complexity": 10})

        tool.configure(config, None)

        assert tool.max_complexity == 10

    def test_disabled_codes(self) -> None:
        """Test disabled error codes."""
        tool = ComplexipyTool()
        config = MockProspectorConfig()
        config._disabled = [CODE_COMPLEXITY]

        tool.configure(config, None)

        assert CODE_COMPLEXITY in tool.ignore_codes


class TestComplexipyToolRun:
    """Tests for complexipy tool execution."""

    def test_run_on_simple_file(self) -> None:
        """Test running complexipy on a simple file."""
        tool = ComplexipyTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "clean.py"])

        messages = tool.run(finder)

        # Clean file should have low complexity
        assert all(m.code != CODE_COMPLEXITY for m in messages)

    def test_run_on_complex_file(self) -> None:
        """Test running complexipy on a complex file."""
        tool = ComplexipyTool()
        config = MockProspectorConfig({"max-complexity": 5})  # Low threshold
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "high_complexity.py"])

        messages = tool.run(finder)

        # Should find the complex function
        complexity_messages = [m for m in messages if m.code == CODE_COMPLEXITY]
        assert len(complexity_messages) > 0

        # Should mention the function name
        assert any("complex_function" in m.message for m in complexity_messages)

    def test_run_with_empty_files(self) -> None:
        """Test running complexipy with no files."""
        tool = ComplexipyTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        finder = MockFileFinder([])

        messages = tool.run(finder)

        assert messages == []

    def test_threshold_respected(self) -> None:
        """Test that threshold is respected."""
        # High threshold - should find nothing
        tool = ComplexipyTool()
        config = MockProspectorConfig({"max-complexity": 100})
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "high_complexity.py"])

        messages = tool.run(finder)

        complexity_messages = [m for m in messages if m.code == CODE_COMPLEXITY]
        assert len(complexity_messages) == 0

    def test_disabled_code_skipped(self) -> None:
        """Test that disabled codes are skipped."""
        tool = ComplexipyTool()
        config = MockProspectorConfig({"max-complexity": 1})  # Very low threshold
        config._disabled = [CODE_COMPLEXITY]
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "high_complexity.py"])

        messages = tool.run(finder)

        # Should find nothing since code is disabled
        complexity_messages = [m for m in messages if m.code == CODE_COMPLEXITY]
        assert len(complexity_messages) == 0

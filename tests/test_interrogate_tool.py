"""Tests for the interrogate tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from prospector_extended.tools.interrogate_tool import InterrogateTool


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


class TestInterrogateToolConfiguration:
    """Tests for interrogate tool configuration."""

    def test_default_configuration(self) -> None:
        """Test default configuration."""
        tool = InterrogateTool()
        config = MockProspectorConfig()

        tool.configure(config, None)

        assert tool._config_options == {}

    def test_ignore_init_method(self) -> None:
        """Test ignore-init-method option."""
        tool = InterrogateTool()
        config = MockProspectorConfig({"ignore-init-method": True})

        tool.configure(config, None)

        assert tool._config_options.get("ignore_init_method") is True

    def test_ignore_magic(self) -> None:
        """Test ignore-magic option."""
        tool = InterrogateTool()
        config = MockProspectorConfig({"ignore-magic": True})

        tool.configure(config, None)

        assert tool._config_options.get("ignore_magic") is True

    def test_multiple_options(self) -> None:
        """Test multiple options."""
        tool = InterrogateTool()
        config = MockProspectorConfig(
            {
                "ignore-init-method": True,
                "ignore-magic": True,
                "ignore-module": True,
            }
        )

        tool.configure(config, None)

        assert tool._config_options.get("ignore_init_method") is True
        assert tool._config_options.get("ignore_magic") is True
        assert tool._config_options.get("ignore_module") is True


class TestInterrogateToolRun:
    """Tests for interrogate tool execution."""

    def test_run_on_documented_file(self) -> None:
        """Test running interrogate on a well-documented file."""
        tool = InterrogateTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "clean.py"])

        messages = tool.run(finder)

        # Clean file is well-documented
        # May still have module-level docstring missing
        function_messages = [m for m in messages if "function" in m.message.lower()]
        assert len(function_messages) == 0

    def test_run_on_undocumented_file(self) -> None:
        """Test running interrogate on an undocumented file."""
        tool = InterrogateTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "missing_docstrings.py"])

        messages = tool.run(finder)

        # Should find missing docstrings
        assert len(messages) > 0

        # Should include function and class mentions
        codes = [m.code for m in messages]
        assert any(code.startswith("INT") for code in codes)

    def test_run_with_empty_files(self) -> None:
        """Test running interrogate with no files."""
        tool = InterrogateTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        finder = MockFileFinder([])

        messages = tool.run(finder)

        assert messages == []

    def test_ignore_module_docstring(self) -> None:
        """Test ignoring module docstrings."""
        tool = InterrogateTool()
        config = MockProspectorConfig({"ignore-module": True})
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "missing_docstrings.py"])

        messages = tool.run(finder)

        # Should not report missing module docstring
        module_messages = [m for m in messages if m.code == "INT100"]
        assert len(module_messages) == 0

    def test_message_format(self) -> None:
        """Test message format."""
        tool = InterrogateTool()
        config = MockProspectorConfig()
        tool.configure(config, None)

        fixtures_dir = Path(__file__).parent / "fixtures_exempt"
        finder = MockFileFinder([fixtures_dir / "missing_docstrings.py"])

        messages = tool.run(finder)

        # Messages should have proper format
        for msg in messages:
            assert msg.source == "interrogate"
            assert msg.code.startswith("INT")
            assert "Missing docstring" in msg.message
            assert str(msg.location.path).endswith("missing_docstrings.py")

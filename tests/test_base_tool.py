"""Tests for ExtendedToolBase."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from prospector.message import Message

from prospector_extended.tools.base import ExtendedToolBase


class ConcreteTestTool(ExtendedToolBase):
    """Concrete subclass for testing the abstract base class."""

    tool_name = "test-tool"

    def _configure_options(self, options: dict[str, Any]) -> None:
        self.custom_option = options.get("custom", "default")

    def _analyze_file(self, filepath: Path) -> list[Message]:
        msg = self._create_message("TEST001", filepath, 1, f"Test issue in {filepath.name}")
        return [msg] if msg else []


class TestCreateMessage:
    """Tests for _create_message()."""

    def test_creates_message_with_all_fields(self):
        tool = ConcreteTestTool()
        msg = tool._create_message("E001", Path("test.py"), 10, "Error found", function="my_func", character=5)
        assert isinstance(msg, Message)
        assert msg.source == "test-tool"
        assert msg.code == "E001"
        assert msg.message == "Error found"
        assert msg.location.line == 10
        assert msg.location.function == "my_func"
        assert msg.location.character == 5

    def test_returns_none_when_code_ignored(self):
        tool = ConcreteTestTool()
        tool.ignore_codes = {"E001"}
        msg = tool._create_message("E001", Path("test.py"), 1, "Ignored error")
        assert msg is None

    def test_returns_message_when_code_not_ignored(self):
        tool = ConcreteTestTool()
        tool.ignore_codes = {"OTHER"}
        msg = tool._create_message("E001", Path("test.py"), 1, "Not ignored")
        assert msg is not None
        assert msg.code == "E001"

    def test_default_character_is_zero(self):
        tool = ConcreteTestTool()
        msg = tool._create_message("E001", Path("test.py"), 1, "Test")
        assert msg is not None
        assert msg.location.character == 0

    def test_default_function_is_none(self):
        tool = ConcreteTestTool()
        msg = tool._create_message("E001", Path("test.py"), 1, "Test")
        assert msg is not None
        assert msg.location.function is None


class TestRun:
    """Tests for run()."""

    def test_iterates_files_and_calls_analyze(self):
        tool = ConcreteTestTool()
        finder = MagicMock()
        finder.python_modules = [Path("a.py"), Path("b.py"), Path("c.py")]
        messages = tool.run(finder)
        assert len(messages) == 3

    def test_aggregates_messages_from_multiple_files(self):
        tool = ConcreteTestTool()
        finder = MagicMock()
        finder.python_modules = [Path("one.py"), Path("two.py")]
        messages = tool.run(finder)
        assert all(isinstance(m, Message) for m in messages)
        names = [str(m.location.path) for m in messages]
        assert any("one.py" in n for n in names)
        assert any("two.py" in n for n in names)

    def test_empty_file_list_returns_empty(self):
        tool = ConcreteTestTool()
        finder = MagicMock()
        finder.python_modules = []
        messages = tool.run(finder)
        assert messages == []

    def test_ignored_codes_filter_during_run(self):
        tool = ConcreteTestTool()
        tool.ignore_codes = {"TEST001"}
        finder = MagicMock()
        finder.python_modules = [Path("a.py"), Path("b.py")]
        messages = tool.run(finder)
        assert messages == []


class TestConfigure:
    """Tests for configure()."""

    def test_reads_tool_options(self):
        tool = ConcreteTestTool()
        config = MagicMock()
        config.tool_options.return_value = {"custom": "value123"}
        config.get_disabled_messages.return_value = []
        tool.configure(config, MagicMock())
        assert tool.custom_option == "value123"

    def test_reads_disabled_messages(self):
        tool = ConcreteTestTool()
        config = MagicMock()
        config.tool_options.return_value = {}
        config.get_disabled_messages.return_value = ["E001", "E002"]
        tool.configure(config, MagicMock())
        assert tool.ignore_codes == {"E001", "E002"}

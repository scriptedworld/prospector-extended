"""Tests for VultureTool and ProspectorVultureExtended."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from prospector.message import Message

from prospector_extended.tools.vulture_tool import ProspectorVultureExtended, VultureTool


@pytest.fixture
def dead_code_file(fixtures_dir):
    return fixtures_dir / "dead_code.py"


@pytest.fixture
def whitelist_fixture_file(fixtures_dir):
    return fixtures_dir / "whitelist_fixture.py"


@pytest.fixture
def mock_file_finder(dead_code_file):
    finder = MagicMock()
    finder.python_modules = [dead_code_file]
    return finder


class TestProspectorVultureExtended:
    """Tests for the extended Vulture scanner."""

    def test_scans_source_and_finds_dead_code(self, mock_file_finder):
        vulture = ProspectorVultureExtended(mock_file_finder, min_confidence=60)
        vulture.scavenge()
        messages = vulture.get_messages()
        codes = [m.code for m in messages]
        assert any("unused" in code for code in codes)

    def test_whitelist_suppresses_false_positives(self, mock_file_finder, whitelist_fixture_file):
        vulture_no_wl = ProspectorVultureExtended(mock_file_finder, min_confidence=60)
        vulture_no_wl.scavenge()
        messages_no_wl = vulture_no_wl.get_messages()

        vulture_wl = ProspectorVultureExtended(mock_file_finder, whitelist_paths=[whitelist_fixture_file], min_confidence=60)
        vulture_wl.scavenge()
        messages_wl = vulture_wl.get_messages()

        assert len(messages_wl) <= len(messages_no_wl)

    def test_min_confidence_filtering(self, mock_file_finder):
        vulture_low = ProspectorVultureExtended(mock_file_finder, min_confidence=10)
        vulture_low.scavenge()
        messages_low = vulture_low.get_messages()

        vulture_high = ProspectorVultureExtended(mock_file_finder, min_confidence=100)
        vulture_high.scavenge()
        messages_high = vulture_high.get_messages()

        assert len(messages_high) <= len(messages_low)

    def test_missing_whitelist_produces_v001(self, mock_file_finder):
        nonexistent = Path("/nonexistent/whitelist.py")
        vulture = ProspectorVultureExtended(mock_file_finder, whitelist_paths=[nonexistent], min_confidence=60)
        vulture.scavenge()
        messages = vulture.get_messages()
        v001_messages = [m for m in messages if m.code == "V001"]
        assert len(v001_messages) == 1
        assert "not found" in v001_messages[0].message.lower()

    def test_message_format(self, mock_file_finder):
        vulture = ProspectorVultureExtended(mock_file_finder, min_confidence=60)
        vulture.scavenge()
        messages = vulture.get_messages()
        assert len(messages) > 0
        for msg in messages:
            assert isinstance(msg, Message)
            assert msg.source == "vulture"
            assert msg.code is not None
            assert msg.location is not None

    def test_scavenge_ignores_arguments(self, mock_file_finder):
        vulture = ProspectorVultureExtended(mock_file_finder, min_confidence=60)
        vulture.scavenge("ignored", "also_ignored")
        messages = vulture.get_messages()
        assert isinstance(messages, list)


class TestVultureTool:
    """Tests for the VultureTool prospector integration."""

    def test_configure_reads_whitelist_paths(self):
        tool = VultureTool()
        config = MagicMock()
        config.tool_options.return_value = {"whitelist-paths": ["wl1.py", "wl2.py"], "min-confidence": 80}
        config.get_disabled_messages.return_value = []
        finder = MagicMock()
        tool.configure(config, finder)
        assert len(tool._whitelist_paths) == 2
        assert tool._min_confidence == 80

    def test_configure_handles_string_whitelist(self):
        tool = VultureTool()
        config = MagicMock()
        config.tool_options.return_value = {"whitelist-paths": "single.py"}
        config.get_disabled_messages.return_value = []
        finder = MagicMock()
        tool.configure(config, finder)
        assert len(tool._whitelist_paths) == 1

    def test_configure_defaults(self):
        tool = VultureTool()
        config = MagicMock()
        config.tool_options.return_value = {}
        config.get_disabled_messages.return_value = []
        finder = MagicMock()
        tool.configure(config, finder)
        assert tool._whitelist_paths == []
        assert tool._min_confidence == 60

    def test_run_returns_messages(self, mock_file_finder):
        tool = VultureTool()
        config = MagicMock()
        config.tool_options.return_value = {"min-confidence": 60}
        config.get_disabled_messages.return_value = []
        tool.configure(config, mock_file_finder)
        messages = tool.run(mock_file_finder)
        assert isinstance(messages, list)
        assert all(isinstance(m, Message) for m in messages)

    def test_run_filters_ignored_codes(self, mock_file_finder):
        tool = VultureTool()
        config = MagicMock()
        config.tool_options.return_value = {"min-confidence": 60}
        config.get_disabled_messages.return_value = ["unused-function", "unused-variable"]
        tool.configure(config, mock_file_finder)
        messages = tool.run(mock_file_finder)
        for msg in messages:
            assert msg.code not in ["unused-function", "unused-variable"]

"""Tests for cli.py - patch_prospector_tools() and main()."""

from __future__ import annotations

from unittest.mock import patch

from prospector_extended.cli import main, patch_prospector_tools
from prospector_extended.tools import ComplexipyTool, InterrogateTool, MypyTool, VultureTool


class TestPatchProspectorTools:
    """Tests for patch_prospector_tools()."""

    def test_registers_mypy_tool(self):
        from prospector import tools

        patch_prospector_tools()
        assert tools.TOOLS["mypy"] is MypyTool

    def test_registers_vulture_tool(self):
        from prospector import tools

        patch_prospector_tools()
        assert tools.TOOLS["vulture"] is VultureTool

    def test_registers_complexipy_tool(self):
        from prospector import tools

        patch_prospector_tools()
        assert tools.TOOLS["complexipy"] is ComplexipyTool

    def test_registers_interrogate_tool(self):
        from prospector import tools

        patch_prospector_tools()
        assert tools.TOOLS["interrogate"] is InterrogateTool

    def test_replaces_existing_mypy_entry(self):
        from prospector import tools

        original = tools.TOOLS.get("mypy")
        patch_prospector_tools()
        assert tools.TOOLS["mypy"] is MypyTool
        assert tools.TOOLS["mypy"] is not original or original is MypyTool

    def test_idempotent(self):
        patch_prospector_tools()
        patch_prospector_tools()
        from prospector import tools

        assert tools.TOOLS["mypy"] is MypyTool
        assert tools.TOOLS["vulture"] is VultureTool
        assert tools.TOOLS["complexipy"] is ComplexipyTool
        assert tools.TOOLS["interrogate"] is InterrogateTool


class TestMain:
    """Tests for main()."""

    def test_main_calls_prospector(self):
        with patch("prospector_extended.cli.patch_prospector_tools") as mock_patch, patch("prospector.run.main", return_value=0) as mock_main:
            result = main()
            mock_patch.assert_called_once()
            mock_main.assert_called_once()
            assert result == 0

    def test_main_returns_prospector_exit_code(self):
        with patch("prospector_extended.cli.patch_prospector_tools"), patch("prospector.run.main", return_value=2):
            result = main()
            assert result == 2

    def test_main_handles_none_return(self):
        with patch("prospector_extended.cli.patch_prospector_tools"), patch("prospector.run.main", return_value=None):
            result = main()
            assert result == 0

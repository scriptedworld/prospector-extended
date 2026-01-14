"""Interrogate integration for Prospector.

Provides docstring coverage analysis using interrogate.
Reports missing docstrings for modules, classes, functions, and methods.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prospector.message import Message

from prospector_extended.tools.base import ExtendedToolBase

# Error codes by node type
NODE_TYPE_CODES: dict[str, str] = {
    "Module": "INT100",
    "Class": "INT101",
    "Function": "INT102",
    "Method": "INT102",
    "FunctionDef": "INT102",
    "AsyncFunctionDef": "INT103",
    "NestedFunction": "INT104",
    "NestedAsyncFunction": "INT105",
    "Property": "INT106",
}

# Option name mapping from kebab-case to snake_case
OPTION_MAPPING: dict[str, str] = {
    "ignore-init-method": "ignore_init_method",
    "ignore-init-module": "ignore_init_module",
    "ignore-magic": "ignore_magic",
    "ignore-module": "ignore_module",
    "ignore-nested-functions": "ignore_nested_functions",
    "ignore-nested-classes": "ignore_nested_classes",
    "ignore-private": "ignore_private",
    "ignore-property-decorators": "ignore_property_decorators",
    "ignore-semiprivate": "ignore_semiprivate",
    "ignore-setters": "ignore_setters",
    "ignore-regex": "ignore_regex",
    "fail-under": "fail_under",
}


class InterrogateTool(ExtendedToolBase):
    """Docstring coverage analysis using interrogate.

    Reports missing docstrings for various Python constructs.
    Supports interrogate's ignore options for fine-grained control.
    """

    tool_name = "interrogate"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the interrogate tool."""
        super().__init__(*args, **kwargs)
        self._config_options: dict[str, Any] = {}

    def _configure_options(self, options: dict[str, Any]) -> None:
        """Configure interrogate-specific options."""
        self._config_options = {
            interrogate_key: options[prospector_key]
            for prospector_key, interrogate_key in OPTION_MAPPING.items()
            if prospector_key in options
        }

    def _analyze_file(self, filepath: Path) -> list[Message]:
        """Analyze a single file for missing docstrings."""
        try:
            from interrogate import config as interrogate_config
            from interrogate import coverage as interrogate_coverage
        except ImportError:
            return []

        try:
            conf = interrogate_config.InterrogateConfig(**self._config_options)
            cov = interrogate_coverage.InterrogateCoverage(
                paths=[str(filepath.absolute())],
                conf=conf,
            )
            results = cov.get_coverage()
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError, AttributeError):
            # OSError: file access issues
            # UnicodeDecodeError: encoding issues
            # SyntaxError: unparseable Python
            # ValueError/AttributeError: interrogate internal errors on edge cases
            return []

        messages: list[Message] = []
        for file_result in results.file_results:
            for node in file_result.nodes:
                if msg := self._check_node(filepath, node):
                    messages.append(msg)
        return messages

    def _check_node(self, filepath: Path, node: Any) -> Message | None:
        """Check if a node is missing a docstring."""
        if node.covered:
            return None

        # Skip module docstrings if ignore_module is set
        if node.node_type == "Module" and self._config_options.get("ignore_module", False):
            return None

        code = NODE_TYPE_CODES.get(node.node_type, "INT199")
        node_type_display = self._format_node_type(node.node_type)

        return self._create_message(
            code=code,
            filepath=filepath,
            line=node.lineno if node.lineno is not None else 1,
            message=f"Missing docstring for {node_type_display}: {node.name}",
            function=node.name if node.node_type != "Module" else None,
        )

    @staticmethod
    def _format_node_type(node_type: str) -> str:
        """Format node type for human-readable message."""
        type_map = {
            "AsyncFunctionDef": "async function",
            "NestedAsyncFunction": "nested async function",
            "NestedFunction": "nested function",
            "FunctionDef": "function",
        }
        return type_map.get(node_type, node_type.replace("Def", "").lower())

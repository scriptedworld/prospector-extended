"""Complexipy integration for Prospector.

Provides cognitive complexity analysis using complexipy.
Cognitive complexity measures how difficult code is to understand,
which is different from cyclomatic complexity (execution paths).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prospector.message import Message

from prospector_extended.tools.base import ExtendedToolBase

# Error codes
CODE_COMPLEXITY = "CCR001"  # Cognitive complexity too high
CODE_PARSE_ERROR = "CCE001"  # Parse error


class ComplexipyTool(ExtendedToolBase):
    """Cognitive complexity analysis using complexipy.

    Reports functions that exceed a configurable complexity threshold.
    Default threshold is 15 (aligned with SonarQube recommendations).
    """

    tool_name = "complexipy"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the complexipy tool."""
        super().__init__(*args, **kwargs)
        self.max_complexity: int = 15

    def _configure_options(self, options: dict[str, Any]) -> None:
        """Configure complexipy-specific options."""
        self.max_complexity = int(options.get("max-complexity", 15))

    def _analyze_file(self, filepath: Path) -> list[Message]:
        """Analyze a single file for complexity issues."""
        try:
            from complexipy import file_complexity
        except ImportError:
            return []

        try:
            file_result = file_complexity(str(filepath.absolute()))
            return [
                msg
                for func in file_result.functions
                if (msg := self._check_function(filepath, func)) is not None
            ]
        except SyntaxError as e:
            msg = self._syntax_error_message(filepath, e)
            return [msg] if msg else []
        except (OSError, UnicodeDecodeError, ValueError, AttributeError):
            # OSError: file access issues
            # UnicodeDecodeError: encoding issues
            # ValueError/AttributeError: complexipy internal errors on edge cases
            return []

    def _check_function(self, filepath: Path, func: Any) -> Message | None:
        """Check if a function exceeds complexity threshold."""
        if func.complexity <= self.max_complexity:
            return None

        return self._create_message(
            code=CODE_COMPLEXITY,
            filepath=filepath,
            line=func.line_start,
            message=(
                f"Cognitive complexity of {func.complexity} "
                f"exceeds threshold of {self.max_complexity} "
                f"for function '{func.name}'"
            ),
            function=func.name,
        )

    def _syntax_error_message(self, filepath: Path, e: SyntaxError) -> Message | None:
        """Create syntax error message."""
        return self._create_message(
            code=CODE_PARSE_ERROR,
            filepath=filepath,
            line=e.lineno or 1,
            message=f"Parse error: {e.msg}",
            character=e.offset,
        )

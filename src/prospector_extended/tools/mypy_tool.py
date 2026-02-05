"""Improved mypy integration for Prospector.

This tool provides robust mypy integration with:
- Direct use of mypy.api.run() for reliability
- JSON output parsing with Pydantic validation
- Text fallback for syntax errors (which bypass JSON formatter)
- Full configuration option support
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from prospector.message import Location, Message
from prospector.tools.base import ToolBase

from prospector_extended.parsing import MypyJsonOutput, parse_mypy_output

if TYPE_CHECKING:
    from prospector.config import ProspectorConfig
    from prospector.finder import FileFinder


# All valid mypy command-line options (as of mypy 1.13)
# See: https://mypy.readthedocs.io/en/stable/command_line.html
VALID_OPTIONS: frozenset[str] = frozenset(
    {
        # Import discovery
        "namespace-packages", "explicit-package-bases", "ignore-missing-imports",
        "follow-imports", "python-executable", "no-site-packages", "no-silence-site-packages",
        # Platform configuration
        "python-version", "platform", "always-true", "always-false",
        # Disallow dynamic typing
        "disallow-any-unimported", "disallow-any-expr", "disallow-any-decorated",
        "disallow-any-explicit", "disallow-any-generics", "disallow-subclassing-any",
        # Untyped definitions and calls
        "disallow-untyped-calls", "disallow-untyped-defs", "disallow-incomplete-defs",
        "check-untyped-defs", "disallow-untyped-decorators",
        # None and Optional handling
        "no-implicit-optional", "strict-optional",
        # Configuring warnings
        "warn-redundant-casts", "warn-unused-ignores", "warn-no-return",
        "warn-return-any", "warn-unreachable",
        # Suppressing errors
        "show-none-errors", "ignore-errors",
        # Miscellaneous strictness flags
        "allow-untyped-globals", "allow-redefinition", "local-partial-types",
        "disable-error-code", "enable-error-code", "strict-concatenate",
        "strict-equality", "strict", "extra-checks",
        # Configuring error messages
        "show-error-context", "show-column-numbers", "show-error-codes",
        "pretty", "color-output", "no-color-output", "error-summary",
        "no-error-summary", "show-absolute-path",
        # Incremental mode
        "no-incremental", "cache-dir", "skip-version-check", "skip-cache-mtime-checks",
        # Advanced options
        "plugins", "warn-unused-configs",
        # Report generation
        "any-exprs-report", "cobertura-xml-report", "html-report", "linecount-report",
        "linecoverage-report", "lineprecision-report", "txt-report", "xml-report",
        # Miscellaneous
        "scripts-are-modules", "install-types", "non-interactive", "junit-xml",
        "find-occurrences", "config-file", "exclude",
    }
)

# Default options for reliable parsing
DEFAULT_OPTIONS: list[str] = [
    "--show-column-numbers",
    "--no-error-summary",
    "--no-color-output",
    "--show-error-codes",
    "--follow-imports=normal",
]


# ToolBase is untyped in prospector, hence the type: ignore
# Note: MypyTool doesn't use ExtendedToolBase because mypy runs once on all files,
# not file-by-file like complexipy and interrogate.
class MypyTool(ToolBase):  # type: ignore[misc]
    """Improved mypy integration for Prospector.

    Uses mypy.api.run() directly with JSON output format and robust parsing.
    Falls back to text parsing for syntax errors.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mypy tool."""
        super().__init__(*args, **kwargs)
        self.options: list[str] = []
        self._configured = False

    def configure(
        self,
        prospector_config: ProspectorConfig,
        _: Any,
    ) -> tuple[str, Iterable[Message]] | None:
        """Configure mypy options from prospector config."""
        options = prospector_config.tool_options("mypy")
        self.options = self._build_base_options(options)
        self.options.extend(self._build_user_options(options))
        self.options.extend(self._build_message_options(prospector_config))
        self._configured = True
        return None

    def _build_base_options(self, options: dict[str, Any]) -> list[str]:
        """Build base options for reliable parsing."""
        base = [
            "--show-column-numbers",
            "--no-error-summary",
            "--no-color-output",
            "--show-error-codes",
        ]
        if "follow-imports" not in options:
            base.append("--follow-imports=normal")
        return base

    def _build_user_options(self, options: dict[str, Any]) -> list[str]:
        """Build user-specified options."""
        result: list[str] = []
        for name, value in options.items():
            if name not in VALID_OPTIONS:
                continue
            result.extend(self._format_option(name, value))
        return result

    @staticmethod
    def _format_option(name: str, value: Any) -> list[str]:
        """Format a single option for command line."""
        if value is False:
            return []
        if value is True:
            return [f"--{name}"]
        if isinstance(value, list):
            return [f"--{name}={v}" for v in value]
        return [f"--{name}={value}"]

    @staticmethod
    def _build_message_options(prospector_config: ProspectorConfig) -> list[str]:
        """Build options for disabled/enabled messages."""
        result: list[str] = []
        for code in prospector_config.get_disabled_messages("mypy"):
            result.append(f"--disable-error-code={code}")
        for code in prospector_config.get_enabled_messages("mypy"):
            result.append(f"--enable-error-code={code}")
        return result

    def run(self, found_files: FileFinder) -> list[Message]:
        """Run mypy on the found files."""
        if not self._configured:
            self.options = list(DEFAULT_OPTIONS)

        paths = [str(path) for path in found_files.python_modules]
        if not paths:
            return []

        stdout, stderr = self._run_mypy(paths)
        parsed = parse_mypy_output(stdout, stderr)
        return [msg for error in parsed if (msg := self._error_to_message(error)) is not None]

    def _run_mypy(self, paths: list[str]) -> tuple[str, str]:
        """Run mypy using the Python API."""
        import mypy.api

        args = ["--output=json", *self.options, *paths]
        stdout, stderr, _ = mypy.api.run(args)
        return stdout, stderr

    @staticmethod
    def _error_to_message(error: MypyJsonOutput) -> Message | None:
        """Convert a single error to a message."""
        if error.severity == "note":
            return None

        message_text = error.message
        if error.hint:
            message_text = f"{message_text} ({error.hint})"

        return Message(
            source="mypy",
            code=error.code or "error",
            location=Location(
                path=error.file,
                module=None,
                function=None,
                line=error.line,
                character=error.column,
            ),
            message=message_text,
        )

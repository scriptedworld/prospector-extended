"""Improved vulture integration for Prospector with whitelist support.

This tool extends prospector's built-in vulture integration to add:
- Whitelist file support (scan files that "use" things to suppress false positives)
- min-confidence configuration option

Whitelist files are Python files that reference items you want to suppress.
For example, a whitelist might contain:

    from mymodule import MyClass
    _instance = MyClass()
    _instance.some_field  # marks 'some_field' as used

The whitelist files are scanned BEFORE source files, so vulture sees
those items as "used" and won't report them as dead code.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vulture import Vulture

from prospector.encoding import CouldNotHandleEncoding, read_py_file
from prospector.message import Location, Message, make_tool_error_message
from prospector.tools.base import ToolBase

if TYPE_CHECKING:
    from prospector.config import ProspectorConfig
    from prospector.finder import FileFinder


class ProspectorVultureExtended(Vulture):
    """Extended Vulture with whitelist support.

    Scans whitelist files before source files so that items referenced
    in whitelists are marked as "used" and not reported as dead code.
    """

    def __init__(
        self,
        found_files: FileFinder,
        *,
        whitelist_paths: list[Path] | None = None,
        min_confidence: int = 60,
    ) -> None:
        """Initialize extended vulture.

        Args:
            found_files: Prospector's file finder.
            whitelist_paths: List of whitelist file paths to scan first.
            min_confidence: Minimum confidence for reporting (0-100).
        """
        Vulture.__init__(self, verbose=False)
        self._files = found_files
        self._whitelist_paths = whitelist_paths or []
        self._min_confidence = min_confidence
        self._internal_messages: list[Message] = []
        self.file: Path | None = None
        self.filename: Path | None = None

    def scavenge(self, _: Any = None, __: Any = None) -> None:
        """Scan whitelist files first, then source files.

        The arguments are ignored - we use the found_files from __init__.
        They're here to match the Vulture.scavenge signature.
        """
        # First, scan whitelist files to mark items as "used"
        for whitelist_path in self._whitelist_paths:
            self._scan_file(whitelist_path, is_whitelist=True)

        # Then scan source files
        for module in self._files.python_modules:
            self._scan_file(module, is_whitelist=False)

    def _scan_file(self, filepath: Path, *, is_whitelist: bool) -> None:
        """Scan a single file.

        Args:
            filepath: Path to the file.
            is_whitelist: True if this is a whitelist file (errors are warnings).
        """
        try:
            module_string = read_py_file(filepath)
        except CouldNotHandleEncoding as err:
            # Only report encoding errors for source files, not whitelists
            if not is_whitelist:
                self._internal_messages.append(
                    make_tool_error_message(
                        filepath,
                        "vulture",
                        "V000",
                        message=f"Could not handle the encoding of this file: {err.encoding}",  # type: ignore[attr-defined]
                    )
                )
            return
        except FileNotFoundError:
            # Whitelist file not found - report as warning
            if is_whitelist:
                self._internal_messages.append(
                    make_tool_error_message(
                        filepath,
                        "vulture",
                        "V001",
                        message=f"Whitelist file not found: {filepath}",
                    )
                )
            return

        self.file = filepath
        self.filename = filepath
        try:
            self.scan(module_string, filename=filepath)
        except TypeError:
            # Older vulture versions don't accept filename
            self.scan(module_string)

    def get_messages(self) -> list[Message]:
        """Get all vulture messages filtered by min_confidence.

        Returns:
            List of prospector Message objects for unused code.
        """
        # Map vulture item types to error codes
        type_to_code = {
            "function": "unused-function",
            "property": "unused-property",
            "variable": "unused-variable",
            "attribute": "unused-attribute",
            "class": "unused-class",
            "import": "unused-import",
            "method": "unused-method",
        }

        vulture_messages = []
        # get_unused_code() returns all items filtered by min_confidence
        for item in self.get_unused_code(min_confidence=self._min_confidence):
            try:
                filename = item.file
            except AttributeError:
                filename = item.filename
            lineno = item.lineno if hasattr(item, "lineno") else item.first_lineno

            # Get the error code based on item type
            code = type_to_code.get(item.typ, f"unused-{item.typ}")

            loc = Location(filename, None, None, lineno, -1)
            message_text = f"Unused {item.typ} '{item.name}' ({item.confidence}% confidence)"
            message = Message("vulture", code, loc, message_text)
            vulture_messages.append(message)

        return self._internal_messages + vulture_messages


# ToolBase is untyped in prospector, hence the type: ignore
class VultureTool(ToolBase):  # type: ignore[misc]
    """Extended vulture tool with whitelist support.

    Configuration options in .prospector.yaml:

        vulture:
          run: true
          options:
            min-confidence: 80
            whitelist-paths:
              - vulture_whitelist.py
              - other_whitelist.py

    Whitelist files are Python files that "use" items you want to suppress.
    They are scanned before source files so vulture sees those items as used.
    """

    def __init__(self) -> None:
        """Initialize the vulture tool."""
        ToolBase.__init__(self)
        self._whitelist_paths: list[Path] = []
        self._min_confidence: int = 60
        self.ignore_codes: list[str] = []

    def configure(
        self, prospector_config: ProspectorConfig, found_files: FileFinder
    ) -> tuple[str, Iterable[Message]] | None:
        """Configure vulture options from prospector config.

        Args:
            prospector_config: The prospector configuration.
            found_files: Files to analyze (unused here, used in run()).

        Returns:
            None on success.
        """
        options = prospector_config.tool_options("vulture")

        # Get whitelist paths
        whitelist_paths = options.get("whitelist-paths", [])
        if isinstance(whitelist_paths, str):
            whitelist_paths = [whitelist_paths]
        self._whitelist_paths = [Path(p) for p in whitelist_paths]

        # Get min-confidence (vulture default is 60)
        self._min_confidence = int(options.get("min-confidence", 60))

        # Get ignored error codes
        self.ignore_codes = list(prospector_config.get_disabled_messages("vulture"))

        return None

    def run(self, found_files: FileFinder) -> list[Message]:
        """Run vulture on found files with whitelist support.

        Args:
            found_files: Files to analyze.

        Returns:
            List of messages for unused code.
        """
        vulture = ProspectorVultureExtended(
            found_files,
            whitelist_paths=self._whitelist_paths,
            min_confidence=self._min_confidence,
        )
        vulture.scavenge()
        return [
            message
            for message in vulture.get_messages()
            if message.code not in self.ignore_codes
        ]

"""Base class for prospector-extended tools.

Provides common infrastructure for tool implementations:
- Configuration handling
- Ignore code management
- Message creation helpers
- File iteration patterns
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prospector.message import Location, Message
from prospector.tools.base import ToolBase

if TYPE_CHECKING:
    from prospector.config import ProspectorConfig
    from prospector.finder import FileFinder


# ToolBase is untyped in prospector, hence the type: ignore
class ExtendedToolBase(ToolBase):  # type: ignore[misc]
    """Base class for prospector-extended tools.

    Subclasses must implement:
    - tool_name: class attribute with the tool's name
    - _configure_options: extract tool-specific options
    - _analyze_file: analyze a single file
    """

    tool_name: str = ""  # Override in subclasses

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the tool."""
        super().__init__(*args, **kwargs)
        self.ignore_codes: set[str] = set()

    def configure(
        self,
        prospector_config: ProspectorConfig,
        _: Any,
    ) -> tuple[str, Iterable[Message]] | None:
        """Configure tool options from prospector config.

        Args:
            prospector_config: The prospector configuration.
            _: Unused found_files parameter.

        Returns:
            None on success.
        """
        options = prospector_config.tool_options(self.tool_name)
        self._configure_options(options)
        self.ignore_codes = set(prospector_config.get_disabled_messages(self.tool_name))
        return None

    @abstractmethod
    def _configure_options(self, options: dict[str, Any]) -> None:
        """Configure tool-specific options.

        Args:
            options: Tool options from prospector config.
        """
        ...

    def run(self, found_files: FileFinder) -> list[Message]:
        """Run the tool on found files.

        Args:
            found_files: Files to analyze.

        Returns:
            List of prospector Message objects.
        """
        messages: list[Message] = []
        for filepath in found_files.python_modules:
            messages.extend(self._analyze_file(filepath))
        return messages

    @abstractmethod
    def _analyze_file(self, filepath: Path) -> list[Message]:
        """Analyze a single file.

        Args:
            filepath: Path to the file.

        Returns:
            List of messages for this file.
        """
        ...

    def _create_message(
        self,
        code: str,
        filepath: Path,
        line: int,
        message: str,
        *,
        function: str | None = None,
        character: int | None = 0,
    ) -> Message | None:
        """Create a message if the code is not ignored.

        Args:
            code: Error code.
            filepath: Path to the file.
            line: Line number.
            message: Error message.
            function: Optional function name.
            character: Optional column number.

        Returns:
            Message if code not ignored, None otherwise.
        """
        if code in self.ignore_codes:
            return None

        return Message(
            source=self.tool_name,
            code=code,
            location=Location(
                path=str(filepath),
                module=None,
                function=function,
                line=line,
                character=character,
            ),
            message=message,
        )

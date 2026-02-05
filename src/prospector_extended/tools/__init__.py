"""Extended tools for Prospector.

Provides improved and additional tools:
- MypyTool: Robust mypy integration with JSON parsing
- ComplexipyTool: Cognitive complexity analysis
- InterrogateTool: Docstring coverage analysis

Also provides ExtendedToolBase for creating custom file-by-file analysis tools.
"""

from prospector_extended.tools.base import ExtendedToolBase
from prospector_extended.tools.complexipy_tool import ComplexipyTool
from prospector_extended.tools.interrogate_tool import InterrogateTool
from prospector_extended.tools.mypy_tool import MypyTool

__all__ = [
    "ExtendedToolBase",
    "MypyTool",
    "ComplexipyTool",
    "InterrogateTool",
]

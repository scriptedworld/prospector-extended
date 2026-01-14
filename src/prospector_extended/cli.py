"""CLI wrapper for prospector with extended tools.

This module patches prospector's TOOLS dict to add/replace tools:
- mypy: Improved implementation with robust JSON parsing (replaces built-in)
- vulture: Dead code detection with whitelist support (replaces built-in)
- complexipy: Cognitive complexity analysis (new)
- interrogate: Docstring coverage analysis (new)

Usage:
    prospector-extended src/
    prospector-extended --output-format json src/
    pex --without-tool vulture src/

Tools are configured via .prospector.yaml (run: true/false).
"""

from __future__ import annotations

import sys


def patch_prospector_tools() -> None:
    """Patch prospector's TOOLS dict with our improved/new tools.

    This must be called before importing prospector.run.
    """
    from prospector import tools

    from prospector_extended.tools import ComplexipyTool, InterrogateTool, MypyTool, VultureTool

    # Replace built-in tools with improved versions
    tools.TOOLS["mypy"] = MypyTool
    tools.TOOLS["vulture"] = VultureTool

    # Add new tools
    tools.TOOLS["complexipy"] = ComplexipyTool
    tools.TOOLS["interrogate"] = InterrogateTool


def main() -> int:
    """Run prospector with extended tools.

    Returns:
        Exit code from prospector.
    """
    # Patch tools before importing prospector.run
    patch_prospector_tools()

    # Import and run prospector's main
    from prospector.run import main as prospector_main

    result = prospector_main()
    return int(result) if result is not None else 0


if __name__ == "__main__":
    sys.exit(main())

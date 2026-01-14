"""Prospector Extended - Enhanced static analysis tools for Python.

This package provides improved and additional tools for Prospector:
- mypy: Improved implementation with robust JSON parsing and text fallback
- complexipy: Cognitive complexity analysis (better than cyclomatic for maintainability)
- interrogate: Docstring coverage analysis

Usage:
    # Run via CLI wrapper
    prospector-extended src/

    # Or import and patch manually
    from prospector_extended.cli import patch_prospector_tools
    patch_prospector_tools()

    # Then use prospector normally
    from prospector.run import main
    main()

Tools Configuration (.prospector.yaml):
    mypy:
      run: true
      options:
        strict: true
        python-version: "3.12"

    complexipy:
      run: true
      options:
        max-complexity: 15

    interrogate:
      run: true
      options:
        ignore-init-method: true
        ignore-magic: true
"""

from prospector_extended.cli import main, patch_prospector_tools

__all__ = ["main", "patch_prospector_tools"]
__version__ = "0.1.0"

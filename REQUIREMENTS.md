# prospector-extended - Requirements

## Overview

Extended Prospector with improved mypy, vulture (whitelist support), complexipy, and interrogate tools for comprehensive Python code analysis.

## Functional Requirements

### FR-001: Improved mypy Integration

**Description:** Replace Prospector's built-in mypy tool with a robust implementation that handles all output formats reliably.

**Acceptance Criteria:**
- [x] Uses `mypy.api.run()` directly for reliable execution
- [x] Parses JSON output with Pydantic validation
- [x] Falls back to text/regex parsing when JSON output is malformed
- [x] Supports all standard mypy configuration options via `pyproject.toml`
- [x] Compatible with Python 3.12, 3.13, and 3.14

### FR-002: Vulture with Whitelist Support

**Description:** Extend Prospector's vulture integration to support whitelist files for suppressing false positives.

**Acceptance Criteria:**
- [x] Supports `whitelist-paths` option in `.prospector.yaml`
- [x] Scans whitelist files first to mark items as "used" before analyzing source
- [x] Reports warning (V001) if whitelist file not found
- [x] Reports warning (V000) for encoding errors
- [x] Supports `min-confidence` threshold configuration

### FR-003: Complexipy Integration

**Description:** Add cognitive complexity analysis as a Prospector tool.

**Acceptance Criteria:**
- [x] Integrates complexipy as a Prospector tool
- [x] Reports functions exceeding cognitive complexity threshold
- [x] Configurable via `max-complexity` option
- [x] Error code CCR001 for threshold violations, CCE001 for parse errors

### FR-004: Interrogate Integration

**Description:** Add docstring coverage analysis as a Prospector tool.

**Acceptance Criteria:**
- [x] Integrates interrogate as a Prospector tool
- [x] Reports missing docstrings with INT1xx error codes
- [x] Supports all interrogate configuration options (ignore-init, ignore-magic, etc.)
- [x] Configurable fail-under threshold

### FR-005: CLI Entry Point

**Description:** Provide a CLI that patches Prospector's tool registry and runs analysis.

**Acceptance Criteria:**
- [x] `prospector-extended` command available after install
- [x] `pex` convenience alias available
- [x] Patches Prospector's TOOLS dict at runtime before execution
- [x] Passes all arguments through to Prospector

### FR-006: Parsing Infrastructure

**Description:** Flexible JSON parsing infrastructure for tool output handling.

**Acceptance Criteria:**
- [x] TypeRegistry for polymorphic JSON parsing with schema matching
- [x] Pydantic models with runtime validation
- [x] Schema fingerprinting for drift detection
- [x] Text fallback for non-JSON output

## Non-Functional Requirements

### NFR-001: Code Quality

- 80%+ test coverage (branch-inclusive)
- All type hints (strict mypy)
- 80% docstring coverage (interrogate)
- Cyclomatic complexity ≤ 10 per function
- Cognitive complexity ≤ 15 per function

### NFR-002: Python Version Support

- Python 3.12+ required
- Tested on 3.12, 3.13, 3.14

### NFR-003: Compatibility

- Compatible with Prospector ≥ 1.10.0
- Uses Prospector's tool interface (`ToolBase`)
- No modifications to Prospector source code

## Constraints

- Python 3.12+ (uses modern syntax)
- Licensed under GPL-2.0-or-later (same as Prospector)
- Must work as a drop-in replacement for `prospector` CLI

## Non-Requirements

- Pyright integration (dropped in favor of mypy-only approach)
- Custom output formatters (uses Prospector's built-in formatters)
- IDE plugins or editor integrations

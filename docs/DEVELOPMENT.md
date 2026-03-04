# Development Guide

This guide covers setting up a development environment and contributing to prospector-extended.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
git clone <repository-url>
cd prospector-extended
uv run poe sync-setup
uv run poe ensure-hooks
```

## Poe Tasks

prospector-extended uses [poethepoet](https://poethepoet.natn.io/) for task automation. All tasks are run via `uv run poe <task>`.

### Core Tasks

| Task | Description |
|------|-------------|
| `test` | Run tests without coverage |
| `test-cov` | Run pytest with coverage report |
| `test-slow` | Run slow tests only (real subprocess pipelines) |
| `test-all` | Run all tests including slow |
| `validate-coverage` | Per-file branch coverage gate (80% threshold) |
| `test-coverage` | Run test-cov + validate-coverage |
| `checks` | Run all checks (test-coverage + format-check + quality) |

### Code Quality

| Task | Description |
|------|-------------|
| `format` | Format code with ruff |
| `format-check` | Check formatting without changes |
| `lint` | Run ruff linter |
| `lint-fix` | Run ruff with auto-fix |
| `types` | Run mypy type checking |
| `security` | Run bandit security scanner |
| `quality` | Run prospector-extended (comprehensive analysis) |
| `xray` | Run xray-audit dependency CVE scan (JFrog Xray) |

### Documentation

| Task | Description |
|------|-------------|
| `docs` | Generate API docs to docs/api/ |

### Maintenance

| Task | Description |
|------|-------------|
| `sync-setup` | Sync dependencies + install vendor packages |
| `ensure-hooks` | Install pre-commit hooks |
| `clean` | Remove generated artifacts |

## Code Style

### Formatting

Code is formatted with [ruff](https://docs.astral.sh/ruff/). Line length is 150, double quotes, space indent.

```bash
uv run poe format        # Auto-format
uv run poe format-check  # Check only
```

### Linting

Ruff handles linting with rule sets: E, F, W (pycodestyle/pyflakes), I (isort), UP (pyupgrade),
B (bugbear), SIM (simplify), C4/C90 (comprehensions/complexity), N (naming), D (docstrings),
T20 (print), RET (returns), PTH (pathlib), ERA (commented code), PL (pylint), RUF (ruff-specific),
ARG (unused arguments).

### Type Checking

Strict mypy configuration. All code in `src/` must pass strict type checking.

```bash
uv run poe types
```

### Docstrings

Google-style docstrings are required for all public functions, classes, and methods.
Coverage is enforced by interrogate at 80% minimum.

## Pre-commit Hooks

| Hook | Stage | Description |
|------|-------|-------------|
| trailing-whitespace | commit | Remove trailing whitespace |
| end-of-file-fixer | commit | Ensure files end with newline |
| check-yaml | commit | Validate YAML syntax |
| check-toml | commit | Validate TOML syntax |
| check-json | commit | Validate JSON syntax |
| check-added-large-files | commit | Prevent large file commits |
| ruff | commit | Lint with auto-fix |
| ruff-format | commit | Format check |
| commitizen | commit-msg | Validate conventional commit format |
| xray | pre-push | JFrog Xray vulnerability scan |

## Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/) enforced by commitizen.

```
type(scope): description

body (optional)
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Project Structure

```
prospector-extended/
├── src/prospector_extended/
│   ├── __init__.py             # Package init, patch_prospector_tools()
│   ├── cli.py                  # CLI entry point
│   ├── parsing/
│   │   ├── __init__.py         # Public API exports
│   │   ├── models.py           # Pydantic models for tool output
│   │   └── registry.py         # TypeRegistry for polymorphic parsing
│   └── tools/
│       ├── __init__.py         # Tool registration
│       ├── base.py             # ExtendedToolBase
│       ├── complexipy_tool.py  # Cognitive complexity tool
│       ├── interrogate_tool.py # Docstring coverage tool
│       ├── mypy_tool.py        # Improved mypy tool
│       └── vulture_tool.py     # Vulture with whitelist support
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_mypy_tool.py       # Mypy tool tests
│   └── test_parsing.py         # Parsing infrastructure tests
├── docs/                       # Documentation
├── vendor/                     # Vendored wheels
├── vulture_whitelist.py        # Vulture false positive suppressions
├── .prospector.yaml            # Prospector tool configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
└── pyproject.toml              # Build config, dependencies, tool settings
```

## Quality Gates

All quality gates must pass before merging:

1. **Tests** — All pytest tests pass
2. **Coverage** — Branch-inclusive coverage ≥ 80%
3. **Format** — ruff format check passes
4. **Quality** — prospector-extended reports no issues (runs ruff, mypy, bandit, vulture, pylint, complexipy, interrogate, dodgy)

Run all gates: `uv run poe checks`

## Suppression Policy

No `# noqa`, `# nosec`, or `# type: ignore` comment may be added without explicit approval.
Every approved suppression must be documented in [SUPPRESSIONS.md](SUPPRESSIONS.md) with
justification. Prefer fixing root causes over suppressing warnings.

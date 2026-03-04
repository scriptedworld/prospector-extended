# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PROJECT.md and REQUIREMENTS.md documentation
- CHANGELOG.md and SECURITY.md
- `.pre-commit-config.yaml` with ruff, commitizen, and xray hooks
- `.gitignore` and directory scaffolding (vendor/, scripts/, docs/design/)
- `vulture_whitelist.py` for false positive suppression
- PEP 561 `py.typed` marker

### Changed
- Overhauled `pyproject.toml` to match python-base-template standards
- Migrated build system from hatchling to uv_build
- Migrated dev dependencies to `[dependency-groups]`
- Added 18 poe tasks (sync-setup, checks, test-coverage, quality, etc.)
- Aligned `.prospector.yaml` with template (simplified mypy, added vulture whitelist)
- Expanded ruff rule set (added N, T20, RET, PTH, ERA, PL, RUF)

## [0.2.0] - 2025-01-15

### Added
- VultureTool with whitelist file support (`whitelist-paths` option)
- Vulture error codes: V000 (encoding error), V001 (whitelist not found)

### Changed
- Improved existing tool integrations

## [0.1.0] - 2025-01-01

### Added
- Initial release
- Improved mypy integration with JSON/Pydantic parsing and text fallback
- Complexipy integration for cognitive complexity analysis
- Interrogate integration for docstring coverage analysis
- Parsing infrastructure (TypeRegistry, Pydantic models, schema fingerprinting)
- CLI entry point (`prospector-extended` / `pex`)

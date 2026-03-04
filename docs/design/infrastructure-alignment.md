# Infrastructure Alignment Design

Decisions and deviations for aligning prospector-extended with python-base-template.

## Key Context

This project IS `prospector-extended` — the quality tool that other template-based
projects install from `vendor/`. This creates a self-referential situation where
`poe quality` runs the tool on its own codebase.

## Intentional Deviations from Template

### 1. Runtime Dependencies Include Quality Tools

The template lists quality tools as dev deps (bandit, vulture, ruff). In this
project, these are **runtime** dependencies via `prospector[with_bandit,with_vulture,with_ruff]`
because the package bundles them. Do NOT duplicate them in dev deps.

**Dev deps to add:** commitizen, pdoc, pre-commit, pytest-json-report
**Dev deps NOT needed (already runtime):** bandit, vulture, ruff, pylint

### 2. Build System: hatchling → uv_build

The current `[tool.hatch.build.targets.wheel]` with `packages = ["src/prospector_extended"]`
needs replacement. uv_build auto-detects src layout. Remove hatch-specific config.

### 3. D107 (Missing __init__ docstring)

Template ignores `D100, D104`. Current also ignores `D107`. Since
`[tool.interrogate] ignore-init-method = true` already handles this and interrogate
provides more nuanced docstring checking, keeping `D107` in ruff ignores is valid
to avoid duplicate warnings. **Keep D107 in ignore list.**

### 4. ARG Rule Set

Current project has `ARG` (unused arguments) in ruff rules. Template does not
include it (relies on PL which covers some). Since ARG provides value for this
project (caught the vulture_tool.py issue), **keep ARG in ruff rules** in addition
to template rules.

### 5. Self-Referential Quality Check

`poe quality` runs `prospector-extended src/` — the tool checking itself. This is
correct behavior and validates the tool works. The `poe checks` composite task
should match template: `["test-coverage", "format-check", "quality"]`.

## Task Review Notes

### Task 1.01 (Scaffolding)
- Verified: all directories and files are correct
- No changes needed

### Task 1.03 (pyproject.toml)
- Requirement 5: Remove bandit, pylint, vulture from dev deps list (already runtime)
- Requirement 27: Keep ARG in addition to template rules
- Requirement 30: Keep D107 in ignore list (see deviation #3)
- Add: Remove `[tool.hatch.build.targets.wheel]` and `[tool.hatch.build.targets.sdist]` sections

### Task 1.05 (Pre-commit)
- Verified: matches template exactly
- No changes needed

### Task 1.07 (.prospector.yaml)
- Verified: simplification approach is correct
- Note: max-line-length should be removed entirely (ruff handles via pyproject.toml)

### Task 1.09 (Vulture whitelist)
- Verified: approach is correct
- Move `ignore_names` from pyproject.toml to whitelist file

## Dependency Order

Tasks must execute in order: 1.01 → 1.03 → 1.05 → 1.07 → 1.09
- 1.01 creates directories that 1.03 references (.task/)
- 1.03 creates poe tasks that 1.05 and 1.07 depend on
- 1.07 references vulture whitelist from 1.09, but can be done before
- 1.09 references .prospector.yaml whitelist-paths from 1.07

# prospector-extended - Tasks

## Status: `[ ]` Not started | `[~]` In progress | `[x]` Complete | `[!]` Blocked

## Phase 0: Setup

- [x] 0.01 - Initial project scaffolding
- [x] 0.02 - v0.2.0 with vulture tool support

## Phase 1: Project Infrastructure

- [x] 1.00 - Infrastructure alignment design review
- [x] 1.01 - Add .gitignore and directory scaffolding
- [x] 1.03 - Overhaul pyproject.toml to match template
- [x] 1.05 - Add .pre-commit-config.yaml
- [x] 1.07 - Align .prospector.yaml with template
- [x] 1.09 - Add vulture_whitelist.py

## Phase 2: Documentation

- [x] 2.01 - Add PROJECT.md and REQUIREMENTS.md
- [x] 2.03 - Add CHANGELOG.md and SECURITY.md
- [x] 2.05 - Add docs/DEVELOPMENT.md, docs/ARCHITECTURE.md, docs/SUPPRESSIONS.md
- [x] 2.07 - Add TODO.md, STATUS.md, NEXT_STEPS.md

## Phase 3: Quality & Test Coverage

- [x] 3.01 - Fix 4 quality violations in vulture_tool.py
- [x] 3.03 - Add tests for cli.py
- [x] 3.05 - Add tests for VultureTool
- [x] 3.07 - Add tests for ExtendedToolBase
- [x] 3.09 - Add error path and edge case tests

## Phase 4: Metrics Integration

- [ ] 4.01 - MetricsCollector and `metrics` JSON block infrastructure
- [ ] 4.03 - RadonTool: cyclomatic complexity, raw LOC, maintainability index
- [ ] 4.05 - StructureTool: AST-based function length, nesting, visibility, params
- [ ] 4.07 - Extend complexipy_tool to emit all per-function cognitive scores
- [ ] 4.09 - Extend interrogate_tool to emit coverage % and per-type counts
- [ ] 4.11 - Extend vulture_tool to emit dead code summary metrics
- [ ] 4.13 - Suppression counting and pylint duplication metrics
- [ ] 4.15 - End-to-end integration tests for metrics output

See `tasks/` for detailed task files.

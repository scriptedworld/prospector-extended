# Task Index — prospector-extended

## Progress Summary

| Phase | Total | Done | Remaining |
|-------|-------|------|-----------|
| 1 — Project Infrastructure | 6 | 6 | 0 |
| 2 — Documentation | 4 | 4 | 0 |
| 3 — Quality & Test Coverage | 5 | 0 | 5 |
| **Total** | **15** | **10** | **5** |

## Phase 1: Project Infrastructure

Align build system, tooling, and configuration with python-base-template standards.

| Task | Status | File | Description |
|------|--------|------|-------------|
| 1.00 | [x] | [1.00-infrastructure-design.md](phase-1/1.00-infrastructure-design.md) | Infrastructure alignment design review |
| 1.01 | [x] | [1.01-gitignore-scaffolding.md](phase-1/1.01-gitignore-scaffolding.md) | Add .gitignore and directory scaffolding |
| 1.03 | [x] | [1.03-pyproject-overhaul.md](phase-1/1.03-pyproject-overhaul.md) | Overhaul pyproject.toml to match template |
| 1.05 | [x] | [1.05-pre-commit-config.md](phase-1/1.05-pre-commit-config.md) | Add .pre-commit-config.yaml |
| 1.07 | [x] | [1.07-prospector-yaml-align.md](phase-1/1.07-prospector-yaml-align.md) | Align .prospector.yaml with template |
| 1.09 | [x] | [1.09-vulture-whitelist.md](phase-1/1.09-vulture-whitelist.md) | Add vulture_whitelist.py |

## Phase 2: Documentation

Create standard documentation files per template and CLAUDE.md requirements.

| Task | Status | File | Description |
|------|--------|------|-------------|
| 2.01 | [x] | [2.01-project-requirements.md](phase-2/2.01-project-requirements.md) | Add PROJECT.md and REQUIREMENTS.md |
| 2.03 | [x] | [2.03-changelog-security.md](phase-2/2.03-changelog-security.md) | Add CHANGELOG.md and SECURITY.md |
| 2.05 | [x] | [2.05-dev-docs.md](phase-2/2.05-dev-docs.md) | Add docs/DEVELOPMENT.md, docs/ARCHITECTURE.md, docs/SUPPRESSIONS.md |
| 2.07 | [x] | [2.07-state-files.md](phase-2/2.07-state-files.md) | Add TODO.md, STATUS.md, NEXT_STEPS.md |

## Phase 3: Quality & Test Coverage

Fix quality violations and close test coverage gaps identified in code review.

| Task | Status | File | Description |
|------|--------|------|-------------|
| 3.01 | [ ] | [3.01-fix-quality-violations.md](phase-3/3.01-fix-quality-violations.md) | Fix 4 quality violations in vulture_tool.py |
| 3.03 | [ ] | [3.03-test-cli.md](phase-3/3.03-test-cli.md) | Add tests for cli.py |
| 3.05 | [ ] | [3.05-test-vulture-tool.md](phase-3/3.05-test-vulture-tool.md) | Add tests for VultureTool |
| 3.07 | [ ] | [3.07-test-base-tool.md](phase-3/3.07-test-base-tool.md) | Add tests for ExtendedToolBase |
| 3.09 | [ ] | [3.09-test-error-paths.md](phase-3/3.09-test-error-paths.md) | Add error path and edge case tests |

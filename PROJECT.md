# prospector-extended - Project Details

Project-specific configuration. Process rules are in `.claude/CLAUDE.md`.

## Tech Stack

- **Language:** Python 3.12+
- **Build:** uv
- **Tasks:** poethepoet
- **Testing:** pytest, pytest-cov
- **Quality:** prospector-extended, ruff, mypy, bandit, vulture
- **Git:** pre-commit, commitizen

## Structure

```
prospector-extended/
├── src/prospector_extended/
│   ├── parsing/            # JSON parsing infrastructure (TypeRegistry, Pydantic models)
│   ├── tools/              # Extended tool implementations (mypy, vulture, complexipy, interrogate)
│   └── cli.py              # CLI entry point (patches prospector + runs)
├── tests/
├── docs/                   # Documentation
│   ├── design/             # Project-specific design docs
│   └── SUPPRESSIONS.md     # Suppression audit log
├── lessons/                # Project-specific lessons (gitignored)
├── tasks/                  # Task tracking (gitignored)
├── vendor/                 # Vendored wheels
├── .task/                  # Quality output artifacts (gitignored)
└── .claude/                # Claude Code config (gitignored)
    ├── CLAUDE.md           # Universal process rules
    ├── skills/             # Claude skills
    ├── lessons/            # Global lessons
    └── design/             # Global design principles
```

## Quality Thresholds

| Metric | Threshold |
|--------|-----------|
| Test coverage | 80% |
| Cyclomatic complexity | ≤ 10 |
| Cognitive complexity | ≤ 15 |
| Docstring coverage | 80% |

## Commands

```bash
uv run poe sync-setup      # Sync deps + vendor wheels
uv run poe ensure-hooks    # Setup pre-commit
uv run poe test            # Run tests
uv run poe test-cov        # Tests with coverage
uv run poe test-coverage   # Tests + coverage validation
uv run poe checks          # Full verification (tests + format + quality)
uv run poe format          # Format code
uv run poe format-check    # Verify formatting
uv run poe lint            # Ruff linting
uv run poe lint-fix        # Ruff linting with auto-fix
uv run poe types           # Mypy type checking
uv run poe security        # Bandit security scan
uv run poe quality         # Run prospector-extended on src/
uv run poe xray            # JFrog Xray vulnerability scan
uv run poe docs            # Generate API docs
uv run poe clean           # Remove build/test artifacts
```

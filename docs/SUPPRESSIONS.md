# Code Quality Suppressions

Audit log of all inline suppression comments (`# noqa`, `# nosec`, `# type: ignore`)
in the codebase. Every suppression must be documented here with justification and
approval before it can be committed.

**Policy:** No suppression line may be added without explicit approval and an entry
in this file. If a new suppression is needed, document it here first and get approval
before adding the inline comment.

---

## Type Suppressions (`# type: ignore`)

### misc — Untyped base class (ToolBase / Vulture)

| File | Line | Suppression | Status |
|------|------|-------------|--------|
| `src/prospector_extended/tools/base.py` | 26 | `# type: ignore[misc]` | Approved |
| `src/prospector_extended/tools/vulture_tool.py` | 34 | `# type: ignore[misc]` | Approved |
| `src/prospector_extended/tools/mypy_tool.py` | 128 | `# type: ignore[misc]` | Approved |
| `src/prospector_extended/tools/vulture_tool.py` | 157 | `# type: ignore[misc]` | Approved |

**Justification:** Prospector's `ToolBase` and vulture's `Vulture` classes have no type
stubs or `py.typed` marker. Mypy strict mode flags subclassing untyped classes as `[misc]`.
Cannot be fixed without upstream type stubs.

**Approved:** 2025-01-01 (initial release), updated 2026-03-04

---

## Linting Suppressions (`# noqa`)

### ARG002 — Unused method argument

| File | Line | Suppression | Status |
|------|------|-------------|--------|
| `src/prospector_extended/parsing/registry.py` | 141 | `# noqa: ARG002` | Approved |

**Justification:** `AlwaysMatcher.matches()` must accept a `data` parameter to satisfy the
`Matcher` interface contract, but always returns `True` regardless of input. The parameter
is required by the interface, not by the implementation.

**Approved:** 2025-01-01 (initial release)

---

## Security Suppressions (`# nosec`)

_No suppressions._

---

## Per-File Ignores (pyproject.toml)

These are configured in `[tool.ruff.lint.per-file-ignores]` rather than inline comments:

| Pattern | Rules | Justification |
|---------|-------|---------------|
| `tests/**/*.py` | PLR2004, PLW1510, D, PLC0415, ARG, F401, F841 | Test files: magic values in assertions, intentional subprocess usage, self-documenting names, fixture imports |
| `tests/fixtures_exempt/**/*.py` | ALL | Fixture files intentionally contain bad code for testing tools |
| `vulture_whitelist.py` | B018 | Whitelist files intentionally contain "useless" expressions to mark items as used |
| `src/.../cli.py` | PLC0415 | Deferred imports after patching prospector |
| `src/.../complexipy_tool.py` | PLC0415 | Deferred imports of optional dependency |
| `src/.../interrogate_tool.py` | PLC0415 | Deferred imports of optional dependency |
| `src/.../mypy_tool.py` | PLC0415 | Deferred imports of optional dependency |

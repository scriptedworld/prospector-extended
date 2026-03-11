# Deep Dive Code Review: prospector-extended

**Date:** 2026-03-05
**Version:** 0.2.0
**Branch:** main (20 commits)

## Executive Summary

prospector-extended is a Python library that extends Prospector with improved mypy, vulture
(whitelist support), complexipy, and interrogate tools for comprehensive Python code analysis.
The codebase is compact (1,201 LOC across 11 source files) and demonstrates mature architectural
thinking — clean module boundaries, well-chosen design patterns (Type Registry, Strategy,
Template Method), and consistent adherence to modern Python practices including strict mypy,
Google-style docstrings, and comprehensive type annotations.

The project's local quality tooling is excellent: 9 quality tools run through a unified
`poe checks` pipeline, pre-commit hooks enforce formatting and conventional commits, and
90.5% branch-inclusive test coverage validates behavior with 93 tests that favor real execution
over mocking. Code quality is the project's strongest dimension — zero messages from
prospector-extended's own analysis, strict mypy with no unjustified suppressions, and clean
ruff/bandit results.

The most significant gap is the complete absence of CI/CD. Quality gates exist only locally via
pre-commit hooks and poe tasks; there is no automated enforcement in a merge pipeline. This
means developers can push code that fails tests, has type errors, or introduces security issues.
Additionally, a single file (complexipy_tool.py at 77.1% coverage) currently blocks the
`poe checks` pipeline, and a version mismatch between pyproject.toml (0.2.0) and `__init__.py`
(0.1.0) needs resolution.

## Overall Grade: B

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Architecture | A | Clean modular design, no circular deps, well-chosen patterns |
| Code Quality | A | Zero tool messages, strict mypy, modern Python throughout |
| Security | A | Bandit clean, safe subprocess handling, Pydantic validation |
| Test Quality | B | 93 tests / 90.5% coverage, but one file below threshold |
| Error Handling | B | Good specificity and degradation, but no timeouts on external calls |
| Performance | A | No issues detected, efficient parsing, smart short-circuits |
| Documentation | B | Comprehensive suite but missing CI/CD docs and troubleshooting guide |
| Dependency Health | B | Well-managed with hash-verified lock file, but 3 unsuppressed CVEs |
| Infrastructure | D | No CI/CD pipeline; pre-commit hooks provide only partial enforcement |

### Rating Scale
- **A** — Excellent. Low complexity, well-structured, minimal issues.
- **B** — Good. Minor issues, solid fundamentals.
- **C** — Acceptable. Some technical debt, functional but with gaps.
- **D** — Concerning. Significant issues requiring attention.
- **F** — Critical. Major problems, high risk.

## Findings Summary

| Severity | Count | Areas |
|----------|-------|-------|
| Critical | 1 | Infrastructure (no CI/CD pipeline) |
| Must-Fix | 3 | Version mismatch, coverage threshold failure, check task sequencing |
| High | 6 | CVEs (transitive), silent tool failures, no timeouts, CLI docs, regex fragility, vulture API compat |
| Recommended | 12 | Type hint clarity, validator strictness, pre-commit gaps, untested paths, doc gaps |
| Nit | 6 | Error message paths, assertion specificity, fixture scope, changelog format |

## Architecture Assessment

### Strengths

**Excellent modular design with clear separation of concerns:**
- Parsing infrastructure (`parsing/models.py` + `parsing/registry.py`) is completely decoupled
  from tools
- Tool base class (`ExtendedToolBase`) provides consistent interface for file-by-file analyzers
- Each tool (ComplexipyTool, InterrogateTool, VultureTool, MypyTool) is independent
- Dependency direction is acyclic: `cli` -> `tools` -> `base`, parsing is separate
- No circular dependencies

**Strong architecture patterns:**
- Type Registry pattern (`parsing/registry.py`) provides extensible polymorphic JSON parsing
  without coupling to specific tools
- SchemaMatcher abstraction enables priority-based schema dispatching (TypeTagMatcher,
  DiscriminatorMatcher, RequiredFieldsMatcher, PredicateMatcher)
- CLI patch pattern (`cli.py`) allows runtime tool injection without modifying prospector internals
- Layered error handling with graceful fallbacks (e.g., mypy JSON -> text parsing, vulture
  confidence filtering)

**Well-designed error boundaries:**
- Proper validation at system boundaries (JSON parsing, tool output parsing)
- Comprehensive exception handling with specific error types
- Tools silently return empty message lists on expected errors (encoding, file not found, parse
  errors), preserving other tools' output
- Stderr messages from mypy are captured and converted to Message objects

**Modern Python practices throughout:**
- Consistent use of `from __future__ import annotations` across files
- Modern generic syntax (`list[str]`, `dict[str, Any]`) throughout
- Walrus operator used effectively in conditionals
- `TYPE_CHECKING` guards for imports that don't execute at runtime

### Areas Worth Noting

**[Must-Fix] Version inconsistency:**
- `pyproject.toml:6` declares version `"0.2.0"`
- `src/prospector_extended/__init__.py:42` declares `__version__ = "0.1.0"`
- Commitizen expects these to be synced (configured in `pyproject.toml:267-270`)

**[Recommended] ExtendedToolBase not used by MypyTool:**
- MypyTool inherits directly from `ToolBase` (`mypy_tool.py:128`) rather than `ExtendedToolBase`
- This is intentional and documented: mypy runs once on all files, not file-by-file
- Consider documenting this pattern if other all-at-once tools are added in the future

## Security Assessment

### Strengths

- **No hardcoded secrets** — `.gitignore` covers `.env` files and sensitive data; no credentials
  in source
- **Safe subprocess handling** — Uses `mypy.api.run()` instead of shell execution, avoiding
  injection attacks; environment variable management is careful with save/restore pattern
- **Input validation via Pydantic** — `parsing/models.py:34-44` validates line numbers and
  columns with field validators before use
- **Safe deserialization** — Uses `json.loads()` (safe) throughout; no pickle or unsafe YAML
- **Security scanning configured** — Bandit integrated in quality gates via prospector-extended;
  xray-audit for CVE scanning at pre-push
- **Supply chain integrity** — `uv.lock` includes cryptographic hashes for all 89 packages
- **Strict type safety** — Full strict mypy with documented overrides for untyped third-party
  libraries only

### Findings

**[High] 3 unsuppressed CVEs in transitive dependencies** (from xray-audit):
- CVE-2022-42969 in py:1.11.0 — ReDoS in Subversion parser (disputed by multiple third parties)
- CVE-2018-20225 in pip:25.3 — Unintended package installation via `--extra-index-url`
- CVE-2026-1703 in pip:25.3 — Path traversal during wheel extraction (limited impact)

Root cause: `py` and `pip` are transitive dependencies from test/build tooling, not used in
application code. Consider documenting suppression rationale if continued acknowledgment is
intentional.

**[Recommended] Mypy command options validated but could be stricter:**
- `mypy_tool.py:27-113` defines `VALID_OPTIONS` frozenset, but options are not validated beyond
  membership; unexpected combinations could theoretically cause issues

## Error Handling and Resilience

### Strengths

- **Specific exception handling** — Targeted catches throughout: `SyntaxError`,
  `UnicodeDecodeError`, `OSError`, `ValueError`, `AttributeError` with comments explaining
  each (`complexipy_tool.py:50-57`, `interrogate_tool.py:81-86`)
- **Graceful degradation on import failures** — Optional dependencies handled gracefully:
  returns empty list if complexipy/interrogate not importable
- **Encoding error handling** — Robust handling in `vulture_tool.py:86-96` with proper
  distinction between source and whitelist file errors
- **JSON parsing fallback** — Attempts JSON parsing, falls back to text format
  (`parsing/models.py:128-139`)
- **Resource cleanup** — Environment variable save/restore uses try/finally
  (`mypy_tool.py:217-228`)
- **Message filtering** — Disabled code filtering respects configuration across all tools

### Findings

**[High] Silent failures in tools — no logging:**
- `complexipy_tool.py:50-57`, `interrogate_tool.py:81-86`: When exceptions occur (syntax errors,
  import failures), tools return empty lists without logging
- Impact: Files with real problems are silently skipped; users see no indication of analysis gaps
- Recommendation: Log at DEBUG level when skipping files due to errors

**[High] No timeout configuration on external tool execution:**
- `mypy_tool.py:222`: `mypy.api.run(args)` has no timeout
- `complexipy_tool.py:48`: `file_complexity()` has no timeout
- `interrogate_tool.py:80`: `InterrogateCoverage()` has no timeout
- Risk: Malformed Python files or pathological input could hang analysis indefinitely

**[High] VultureTool attribute compatibility across versions:**
- `vulture_tool.py:140-143`: Works around vulture API variations (`item.file` vs
  `item.filename`, `item.lineno` vs `item.first_lineno`)
- Defensive but fragile; no documentation of supported vulture version range

**[Recommended] Incomplete error messages in complexipy:**
- `complexipy_tool.py:78`: `e.offset` could be `None` (SyntaxError.offset is optional)
- Character parameter passed without null-checking; base class handles `None` but implicitly

**[Recommended] Inconsistent error handling between tools:**
- `complexipy_tool.py` and `interrogate_tool.py` catch `AttributeError` as internal errors
- `mypy_tool.py` doesn't explicitly catch these
- Suggests untested assumptions about tool APIs

## Performance

### Strengths

- **Smart short-circuit paths:** TypeRegistry checks `line.startswith("{")` before JSON parsing;
  MypyTool returns `[]` for empty paths; ComplexipyTool catches ImportError early
- **Efficient parsing:** Walrus operator for parse-and-check; compiled regex at module level
  (`_MYPY_TEXT_PATTERN`); no unnecessary intermediate collections
- **Resource management:** Environment variable cleanup uses try/finally; no unbounded
  collections
- **Reasonable algorithmic complexity:** Schema matching is O(n) per line where n=number of
  schemas (typically 1-5); all operations linear or better

### Findings

**No performance issues detected.** All operations are linear or better. Tools properly delegate
to subprocess/library calls rather than reimplementing analysis. The only potential improvement
would be version-gating the Python 3.14+ `NO_COLOR` workaround, but this has negligible cost.

## Code Quality

### What's Done Well

- **Type safety is rigorous:** Strict mypy, complete annotations, modern syntax (`list[str]`
  not `List[str]`), justified `type: ignore` comments only for untyped third-party libraries
- **Docstrings follow Google style consistently:** All public classes and functions documented;
  Args, Returns, Raises sections present; 80%+ interrogate score
- **Error handling is intentional, not defensive:** Try-except blocks catch specific known
  exceptions with comments explaining each type
- **Code organization is clean:** Well-distributed module sizes (24-385 lines), largest function
  58 lines, max nesting 6 levels
- **Naming consistency:** PascalCase classes, snake_case functions, kebab-case config options
  mapped to snake_case internally
- **No dead code:** vulture reports 0 findings; no commented-out code blocks
- **No mutable default arguments:** All defaults are immutable or None

### Specific Code Observations

**[High] Regex pattern assumes filename format:**
- `parsing/models.py:63`: `_MYPY_TEXT_PATTERN` uses non-greedy `(.+?)` which could match too
  little if filename contains colons (e.g., Windows paths, edge cases)
- Pattern is correct for typical use but not robust against unusual filenames

**[Recommended] Character parameter type hint ambiguity:**
- `tools/base.py:104`: `character: int | None = 0` — default is `0` but type allows `None`;
  semantics unclear (is `None` different from `0`?)
- Consider `character: int = 0` if None has no distinct meaning

**[Recommended] MypyJsonOutput field validators are lenient:**
- `parsing/models.py:34-38`: `ensure_positive_line()` silently converts `line=0` to `line=1`
- Mypy should never return line 0; silently masking could hide upstream changes

**[Recommended] Mypy NO_COLOR workaround could use version check:**
- `mypy_tool.py:215-228`: Handles Python 3.14+ argparse TTY detection issue
- Consider a version check to avoid unnecessary env manipulation on older Python

## Design Patterns

**Patterns Used (Well):**

1. **Type Registry** (`parsing/registry.py`) — Extensible polymorphic JSON parsing inspired by
   cattrs structure hooks
2. **Strategy** (SchemaMatcher hierarchy) — Different matching strategies with priority ordering
3. **Builder** (implicit in MypyTool) — Incremental command-line option construction
4. **Template Method** (ExtendedToolBase) — Subclasses implement `_configure_options` and
   `_analyze_file`; `run()` orchestrates
5. **Adapter** (ProspectorVultureExtended) — Adapts vulture's `scavenge()` for whitelist support
6. **Decorator** (CLI `patch_prospector_tools`) — Modifies prospector's TOOLS dict at runtime

**SOLID Compliance:**
- **Single Responsibility:** Each tool handles one tool; registry handles one format
- **Open/Closed:** TypeRegistry is open for extension (new schemas via `register()`), closed
  for modification
- **Liskov Substitution:** ExtendedToolBase subclasses are substitutable; MypyTool follows
  ToolBase contract
- **Interface Segregation:** Small focused interfaces (SchemaMatcher, ExtendedToolBase)
- **Dependency Inversion:** Tools depend on abstractions (ToolBase, FileFinder, ProspectorConfig)

## Test Quality

### Strengths

- **Comprehensive fixture strategy:** `conftest.py` provides reusable fixtures; real code files
  in `tests/fixtures_exempt/` exercise actual tool analysis
- **Mock discipline:** Custom mock classes (MockProspectorConfig, MockFileFinder) are minimal
  and match actual interfaces; real behavior testing preferred
- **Strong edge case coverage:** Empty inputs, nonexistent files, disabled codes, threshold
  variations all tested
- **Good test independence:** No interdependencies; fresh instances and isolated mocking
- **Clear naming:** Descriptive names like `test_run_on_complex_file`,
  `test_disabled_code_skipped`
- **Message validation:** Tests verify message properties (source, code, location, content)
  against actual Prospector Message objects

### Test Organization

| File | Tests | Category | Strategy |
|------|-------|----------|----------|
| test_base_tool.py | 11 | Unit | Concrete subclass of ExtendedToolBase |
| test_cli.py | 9 | Unit | Patch registration and main() integration |
| test_complexipy_tool.py | 8 | Integration | Fixture files with real complexity analysis |
| test_interrogate_tool.py | 9 | Integration | Fixture files with docstring detection |
| test_mypy_tool.py | 17 | Integration + Edge | JSON/text conversion, formatting, unconfigured behavior |
| test_parsing.py | 28 | Unit + Integration | Models, registry, matchers, JSON schema validation |
| test_vulture_tool.py | 11 | Integration + Edge | Whitelist handling, confidence filtering, file scanning |

Test density: 93 tests / 494 statements = 0.19 tests per statement.
Test-to-code LOC ratio: 1,028 / 1,201 = 0.86:1.

### Findings

**[High] complexipy_tool.py coverage gap (77.1% — BELOW 80% threshold):**
- Missing coverage for lines 44-45 (ImportError fallback), 50-57 (exception handling for
  SyntaxError, OSError, UnicodeDecodeError, ValueError, AttributeError), and line 74
- No test for missing complexipy import, syntax error recovery, file access errors, or
  encoding errors
- This is the only file below threshold and currently blocks `poe checks`

**[Recommended] parsing/registry.py serialization methods untested (88.4%):**
- `to_dict()`, `save()`, `load()` at lines 290-314 have no direct tests
- `parse_output()` tested indirectly via `parse_mypy_output` but not directly
- Low risk: serialization paths are non-critical during tool execution

**[Recommended] PredicateMatcher untested:**
- `registry.py:122-136` — exists as a matcher strategy but has zero test coverage
- Valid matcher class but appears unused in current codebase

**[Nit] Test assertion specificity:**
- Some assertions use `any(... in ...)` patterns instead of exact value matching
  (`test_base_tool.py:84-85`, `test_complexipy_tool.py:102-103`)
- Acceptable for version-sensitive tool output but reduces precision

## Dependency Health

### Overview

6 direct runtime dependencies, 9 dev dependencies, all actively used. Lock file covers 89
packages with cryptographic hash verification. Dependencies are reputable and maintained.

### Findings

**[High] 3 unsuppressed CVEs in transitive dependencies:**
- CVE-2022-42969 (py:1.11.0) — Disputed ReDoS, not in application code
- CVE-2018-20225 (pip:25.3) — Package installation attack vector, moderate severity
- CVE-2026-1703 (pip:25.3) — Path traversal, low severity

All are in transitive build/test tooling dependencies, not application code. Consider formal
suppression with documented rationale.

**[Recommended] Optional dependencies declared as runtime:**
- Mypy, complexipy, and interrogate are runtime deps but imported only within try/except
  blocks after tool instantiation
- Pattern is intentional (graceful degradation) but means packages must be present even if
  tools aren't configured

### Metrics

| Metric | Value |
|--------|-------|
| Runtime dependencies | 6 |
| Dev dependencies | 9 |
| Vendored dependencies | Yes (vendor/*.whl) |
| Lock file present | Yes (uv.lock) |
| Hash verification | 100% of 89 packages |
| Unsuppressed CVEs | 3 (all transitive) |

## Project Infrastructure

### Quality Gates

| Tool | Local | Pre-commit | CI/CD |
|------|-------|-----------|-------|
| Ruff (lint) | `poe lint` | ruff (--fix) | — |
| Ruff (format) | `poe format-check` | ruff-format | — |
| Mypy | `poe types` | — | — |
| Bandit | `poe security` | — | — |
| Pytest + coverage | `poe test-coverage` | — | — |
| Vulture | `poe quality` | — | — |
| Complexipy | `poe quality` | — | — |
| Interrogate | `poe quality` | — | — |
| Pylint (duplication) | `poe quality` | — | — |
| xray-audit (CVE) | `poe xray` | xray-audit (pre-push) | — |
| Commitizen | — | commitizen (commit-msg) | — |

The CI/CD column is entirely empty — no automated pipeline exists.

### CI/CD Pipeline

**[Critical] No CI/CD pipeline exists.** No `.gitlab-ci.yml`, `.github/workflows/`, or
equivalent CI configuration was found. Quality gates are enforced only locally via pre-commit
hooks and manual `poe checks` execution.

Impact: Code can be pushed that fails tests, has type errors, has security issues, violates
quality thresholds, or introduces duplicated code — none of this is caught automatically before
merge.

### Pre-commit Hooks

10 hooks configured across 3 stages:

| Hook | Stage | Purpose |
|------|-------|---------|
| trailing-whitespace | commit | Trim trailing whitespace |
| end-of-file-fixer | commit | Ensure newline at EOF |
| check-yaml | commit | Validate YAML syntax |
| check-toml | commit | Validate TOML syntax |
| check-json | commit | Validate JSON syntax |
| check-added-large-files | commit | Prevent large file commits |
| ruff (lint + fix) | commit | Auto-fix linting issues |
| ruff-format | commit | Format verification |
| commitizen | commit-msg | Enforce Conventional Commits |
| xray-audit | pre-push | CVE vulnerability scanning |

Gaps: No type checking (mypy), no test execution, no docstring validation, no comprehensive
quality scanning (prospector-extended).

### Findings

**[Must-Fix] Coverage enforcement blocks pipeline:**
- `poe checks` aborts at `validate-coverage` because complexipy_tool.py is at 77.14%
  (threshold: 80%)
- `format-check` and `quality` never run in the same invocation

**[Must-Fix] Check task sequencing:**
- `pyproject.toml:303`: `checks = ["test-coverage", "format-check", "quality"]`
- When test-coverage fails, format-check and quality are skipped
- Developers don't see all issues at once; consider reordering (format-check first) or
  running independently

**[Recommended] Pre-commit doesn't run tests:**
- A developer can commit code that breaks tests as long as formatting passes
- Recommend adding pytest to pre-commit or relying on CI/CD (once it exists)

### Metrics

| Metric | Value |
|--------|-------|
| CI/CD jobs | 0 |
| Quality tools configured | 9 (via prospector-extended) |
| Pre-commit hooks | 10 |
| Poe tasks | 18 |
| Vulnerability scanning in CI | No |

## Documentation

### Strengths

- **Comprehensive architecture documentation:** `docs/ARCHITECTURE.md` covers internal design,
  data flow, patterns, and 3 ADRs
- **Full documentation suite:** README.md, ARCHITECTURE.md, DEVELOPMENT.md, SUPPRESSIONS.md,
  SECURITY.md, CHANGELOG.md, PROJECT.md, REQUIREMENTS.md, STATUS.md, TODO.md
- **Suppression audit trail:** Every `type: ignore` documented in SUPPRESSIONS.md with
  justification and approval date
- **Requirements traceability:** FR-001 through FR-006 with acceptance criteria checkboxes
- **Keep a Changelog format:** CHANGELOG.md follows standard versioning conventions

### Gaps or Risks

**[High] No CI/CD documentation:**
- DEVELOPMENT.md has no section on CI/CD setup or pipeline
- New contributors won't understand how quality gates are enforced (answer: they aren't,
  beyond pre-commit)

**[High] CLI documentation lacks usage examples:**
- README.md shows basic invocation but missing: excluding specific tools, custom
  `.prospector.yaml` location, exit codes, piping output

**[Recommended] Architecture docs assume Prospector knowledge:**
- Data flow references Prospector internals without explaining config loading or tool
  path resolution

**[Recommended] No troubleshooting guide:**
- Missing guidance for: mypy import errors on untyped dependencies, vulture false positive
  management, xray-audit latency

**[Recommended] No performance/scalability guidance:**
- No documentation on analysis time for medium/large codebases, memory requirements, or
  caching behavior

**[Nit] CHANGELOG.md "Unreleased" section has partial entries:**
- Mix of completed features under "Unreleased" heading; consider versioning or clearer grouping

## Design Decisions Worth Highlighting

1. **Runtime tool patching over forking Prospector** — `cli.py` patches `prospector.tools.TOOLS`
   dict at runtime rather than forking or monkey-patching Prospector source. This preserves
   compatibility and allows the library to track upstream changes.

2. **File-by-file vs all-at-once tool execution** — ExtendedToolBase provides file-by-file
   analysis (suitable for complexipy, interrogate, vulture), while MypyTool inherits directly
   from ToolBase for all-at-once execution. The split acknowledges that type checking is
   fundamentally cross-file.

3. **Type Registry for polymorphic parsing** — Rather than hard-coding mypy output format
   handling, the project uses a generic registry with schema matchers. This is more complex
   than needed for mypy alone but anticipates future tools with varied output formats.

4. **Pydantic for tool output validation** — External tool output (JSON from mypy) is validated
   through Pydantic models with field validators rather than trusted as correct. This catches
   format changes in upstream tools early.

5. **Deferred imports for optional tools** — Tool-specific libraries are imported inside methods
   (not at module level), allowing graceful degradation if a tool isn't installed. Declared
   as runtime deps to ensure they're available by default.

6. **Vulture whitelist via subclass** — ProspectorVultureExtended extends Vulture directly and
   overrides `scavenge()` to pre-scan whitelist files. This is cleaner than post-filtering
   results and leverages vulture's own "used" tracking.

## Technical Debt Assessment

### Estimated Debt

Low overall debt for a 20-commit, 1,201-LOC project. The codebase was built with quality
tooling from the start, so debt is concentrated in infrastructure gaps rather than code quality.

### Highest-Cost Areas

1. **No CI/CD pipeline** [Critical] — Highest-impact gap. Effort: 2-4 hours for basic
   GitLab/GitHub Actions setup with check, test, quality, and security stages. Blocks
   confidence in merge quality.

2. **complexipy_tool.py coverage gap** [Must-Fix] — Blocks `poe checks`. Effort: 30 minutes
   to add error path tests (mock ImportError, fixture with SyntaxError, mock OSError).

3. **Version mismatch** [Must-Fix] — `__init__.py` says 0.1.0, pyproject.toml says 0.2.0.
   Effort: 1 minute to fix, but indicates commitizen bump wasn't run or wasn't configured
   correctly.

4. **Check task sequencing** [Must-Fix] — `poe checks` aborts on first failure. Effort:
   5 minutes to reorder or restructure poe tasks for better developer feedback.

5. **No timeouts on external tool execution** [High] — mypy, complexipy, interrogate have
   no timeout. Effort: 30 minutes to add signal-based or threading-based timeout wrappers.

### Duplication

No significant duplication detected. Pylint duplicate-code checker is configured
(`pyproject.toml:225-234`, min-similarity-lines=4) and runs as part of `poe quality` via
prospector-extended. 0 messages reported.

## Quantitative Summary

| Category | Metric | Value |
|----------|--------|-------|
| **Code** | Source LOC (Python) | 1,201 |
| | Test LOC (Python) | 1,028 |
| | Test-to-code ratio | 0.86:1 |
| | Source files | 11 |
| | Test files | 14 (7 test + 6 fixture + 1 conftest) |
| | Total tests | 93 |
| | Branch-inclusive coverage | 90.5% |
| | Duplication ratio | 0% (pylint) |
| **Complexity** | Cyclomatic complexity max | ≤ 10 (threshold, 0 violations) |
| | Cognitive complexity max | ≤ 15 (threshold, 0 violations) |
| | Max function length | 58 lines (schema_from_fields) |
| | Deepest nesting level | 6 (vulture_tool.scavenge) |
| | Public functions/classes | ~25 |
| | Private/internal functions | ~10 |
| | Functions with >3 parameters | 2 |
| **Dependencies** | Runtime dependencies | 6 |
| | Dev dependencies | 9 |
| | Vendored dependencies | Yes |
| | Lock file status | Present, hash-verified (89 packages) |
| | Known vulnerabilities | 3 unsuppressed (all transitive) |
| **Infrastructure** | CI/CD jobs | 0 |
| | Quality tools configured | 9 |
| | Documentation files | 10 |
| | Pre-commit hooks | 10 |
| | Vulnerability scanning in CI | No |

## Overall Assessment

prospector-extended earns a **B** — a well-built library with strong code quality fundamentals
and a mature local development experience, held back by the absence of CI/CD enforcement.

The strongest dimensions are Architecture (A) and Code Quality (A). The codebase demonstrates
discipline: strict typing, comprehensive docstrings, intentional error handling, zero tool
violations, and clean design patterns. For a 1,201-LOC library, the engineering quality is high.

The weakest dimension is Infrastructure (D). Without CI/CD, quality gates are advisory — they
exist locally but nothing prevents unvalidated code from reaching the repository. This is the
single most impactful improvement the project could make: implementing a CI/CD pipeline that
runs `poe checks` on every push would close the largest gap in the project's quality story
and move the overall grade toward A.

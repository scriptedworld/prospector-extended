# Deep Dive Code Review: Prospector Extended

**Date:** 2026-03-04
**Version:** 0.2.0
**Branch:** main (2 commits)
**Reviewer:** Claude Code (automated deep analysis)

## Executive Summary

Prospector Extended is a Python static analysis aggregator that extends
[Prospector](https://github.com/prospector-dev/prospector) with improved mypy
integration, vulture whitelist support, complexipy cognitive complexity
checking, and interrogate docstring coverage. At ~1,500 LOC across 11 source
files, it's a focused, well-architected tool with excellent code quality
fundamentals — complete type annotations, 100% docstring coverage, and clean
separation of concerns via a strategy/template-method architecture.

The project's strongest dimensions are its architecture (clean extension model,
no circular dependencies, SOLID compliance) and code quality (strict mypy,
Google-style docstrings, zero anti-patterns). Its weakest areas are
infrastructure (no CI/CD pipeline, no pre-commit hooks — all enforcement is
manual) and test coverage (46 tests but three major modules completely
untested: CLI, VultureTool, ExtendedToolBase). Documentation is solid at the
README level but lacks CHANGELOG, SECURITY, and contributor guides.

Overall, this is well-engineered code that needs operational infrastructure to
match its code quality.

## Overall Grade: B

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Architecture | A | Clean extension model, strategy/template patterns, no circular deps |
| Code Quality | A- | Complete typing, docstrings, consistent style; 4 minor tool findings |
| Security | A | 0 bandit issues, safe deserialization, no hardcoded secrets |
| Test Quality | C | 46 tests but CLI, VultureTool, ExtendedToolBase untested |
| Error Handling | B | Graceful degradation but silent failures mask problems |
| Performance | A | No issues, efficient algorithms, proper resource management |
| Documentation | C | Good README but missing CHANGELOG, PROJECT.md, SECURITY.md |
| Dependency Health | B | Lock file with hashes but loose version constraints |
| Infrastructure | D | No CI/CD, no pre-commit hooks, all enforcement manual |

### Rating Scale
- **A** — Excellent. Low complexity, well-structured, minimal issues.
- **B** — Good. Minor issues, solid fundamentals.
- **C** — Acceptable. Some technical debt, functional but with gaps.
- **D** — Concerning. Significant issues requiring attention.
- **F** — Critical. Major problems, high risk.

## Findings Summary

| Severity | Count | Areas |
|----------|-------|-------|
| Critical | 2 | Infrastructure (no CI/CD, no pre-commit) |
| Must-Fix | 4 | Test coverage gaps (CLI, VultureTool, ExtendedToolBase), quality violations |
| High | 5 | Silent error handling, missing docs, test error paths, matcher testing |
| Recommended | 7 | Validation errors, import surfacing, config validation, version constraints |
| Nit | 5 | Import order, error formatting, test naming, sample file location, homepage URL |

## Architecture Assessment

### Strengths

1. **Excellent Separation of Concerns** — The codebase divides cleanly into three
   layers: `parsing/` (schema validation, JSON/text parsing), `tools/` (Prospector
   tool implementations), and `cli.py` (entry point, tool registration). Each module
   has a single responsibility.

2. **Strong Extension Architecture** — `ExtendedToolBase` (`base.py:26-134`)
   provides a template method pattern where subclasses implement `_configure_options()`
   and `_analyze_file()`. This accommodates file-by-file tools (complexipy,
   interrogate) while mypy and vulture use whole-project analysis via different
   base classes.

3. **Clean Dependency Flow** — No circular dependencies. Imports follow
   `cli → tools → parsing` with no reverse paths. `TYPE_CHECKING` blocks
   prevent circular imports at runtime.

4. **Polymorphic Parsing Design** — The `TypeRegistry` (`registry.py:189-314`)
   implements priority-sorted matcher dispatch: TypeTagMatcher (100),
   DiscriminatorMatcher (80), PredicateMatcher (60), RequiredFieldsMatcher (50),
   AlwaysMatcher (0). This is extensible without modifying existing matchers.

5. **Single Registration Point** — Tool patching in `cli.py:32-37` provides
   one place to add/remove tool integrations.

### Areas Worth Noting

1. **Typing Compromises (Justified)** — Three `type: ignore[misc]` suppressions
   exist because Prospector's `ToolBase` is untyped. These are documented inline
   and unavoidable given the upstream library.

2. **Two Base Class Patterns** — File-by-file tools inherit `ExtendedToolBase`
   while whole-project tools (mypy, vulture) inherit `ToolBase` directly. This is
   a pragmatic design choice given how tools interact with Prospector's runner,
   but creates two integration patterns to learn.

## Security Assessment

### Strengths

1. **Zero Bandit Findings** — Security scan of all source code (1,842 LOC) found
   no issues. No hardcoded secrets, no injection vectors, no unsafe deserialization.

2. **Safe External Process Integration** — Uses Python APIs directly
   (`mypy.api.run()`) rather than shell commands. No `shell=True`,
   `os.system()`, or subprocess calls with untrusted input.

3. **Pydantic Validation** — All JSON parsing uses `model_validate()` with
   explicit validators ensuring safe defaults (line numbers ≥1, columns ≥0)
   at `models.py:34-44`.

4. **Environment State Isolation** — `mypy_tool.py:162-181` saves and restores
   `NO_COLOR` in a try-finally block, preventing environment leakage.

### Findings

1. **[Recommended] Missing Error Context in Silent Failures** —
   `complexipy_tool.py:57` and `interrogate_tool.py:83` catch broad exceptions
   (`OSError, UnicodeDecodeError, ValueError, AttributeError`) and return empty
   lists silently. Users cannot distinguish "no issues found" from "analysis
   failed." Add structured logging at DEBUG level for failed files.

2. **[Recommended] Validation Error Masking** — `models.py:134-137` catches both
   `json.JSONDecodeError` and `ValueError` together. Pydantic validation failures
   (ValueError) are indistinguishable from malformed JSON. Consider separating
   handlers to aid troubleshooting.

3. **[Recommended] Vulture Attribute Access Fragility** —
   `vulture_tool.py:144` uses `hasattr(item, "lineno")` but falls through to
   `item.first_lineno` without a safety net. If vulture removes both attributes
   in a future version, this raises an uncaught `AttributeError`. Use
   `getattr(item, 'first_lineno', 1)` as fallback.

4. **[Recommended] Path Normalization** — Tool file paths use
   `filepath.absolute()` but not `filepath.resolve()`, which doesn't normalize
   symlinks. Document security assumptions about path handling.

## Error Handling and Resilience

### Strengths

1. **Graceful Degradation** — All tool `_analyze_file()` methods return empty
   lists on errors, allowing Prospector to continue with results from other tools.

2. **Specific Exception Catching** — Uses targeted exception types (`SyntaxError`,
   `OSError`, `UnicodeDecodeError`, `ImportError`) rather than bare `except`.

3. **Resource Cleanup** — File operations use Pathlib's `.read_text()` /
   `.write_text()` (internal cleanup); environment variable restoration uses
   try-finally (`mypy_tool.py:173-181`).

4. **Pydantic Field Validators** — Defensive validators coerce invalid values
   to safe defaults: `max(1, v)` for line numbers, `max(0, v)` for columns
   (`models.py:36-44`).

### Findings

1. **[High] Mypy Exit Code Ignored** — `mypy_tool.py:175` discards mypy's exit
   code (`stdout, stderr, _ = mypy.api.run(args)`). If mypy fails partially,
   results appear complete. Check exit code or stderr to detect incomplete analysis.

2. **[High] Silent Tool Dependency Failures** — `complexipy_tool.py:44` and
   `interrogate_tool.py:73` catch `ImportError` and return empty lists without
   any indication that the tool is unavailable. Users can't tell if a tool found
   no issues or simply wasn't installed.

3. **[High] No Timeout on External Tools** — Mypy, complexipy, and interrogate
   execution has no timeout configuration. A pathological file could hang
   analysis indefinitely.

4. **[Recommended] Stderr Not Fully Processed** — `mypy_tool.py:158-159` only
   parses stderr lines starting with `"mypy:"` or `"error:"`. Other diagnostic
   messages (warnings, deprecations) are silently dropped.

5. **[Nit] Inconsistent Error Message Formatting** — `vulture_tool.py:107,150`
   mixes f-strings and `.format()` style. Standardize on f-strings.

## Performance

### Strengths

1. **Efficient JSON Parsing** — `models.py:109-159` uses single-pass line
   processing with fast-path checks (`startswith`) to skip non-JSON lines.

2. **Smart Schema Dispatch** — `registry.py:250-280` tries matchers in priority
   order with early exit on match.

3. **No Unbounded Collections** — All data structures are sized by input.
   No accumulating caches or growing buffers.

4. **Appropriate Tool Invocation** — Mypy runs once with all files
   (`mypy_tool.py:162-176`); Vulture uses a single instance. No N+1 patterns.

### Findings

No performance issues detected. The codebase demonstrates efficient,
input-proportional resource usage throughout.

## Code Quality

### What's Done Well

1. **Complete Type Annotations** — All function signatures fully typed with
   modern syntax (`list[str]`, `X | None`). Strict mypy with
   `disallow_untyped_defs = true`.

2. **100% Docstring Coverage** — Google-style docstrings on all public
   functions/classes with Args/Returns/Raises sections. Interrogate confirms
   100% coverage.

3. **Zero Anti-Patterns** — No mutable default arguments, no bare except
   clauses, no global state, no commented-out code, no unused imports.

4. **Consistent Style** — 150-char line length, snake_case functions,
   PascalCase classes, sorted imports (stdlib → third-party → local).

5. **Small Functions** — Maximum function length is 38 lines. Average ~22
   lines. No function exceeds 60 lines.

### Specific Code Observations

1. **[Must-Fix] 4 Quality Baseline Violations** — All in `vulture_tool.py`:
   - Line 35: mypy `misc` — Class cannot subclass "Vulture" (has type "Any")
   - Line 95: mypy `unused-ignore` — Stale `type: ignore` comment
   - Line 18: ruff `I001` — Import block unsorted
   - Line 183: ruff `ARG002` — Unused method argument `found_files`

2. **[Recommended] Suppression Documentation Missing** — The project has ~5
   `type: ignore` comments but no `docs/SUPPRESSIONS.md` documenting
   justifications per CLAUDE.md guidelines.

3. **[Nit] Import Order** — `vulture_tool.py:18-28` has vulture import after
   prospector imports. Fix via `ruff check --fix`.

## Design Patterns

**Patterns Used Well:**

1. **Strategy Pattern** — `SchemaMatcher` hierarchy (`registry.py:58-147`)
   with `TypeTagMatcher`, `DiscriminatorMatcher`, `RequiredFieldsMatcher`,
   `PredicateMatcher`, `AlwaysMatcher`. Each encapsulates a matching algorithm,
   sortable by priority.

2. **Template Method** — `ExtendedToolBase` (`base.py:26-134`) defines the
   workflow skeleton; subclasses implement `_configure_options()` and
   `_analyze_file()`.

3. **Builder Pattern** — `TypeRegistry` (`registry.py:189-314`) with fluent
   `register()` returning `self`, plus `save()`/`load()` for persistence.

4. **Adapter Pattern** — `ProspectorVultureExtended` (`vulture_tool.py:35-154`)
   adapts Vulture's interface to Prospector's `Message` format, adding
   whitelist support.

5. **Registry Pattern** — Tool registration in `cli.py:32-37` provides a
   single point of control.

**SOLID Compliance:**
- **Single Responsibility:** Each module has one reason to change
- **Open/Closed:** Extensible via `SchemaMatcher`, `ExtendedToolBase`
- **Liskov Substitution:** Subclasses properly implement interfaces
- **Interface Segregation:** Small interfaces (`SchemaMatcher` has 2 methods)
- **Dependency Inversion:** Tools depend on abstractions (`ToolBase`)

**No Anti-Patterns Detected:** No God classes, circular deps, global state, or
excessive mutation.

## Test Quality

### Strengths

1. **Well-organized test structure** — Tests grouped by class into logical
   categories (Configuration, Execution, Parsing, Matchers).

2. **Real behavior testing** — Tests exercise real tool execution on actual
   fixture files rather than mocking subprocess calls.

3. **Good assertion coverage** — Tests use specific value assertions
   (`assert result.file == "test.py"`) rather than truthiness checks.

4. **Comprehensive parsing tests** — 19 tests covering validators, matchers,
   schema generation, and JSON/text parsing.

5. **Boundary value testing** — Tests cover edge cases like empty file lists,
   line number coercion (0→1), negative column numbers.

### Test Organization

| File | Tests | Category | Strategy |
|------|-------|----------|----------|
| test_complexipy_tool.py | 8 | Config, Execution | Unit with fixtures; real analysis |
| test_interrogate_tool.py | 9 | Config, Execution | Unit with fixtures; real analysis |
| test_mypy_tool.py | 10 | Config, Execution, Output | Unit; real mypy; JSON→Message mapping |
| test_parsing.py | 19 | Validation, Registry, Matchers | Unit; comprehensive schema/regex |
| **Total** | **46** | | |

Test density: 46 tests / 1,504 source statements = 0.031 tests per statement.
Test-to-code LOC ratio: ~1:2 (752 test LOC : 1,504 source LOC).

### Findings

1. **[Must-Fix] No Tests for CLI Module** — `cli.py` (57 LOC) is completely
   untested. `patch_prospector_tools()` and `main()` are the public API entry
   points with zero coverage.

2. **[Must-Fix] No Tests for VultureTool** — `vulture_tool.py` (229 LOC)
   including `ProspectorVultureExtended` and `VultureTool` classes has no test
   file. This is a core tool replacement with no regression tests.

3. **[Must-Fix] No Tests for ExtendedToolBase** — `base.py` (133 LOC) is
   tested indirectly through subclasses but the base class itself (ignore_codes
   handling, Location creation, message suppression) is never directly verified.

4. **[High] Incomplete Error Path Coverage** — Tool tests verify successful
   execution but not error conditions: no tests for invalid file paths,
   subprocess failures, or malformed tool output.

5. **[High] Matcher Priority Ordering Not Tested** — Matcher classes define
   `priority()` methods but no test verifies higher-priority matchers are tried
   first when both match.

6. **[High] Schema Fingerprint Drift Untested** — `compute_fingerprint()` is
   tested for determinism but not that fingerprint changes when schema changes.
   `MYPY_SCHEMA_FINGERPRINT` sentinel is never validated against computed value.

7. **[High] Fixture Isolation Weakness** — If fixture files are deleted, tests
   silently pass (return empty result lists). Tests should verify fixture files
   exist before asserting on results.

8. **[Recommended] Test Names Lack Specificity** — Names like
   `test_default_threshold()` don't indicate expected outcome. Better:
   `test_default_threshold_is_15()`.

## Dependency Health

### Overview

The project has 6 runtime dependencies (prospector with extras, mypy, complexipy,
interrogate, pydantic, jsonschema) and 5 dev dependencies (pytest, pytest-cov,
poethepoet, ruff, types-jsonschema). Dependencies are locked in `uv.lock` with
SHA-256 hashes.

### Findings

1. **[Recommended] Loose Version Constraints** — `pyproject.toml:39-51` uses
   `>=` specifiers (e.g., `"mypy>=1.10.0"`). While `uv.lock` ensures
   reproducibility, the minimum versions are stale relative to locked versions
   (e.g., complexipy declared `>=0.4.0` but locked to `5.1.0`).

2. **[Nit] Homepage URL Mismatch** — `pyproject.toml:68` points to the main
   Prospector repo, not this project's repository.

### Metrics

| Metric | Value |
|--------|-------|
| Runtime dependencies | 6 |
| Dev dependencies | 5 |
| Vendored dependencies | 0 |
| Lock file present | Yes (uv.lock, 1,140 lines) |
| Hash verification | Yes (SHA-256) |
| Known vulnerabilities | poe xray not available |

## Project Infrastructure

### Quality Gates

| Tool | Local | Pre-commit | CI/CD |
|------|-------|-----------|-------|
| ruff (lint) | `poe lint` | — | — |
| ruff (format) | `poe format` | — | — |
| pytest | `poe test` | — | — |
| pytest-cov | `poe test-coverage` | — | — |
| mypy | via `poe checks` | — | — |
| bandit | via `poe checks` | — | — |
| vulture | via `poe checks` | — | — |
| complexipy | via `poe checks` | — | — |
| interrogate | via `poe checks` | — | — |
| pylint (dup code) | via `poe checks` | — | — |

All quality enforcement is local-only. No automated gates exist at commit,
push, or merge time.

### CI/CD Pipeline

**Not configured.** No `.gitlab-ci.yml`, `.github/workflows/`, or equivalent
CI pipeline exists. All quality checks depend on developer discipline.

### Pre-commit Hooks

**Not configured.** No `.pre-commit-config.yaml` exists. Code can be committed
without any quality validation.

### Findings

1. **[Critical] No CI/CD Pipeline** — No automated quality gates on
   branches/merges. No test validation, no coverage enforcement, no
   vulnerability scanning in any pipeline.

2. **[Critical] No Pre-commit Hooks** — No `.pre-commit-config.yaml`. Quality
   violations can be committed without friction.

3. **[High] Poe Tasks Missing vs Template** — Compared to the standard
   `python-base-template`, the following poe tasks are absent:
   - `sync-setup` (uv sync + vendor install)
   - `ensure-hooks` (pre-commit install)
   - `format-check` (ruff format --check)
   - `test-cov` / `test-slow` / `test-all` (granular test runners)
   - `validate-coverage` (coverage threshold validation)
   - `types` (standalone mypy)
   - `security` (standalone bandit)
   - `xray` (vulnerability scan)
   - `quality` (prospector-extended with tee to .task/)
   - `docs` (pdoc generation)
   - `clean` (artifact cleanup)
   - Composite `checks` should be `[test-coverage, format-check, quality]`

4. **[High] Missing Template Configurations** — The project lacks several
   standard configurations from `python-base-template`:
   - `[tool.coverage.run]` with `branch = true` and `fail_under = 80`
   - `[tool.coverage.report]` with `exclude_lines`
   - `[tool.commitizen]` for conventional commits
   - `[dependency-groups]` (uses legacy `[project.optional-dependencies]`)
   - `[tool.uv]` with `python-preference = "only-system"`
   - Build system should use `uv_build` not `hatchling`

### Metrics

| Metric | Value |
|--------|-------|
| CI/CD pipelines | 0 |
| Pre-commit hooks | 0 |
| Quality tools (local) | 9 |
| Quality tools (CI) | 0 |
| Vulnerability scanning (CI) | No |
| Poe tasks defined | 6 (template has 18) |
| Documentation files | 1 (README.md only) |

## Documentation

### Strengths

1. **Comprehensive README.md** (279 lines) — Feature overview, installation,
   CLI usage, configuration reference, error code reference, thresholds table,
   development workflow, architecture explanation, and contributing guidelines.

2. **Well-commented Configuration** — Both `pyproject.toml` and
   `.prospector.yaml` have clear section headers and inline comments explaining
   each tool's configuration and prospector-extended exclusive features.

3. **100% Inline Docstrings** — Google-style docstrings on all public
   functions/classes, confirmed by interrogate.

### Gaps or Risks

1. **[High] Missing Standard Documentation Files** — Per the project's own
   CLAUDE.md standards, these are required but absent:
   - `CHANGELOG.md` — No version history (project is at v0.2.0)
   - `PROJECT.md` — No tech stack, thresholds, or structure docs
   - `SECURITY.md` — No security policy or vulnerability reporting
   - `docs/DEVELOPMENT.md` — No contributor guide
   - `docs/ARCHITECTURE.md` — No design patterns or data flow docs
   - `REQUIREMENTS.md` — No functional specification
   - `STATUS.md` / `TODO.md` — No project state tracking

2. **[Recommended] Missing SUPPRESSIONS.md** — The project has ~5
   `type: ignore` comments but no `docs/SUPPRESSIONS.md` per CLAUDE.md policy.

3. **[Recommended] Stale Sample Files** — `sample-prospector.yaml` and
   `sample-pyproject.toml` in repo root are not referenced from README and may
   be outdated.

4. **[Nit] Sample Files Location** — Sample configs should be in
   `docs/examples/` or `samples/` rather than repo root.

## Design Decisions Worth Highlighting

1. **Two Base Class Patterns** — File-by-file tools use `ExtendedToolBase`
   (template method with `_analyze_file()`); whole-project tools inherit
   `ToolBase` directly. This reflects a real difference in how tools interact
   with Prospector's file iteration model.

2. **Monkey-Patching Tool Registration** — `cli.py:32-37` patches Prospector's
   internal tool registry rather than using Prospector's plugin system. This is
   pragmatic (Prospector's plugin API is limited) but creates coupling to
   Prospector internals.

3. **Pydantic for Structured Parsing** — Uses Pydantic models with field
   validators for mypy JSON output, providing schema validation and safe
   default coercion. This is appropriate for external tool output parsing.

4. **Priority-Sorted Matchers** — Schema matchers are sorted by priority at
   registration time, not at match time. This is a correct optimization since
   the registry is built once and queried many times.

5. **Whitelist as Extension** — Vulture whitelist support is implemented by
   subclassing Vulture itself (`ProspectorVultureExtended`) rather than
   post-processing output. This ensures whitelist entries affect confidence
   calculations, not just filtering.

## Technical Debt Assessment

### Estimated Debt

Moderate technical debt, concentrated in infrastructure and test coverage
rather than code quality. The codebase is young (2 commits, v0.2.0) and the
debt reflects an early-stage project where code quality was prioritized over
operational tooling.

### Highest-Cost Areas

1. **No CI/CD Pipeline** [Critical, Medium effort] — Every quality tool exists
   locally but nothing prevents bad code from being committed or merged.
   Highest-impact improvement per hour invested.

2. **Test Coverage Gaps** [Must-Fix, Medium effort] — CLI (57 LOC), VultureTool
   (229 LOC), and ExtendedToolBase (133 LOC) have zero tests. These total 419
   LOC (28% of source) with no regression protection.

3. **Poe Task Alignment** [High, Low effort] — Project defines 6 poe tasks vs.
   18 in the standard template. Missing tasks include `format-check`, `types`,
   `security`, `quality`, `clean`, `sync-setup`, and composite `checks`.

4. **Documentation Gap** [High, Medium effort] — Only README.md exists.
   Missing CHANGELOG, PROJECT.md, SECURITY.md, DEVELOPMENT.md, and
   ARCHITECTURE.md per the project's own CLAUDE.md standards.

5. **Silent Error Handling** [Recommended, Low effort] — Multiple tools
   silently swallow errors, making diagnosis difficult. Adding structured
   logging at DEBUG level is low-effort, high-diagnostic-value.

### Duplication

No significant duplication detected. Pylint duplicate-code checker is
configured with `min-similarity-lines = 4` and produced no findings in the
quality baseline.

## Quantitative Summary

| Metric | Value |
|--------|-------|
| **Code Metrics** | |
| Total source LOC | 1,504 |
| Total test LOC | 752 (est.) |
| Test-to-code ratio | ~1:2 |
| Source files | 11 |
| Test files | 4 (+4 fixtures) |
| Total tests | 46 |
| Branch-inclusive coverage | Not measured |
| Duplication | None detected (pylint, min 4 lines) |
| **Complexity** | |
| Max cyclomatic complexity | Within threshold (mccabe max=10, 0 violations) |
| Cognitive complexity | Within threshold (complexipy max=15, 0 violations) |
| Max function length | 38 lines |
| Deepest nesting | 3 levels |
| Public functions/classes | 44 |
| Private/internal functions | 23 |
| Functions with >3 parameters | 3 |
| **Dependencies** | |
| Runtime dependencies | 6 |
| Dev dependencies | 5 |
| Vendored dependencies | 0 |
| Lock file status | Present (uv.lock, SHA-256 hashes) |
| Known vulnerabilities | Not scanned (poe xray unavailable) |
| **Infrastructure** | |
| CI/CD jobs | 0 |
| Quality tools configured | 9 |
| Documentation files | 1 (README.md) |
| Pre-commit hooks | 0 |
| Vulnerability scanning (CI) | No |

## Overall Assessment

Prospector Extended earns a **B overall** — strong engineering fundamentals
held back by missing operational infrastructure. The source code is genuinely
well-crafted: strict typing, complete documentation, clean architecture, zero
security findings, and no complexity violations. The design patterns
(strategy, template method, builder, adapter) are appropriate and
well-implemented, not over-engineered.

The project's weakest dimension is infrastructure (**D**). Every quality tool
exists locally but nothing enforces standards at commit or merge time. Adding
CI/CD and pre-commit configuration would immediately raise the overall grade.
The second gap is test coverage (**C**) — 46 tests is solid for parsing and
tool execution, but three core modules (CLI, VultureTool, ExtendedToolBase)
totaling 419 LOC have zero tests.

**Single most impactful improvement:** Add a CI/CD pipeline with the standard
poe task suite from `python-base-template`. This would enforce the quality
standards that already exist locally, close the infrastructure gap, and provide
the automated gates that a tool project — especially one that other projects
depend on — requires for confidence in releases.

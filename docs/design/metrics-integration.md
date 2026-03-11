# Design: Code Metrics Integration into Prospector-Extended

**Date:** 2026-03-11
**Status:** Planning
**Context:** Identified during tempenv v0.6.2 code review — current tooling only surfaces violations, not quantitative metrics.

## Problem

Prospector-extended currently outputs **violations only** (things that fail thresholds). Quantitative metrics — complexity scores for compliant functions, LOC breakdowns, maintainability indexes, function lengths, nesting depths — are either discarded or never collected. The code-review skill must extract these observationally (reading code and counting manually), which is slow and imprecise.

## Goal

Add a `metrics` block to prospector-extended JSON output alongside the existing `messages` block. Every quality tool run should contribute metrics, not just violations.

## Current State: What Each Tool Provides vs. Surfaces

### Tools That Discard Useful Metrics

| Tool | What It Produces | What's Surfaced | What's Discarded |
|------|-----------------|-----------------|------------------|
| **complexipy** | Per-function cognitive complexity scores | Only violations > threshold | Scores for compliant functions, per-file aggregates |
| **interrogate** | Per-node docstring coverage status | Only missing docstrings | Coverage %, counts by node type (module/class/function), documented vs total |
| **vulture** | Items + confidence percentages | Filtered by min_confidence | Confidence scores on reported items, per-type breakdown, summary stats |
| **mccabe** (via ruff C90) | Per-function cyclomatic complexity | Only violations > max-complexity | Actual CC scores for all functions |
| **ruff/pylint** | Parameter counts, statement counts, branch counts | Only violations exceeding limits | Actual counts for compliant functions |
| **mypy** | Type error/warning/note details | Violations only | No % typed metric, no per-function type coverage |
| **bandit** | Security findings | Violations only | No aggregate security posture metric |

### Metrics Not Collected At All (No Current Tool)

| Metric | Source Needed | Notes |
|--------|-------------|-------|
| **LOC/SLOC/comments per file** | radon raw | tokei gives project totals but not per-file JSON |
| **Maintainability index per file** | radon mi | A-F rank + 0-100 score |
| **Function length (lines)** | AST analysis | Max, mean, per-function |
| **Nesting depth** | AST analysis | Max per function |
| **Public vs private counts** | AST analysis | Functions, classes, methods |
| **Parameter count per function** | AST analysis (or radon) | Currently only violations from ruff |
| **Halstead metrics** | radon hal | Volume, difficulty, effort (optional — may be too academic) |

## Proposed Output Structure

Extend the prospector-extended JSON to include a `metrics` key:

```json
{
  "summary": { ... },
  "messages": [ ... ],
  "metrics": {
    "project": {
      "files": 19,
      "loc": 3671,
      "sloc": 3093,
      "comments": 79,
      "blanks": 499,
      "test_files": 25,
      "test_loc": 6107
    },
    "complexity": {
      "cyclomatic": {
        "max": 8,
        "mean": 2.3,
        "functions_above_threshold": 0,
        "per_function": [
          {"file": "config.py", "function": "read_config", "class": "Config", "line": 420, "cc": 8, "rank": "B"}
        ]
      },
      "cognitive": {
        "max": 12,
        "mean": 3.1,
        "functions_above_threshold": 0,
        "per_function": [
          {"file": "config.py", "function": "read_config", "class": "Config", "line": 420, "score": 12}
        ]
      }
    },
    "maintainability": {
      "per_file": [
        {"file": "config.py", "mi": 65.2, "rank": "A"},
        {"file": "tempenv.py", "mi": 58.7, "rank": "A"}
      ]
    },
    "structure": {
      "functions": {
        "total": 80,
        "public": 50,
        "private": 30,
        "max_length": 50,
        "mean_length": 15,
        "above_60_lines": 0,
        "max_params": 3,
        "above_3_params": 0,
        "max_nesting": 3,
        "above_nesting_threshold": 0
      },
      "classes": {
        "total": 17,
        "public": 17,
        "private": 0
      }
    },
    "coverage": {
      "docstrings": {
        "total_nodes": 120,
        "documented": 115,
        "percentage": 95.8,
        "by_type": {
          "module": {"total": 19, "documented": 19},
          "class": {"total": 17, "documented": 17},
          "function": {"total": 84, "documented": 79}
        }
      }
    },
    "dead_code": {
      "items_detected": 0,
      "by_type": {
        "function": 0,
        "variable": 0,
        "class": 0,
        "import": 0
      }
    },
    "duplication": {
      "blocks_detected": 0,
      "duplicate_lines": 0,
      "total_lines": 3093,
      "ratio": 0.0
    },
    "suppressions": {
      "noqa": 0,
      "nosec": 1,
      "type_ignore": 2,
      "total": 3
    }
  }
}
```

## Implementation Approach

### Option A: Radon as Prospector Tool (Preferred)

Add radon as a new tool in prospector-extended, similar to how complexipy and interrogate are wrapped:

1. **RadonTool** wrapping `radon cc`, `radon raw`, `radon mi`
2. Returns empty `Message` list (no violations — just metrics)
3. Metrics collected into the new `metrics` block
4. radon is already installed (dependency of claude-scripts, which is an editable dep)

### Option B: AST-Based Metrics Tool

For metrics radon doesn't provide (function length, nesting depth, visibility):

1. **StructureTool** using Python `ast` module directly
2. Walk AST to count functions, classes, nesting, line spans
3. Lightweight — no external dependency needed

### Option C: Integrate code-metrics project

The planned `code-metrics` project (`~/.projects/code-metrics/REQUIREMENTS.md`) covers function length, nesting, params, visibility. Could be:
- A prospector-extended tool (if built as a library)
- A standalone CLI whose output gets merged into the metrics block

### Recommended: A + B combined

- Radon for complexity (cc), raw metrics (raw), and maintainability (mi)
- AST tool for structure (function length, nesting, visibility, params)
- Extend existing tool wrappers (complexipy, interrogate, vulture) to also emit metrics, not just violations

## What Each Existing Tool Wrapper Needs

| Tool Wrapper | Change Needed |
|-------------|---------------|
| **complexipy_tool.py** | Emit all scores (not just violations) into metrics.complexity.cognitive |
| **interrogate_tool.py** | Emit coverage % and per-type counts into metrics.coverage.docstrings |
| **vulture_tool.py** | Emit per-type breakdown and summary into metrics.dead_code |
| **pylint** (similarities) | Emit duplication ratio into metrics.duplication |
| **New: radon_tool.py** | cc → metrics.complexity.cyclomatic, raw → metrics.project, mi → metrics.maintainability |
| **New: structure_tool.py** | AST → metrics.structure (function length, nesting, visibility, params) |

## Code-Review Skill Integration

Once metrics are in prospector output, the code-review skill would:

1. Run `poe quality` (or `poe checks`)
2. Parse `metrics` block from JSON output
3. Use deterministic data instead of agent-observational counting
4. Agent 1 focuses on architectural analysis, not counting functions

The skill already has a conditional: "if poe metrics available... otherwise Agent 1 will extract observationally." This would satisfy that conditional.

## Dependencies

- `radon>=6.0` (already available via claude-scripts editable dep)
- Python `ast` module (stdlib)
- No new external dependencies needed

## Open Questions

- Should Halstead metrics be included? (volume, difficulty, effort — useful but academic)
- Should per-function detail be opt-in (e.g., `--metrics-detail`) to keep default output concise?
- Should metrics have thresholds that produce warnings in `messages`? Or keep metrics purely informational?

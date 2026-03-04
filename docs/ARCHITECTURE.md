# prospector-extended Architecture

This document describes the internal architecture for developers and contributors.

## Overview

prospector-extended wraps and extends [Prospector](https://github.com/PyCQA/prospector) by
monkey-patching its tool registry at runtime. It replaces the built-in mypy tool with a more
robust implementation and adds new tools (vulture with whitelist, complexipy, interrogate).

```
┌──────────────────────────────────────────────────────────────┐
│                    prospector-extended CLI                    │
│                                                              │
│  1. patch_prospector_tools() — replace/add tool entries      │
│  2. prospector.run.main() — standard prospector execution    │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────────┐
              │             │                 │
        ┌─────┴─────┐ ┌────┴────┐ ┌─────────┴──────────┐
        │  Parsing   │ │  Tools  │ │ Prospector Built-in │
        │ (models,   │ │ (mypy,  │ │ (ruff, bandit,     │
        │  registry) │ │ vulture,│ │  pylint, dodgy)    │
        └────────────┘ │ cpxpy,  │ └────────────────────┘
                       │ interr) │
                       └─────────┘
```

## Components

### CLI (`cli.py`)

**Location:** `src/prospector_extended/cli.py`

**Responsibilities:**
- Call `patch_prospector_tools()` to register extended tools
- Delegate to `prospector.run.main()` for all execution logic
- Provide `prospector-extended` and `pex` entry points

### Parsing Infrastructure (`parsing/`)

**Location:** `src/prospector_extended/parsing/`

**Responsibilities:**
- Parse JSON output from external tools (mypy)
- Validate parsed data using Pydantic models
- Provide polymorphic type resolution via TypeRegistry
- Detect schema drift via fingerprinting

#### Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `TypeRegistry` | `registry.py` | Polymorphic JSON parsing with schema-based matchers |
| `MypyJsonOutput` | `models.py` | Pydantic model for mypy JSON output fields |
| `AlwaysMatcher` | `registry.py` | Default/fallback matcher for TypeRegistry |
| `RequiredFieldsMatcher` | `registry.py` | Matches JSON objects by required field presence |
| `ValidationFailure` | `registry.py` | Dataclass for tracking parse validation failures |

### Tools (`tools/`)

**Location:** `src/prospector_extended/tools/`

**Responsibilities:**
- Implement Prospector's `ToolBase` interface for each tool
- Run external tools via subprocess or Python API
- Convert tool output into Prospector `Message` objects

#### Tool Implementations

| Tool | File | Integration Method |
|------|------|--------------------|
| `ExtendedToolBase` | `base.py` | Abstract base with config extraction helpers |
| `MypyTool` | `mypy_tool.py` | `mypy.api.run()` with JSON/text dual parsing |
| `VultureTool` | `vulture_tool.py` | `vulture.Vulture()` API with whitelist scanning |
| `ComplexipyTool` | `complexipy_tool.py` | Subprocess invocation of `complexipy` |
| `InterrogateTool` | `interrogate_tool.py` | Subprocess invocation of `interrogate` |

## Data Flow

```
1. CLI invocation
   → patch_prospector_tools() patches prospector.tools.TOOLS dict
   → prospector.run.main() starts

2. Prospector reads .prospector.yaml
   → Determines which tools to run
   → Creates tool instances from TOOLS dict (using our patched entries)

3. Each tool executes
   → MypyTool: calls mypy.api.run(), parses JSON with TypeRegistry/Pydantic
   → VultureTool: creates Vulture instance, scans whitelist files, then source
   → ComplexipyTool: runs subprocess, parses JSON output
   → InterrogateTool: runs subprocess, parses text output

4. Results collected
   → Each tool returns list of prospector.message.Message objects
   → Prospector aggregates and formats output
```

## Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Strategy | `tools/*.py` | Each tool implements same interface, different analysis |
| Template Method | `base.py` | `ExtendedToolBase` provides config extraction, subclasses implement `run()` |
| Registry | `registry.py` | `TypeRegistry` maps JSON schemas to types |
| Adapter | `tools/*.py` | Adapts external tool output to Prospector's `Message` format |
| Builder | `registry.py` | `TypeRegistryBuilder` for composing registry configurations |
| Monkey Patch | `__init__.py` | Patches Prospector's TOOLS dict at import time |

## Module Map

| Module | Purpose |
|--------|---------|
| `__init__.py` | Package init, `patch_prospector_tools()` entry point |
| `cli.py` | CLI entry point with Prospector delegation |
| `parsing/__init__.py` | Public API exports for parsing infrastructure |
| `parsing/models.py` | Pydantic models for structured tool output |
| `parsing/registry.py` | TypeRegistry, matchers, validation, fingerprinting |
| `tools/__init__.py` | Tool name → class mapping, registration |
| `tools/base.py` | `ExtendedToolBase` with config extraction |
| `tools/complexipy_tool.py` | Cognitive complexity via complexipy subprocess |
| `tools/interrogate_tool.py` | Docstring coverage via interrogate subprocess |
| `tools/mypy_tool.py` | Type checking via mypy API with dual parsing |
| `tools/vulture_tool.py` | Dead code detection with whitelist support |

## Architecture Decisions

### ADR-1: Monkey-Patching Prospector's Tool Registry

**Decision:** Patch `prospector.tools.TOOLS` dict at runtime rather than forking Prospector.

**Rationale:** Prospector doesn't have a plugin system for replacing built-in tools. Forking
would create maintenance burden. Monkey-patching the TOOLS dict is clean, minimal, and doesn't
modify Prospector source code.

### ADR-2: Two Base Class Patterns

**Decision:** `MypyTool` inherits from `ExtendedToolBase` (which wraps `ToolBase`), while
`VultureTool` inherits directly from `ToolBase`.

**Rationale:** Historical — VultureTool was added later and uses vulture's Python API directly
rather than subprocess execution. Both patterns work with Prospector's tool interface.
Task 3.01 tracks aligning VultureTool to use ExtendedToolBase.

### ADR-3: Dual JSON/Text Parsing for Mypy

**Decision:** Parse mypy output as JSON first, fall back to regex-based text parsing.

**Rationale:** Mypy's JSON output can be malformed in edge cases (syntax errors in scanned
files). Text fallback ensures no messages are silently lost.

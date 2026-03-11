# Prospector Extended Patterns

Project-specific coding patterns that deviate from or extend the global patterns
in `.claude/docs/PATTERNS.md`. Only deviations are documented here.

---

## Matcher Hierarchy with Priority-Ranked Dispatch

**Context:** The TypeRegistry dispatches JSON lines to schemas using matchers
ranked by priority (100=type tag, 80=discriminator, 50=required fields,
0=fallback). Schemas are tried in priority order; first valid match wins.

**Overrides global:** Extends the global strategy/registry pattern. The global
pattern uses a flat `dict[str, type[Base]]` registry keyed by string. This
project uses ranked matchers because the dispatch key isn't a single field —
it's a structural match against the shape of the data.

**See also:** `src/prospector_extended/parsing/registry.py:58-148`

## Union Type for Parse Result Variants

**Context:** Parsing a JSON line has three possible outcomes, modeled as a
union type: `ParseResult = ParsedRecord | UnparsedLine | ValidationFailure`.
Callers use `isinstance` checks to handle each case.

**Overrides global:** The global result envelope pattern uses `success: bool`
with reasons. This project needs richer result types because the caller's
behavior depends on *why* parsing failed (not JSON? valid JSON but wrong schema?).

**See also:** `src/prospector_extended/parsing/registry.py:155-181`

## Template Method in Tool Base Class

**Context:** `ExtendedToolBase` provides the prospector integration boilerplate
(configure, run, filter messages) and delegates to two abstract hooks that
subclasses implement: `_configure_options()` and `_analyze_file()`.

**Overrides global:** The global strategy pattern uses full ABC with `@abstractmethod`
on the public interface. This project uses template method — the public interface
(`configure`, `run`) is concrete and calls abstract private hooks. Better fit when
the framework (prospector) dictates the public interface shape.

**See also:** `src/prospector_extended/tools/base.py:26-133`

## Schema Fingerprinting for Dedup

**Context:** Registered schemas get a SHA256 fingerprint of their canonical JSON.
This enables dedup detection and cache invalidation when schemas change.

**See also:** `src/prospector_extended/parsing/registry.py:30-36`

# Next Steps - Resume Point

## Current State

**Phase:** 4 — Metrics Integration
**Branch:** main
**Last Action:** Phase 4 tasks created from tempenv code review findings (2026-03-11)

## Next Action

Begin Phase 4 — Metrics Integration:

1. **4.01** — MetricsCollector infrastructure and `metrics` JSON block
2. **4.03** — RadonTool (cc + raw + mi) — radon already available as dependency
3. **4.05** — StructureTool (AST: function length, nesting, visibility, params)
4. **4.07-4.11** — Extend existing tools (complexipy, interrogate, vulture) to emit metrics
5. **4.13** — Suppression counting + duplication metrics
6. **4.15** — Integration tests for complete metrics output

Tasks 4.01, 4.03, 4.05 are the foundation — do those first. 4.07-4.13 can be done in any order after 4.01. 4.15 is the capstone.

## Design Reference

- `docs/design/metrics-integration.md` — full design with proposed JSON structure, tool gap analysis, and implementation approach

## Key Decisions

- Metrics go into prospector-extended JSON output (not a separate tool)
- Radon for cc/raw/mi, stdlib `ast` for structure — no new external deps needed
- Existing tool wrappers extended to emit metrics alongside violations
- `--metrics` flag for opt-in/opt-out (default: enabled)

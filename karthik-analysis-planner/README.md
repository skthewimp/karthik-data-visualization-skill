# karthik-analysis-planner

Analysis-planning skill: use this when the question is **what exactly are we measuring and comparing?**

It turns a natural-language data question into an analysis contract before code, charts, or prose.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version of the skill, with Claude-safe metadata.

## Edit rule

If you change skill behavior, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific.

## Relationship to other skills

Use this before `dataviz-selector`, `karthik-data-visualization`, or writing-style skills. The planner defines the denominator, comparison, metric, and caveats that downstream skills must respect.

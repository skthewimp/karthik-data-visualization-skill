# dataviz-orchestrator

The staged orchestrator for the full dataset-to-visual-story loop: raw data in, visual story out. It is the coordinating skill, not a replacement for the more focused skills. It runs as an ordered sequence of separate calls - discover, contract, clean, facts, select, build, refine - each carrying only the skills that stage needs plus a compact artifact handed forward from the previous stage. That per-stage scoping is what keeps a long pipeline from rotting a single context. For repairing an existing chart from an image, use `dataviz-fix` (the repair orchestrator) instead.

The machine-readable contract - exact skill subset and JSON handoff schema per stage - is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE`.

Use it when the request is broader than “pick a chart” or “clean this plot”. For example: “here is a dataset, find the story and make the chart”.

## Stages it coordinates

One skill loaded per call, artifact passed forward:

- **discover** - `dataset-question-generator` for candidate stories from a raw dataset.
- **contract** - `karthik-analysis-planner` for definitions, denominator, metric, comparison, and falsifiers.
- **clean** - `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation.
- **facts** - no dedicated skill yet (`karthik-evidence-builder` is a known gap); compute evidence from the prepared data.
- **select** - `dataviz-selector` for chart form and encodings, and the chart-vs-table `builder` choice.
- **build** - `karthik-data-visualization` (chart) or `karthik-table-style` (table), plus `chart-annotations` / `chart-explainer` when the plan asks.
- **refine** - `dataviz-critique` for the checker loop; `dataviz-eval` only for an explicit audit.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Edit rule

If the workflow changes, update both `codex/SKILL.md` and `claude/SKILL.md`. Also update `docs/skills/dataviz-orchestrator.md` and the repo README if the relationship between skills changes.

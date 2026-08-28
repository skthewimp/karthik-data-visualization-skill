# dataviz-orchestrator

The creation front half for the dataset-to-visual-story loop: raw data in, visual story out. It is the coordinating skill for the front half, not a replacement for the more focused skills. It runs as an ordered sequence of separate calls - discover, contract, clean - and then hands into the shared construct process (`dataviz-construct`), whose tail is insight, select, idea, build, execution. Each call carries only the skills that stage needs plus a compact artifact handed forward; that per-stage scoping is what keeps a long pipeline from rotting a single context. For repairing an existing chart from an image, use `dataviz-fix` (the repair front half) instead - it feeds the same construct tail.

The machine-readable contract - exact skill subset and JSON handoff schema per stage - is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE`.

Use it when the request is broader than “pick a chart” or “clean this plot”. For example: “here is a dataset, find the story and make the chart”.

## Stages it coordinates

One skill loaded per call, artifact passed forward:

Front half (owned by this skill):

- **discover** - `dataset-question-generator` for candidate stories from a raw dataset.
- **contract** - `karthik-analysis-planner` for definitions, denominator, metric, comparison, and falsifiers.
- **clean** - `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation.

Construct tail (shared with repair, via `dataviz-construct`):

- **insight** - `karthik-evidence-builder` computes the facts and names the headline claim + candidate annotations before a form is chosen.
- **select** - `dataviz-selector` for chart form and encodings, and the chart-vs-table `builder` choice.
- **idea** - `dataviz-idea-critique`, the pre-render gate (data / expression / insight / honesty).
- **build** - `karthik-data-visualization` (chart) or `karthik-table-style` (table), plus `chart-annotations` / `chart-explainer` when the plan asks.
- **execution** - `dataviz-execution`, the post-render gate (geometry, overlap, colour, precision, ink).

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Edit rule

If the workflow changes, update both `codex/SKILL.md` and `claude/SKILL.md`. Also update `docs/skills/dataviz-orchestrator.md` and the repo README if the relationship between skills changes.

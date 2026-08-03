# chart-annotations

Use this skill when the question is: what should this chart mark, and what should the mark say? It decides which feature of the chart carries the claim, which competing candidate wins, how the label is worded, and where the label sits.

This is not a chart-selection skill and not a chart-style skill. It assumes the chart form is settled and the reader still cannot see the point without narration.

## What it does

- Splits the work between title and annotation: the title states the claim, the annotation locates it.
- Enumerates annotation candidates from chart geometry - knee-bends, crossovers, runs, thresholds, outliers, endpoints.
- Runs a concentration check so an aggregate is not annotated when a short burst explains it.
- Ranks competing candidates against a significance ladder, and caps the chart at one primary plus two supporting annotations.
- Constrains label wording: under 18 words, one claim, every number tied to its baseline, no causal verb without causal evidence, no report-speak.
- Handles the case where nothing clears the bar: annotates a well-supported absence instead of promoting the largest wiggle.
- Holds derived features - scanned knees, fitted slopes, smoothed peaks - to a higher bar than observed ones.
- Requires annotation coordinates to be derived from the data rather than hand-typed, so labels cannot attach to the wrong row.
- Sets placement and visual-weight rules, and requires rendering and inspecting the image before declaring the chart done.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and surrounding style. Use `dataviz-critique` when reviewing an existing annotated chart. `dataviz-orchestrator` calls this skill at the charting step.

## Edit rule

If annotation behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific.

# dataviz-fix

Use this skill when the task is not merely to critique a chart, but to repair it through a real feedback loop and improve the skill stack from the accepted result.

## What it does

- Rebuilds an uploaded or pasted visualization as a real PNG, SVG, or PDF.
- Iterates from short user feedback without restarting the chart each time.
- Inspects the exact export before showing it, and repairs mechanical defects locally before reopening the design.
- After acceptance, classifies why the first output missed: execution miss, missing rule, ambiguous rule, conflicting rule, tooling, or input data.
- Makes only reusable skill changes, tested against unrelated charts; it does not turn one chart's values, nouns, or layout into a rule.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.

## Relationship to other skills

`dataviz-fix` is the repair-loop umbrella. It calls `dataviz-critique`, `dataviz-selector`, `karthik-data-visualization`, `chart-annotations`, and the analytical skills when their failure mode is relevant. `dataviz-eval` is used only when a formal audit is requested.

## Edit rule

Mirror behavioural changes across the Codex and Claude surfaces.

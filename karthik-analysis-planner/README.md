# karthik-analysis-planner

Use this skill when the main risk is not the chart but the question. It turns a fuzzy natural-language data question into an analysis contract before code, charts, or prose.

The skill forces the boring but essential choices: unit of analysis, denominator, numerator, metric, comparison, filters, sanity checks, falsifiers, and caveats. This is where “does X work?” becomes something measurable.

## What it does

- Rewrites a vague question as a measurable claim.
- Defines ambiguous terms and denominator traps.
- Specifies data requirements, profile checks, cleaning/reshape rules, and source caveats.
- Preserves falsification conditions before anyone starts writing a title or conclusion.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `karthik-data-cleaning` when data preparation affects the metric. Use `dataviz-selector` only after the metric and comparison are clear. Use `karthik-data-visualization` after the chart form is chosen.

## Edit rule

If planning behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep `docs/skills/karthik-analysis-planner.md` aligned with the public behaviour.

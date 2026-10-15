# dataviz-eval

`dataviz-eval` decides whether a rendered chart can be sent as it is, needs a revision, or needs a different form. It returns a one-line verdict (`Send`, `Revise`, `Redesign` or `Not evaluable`) and every real problem, ranked, one line each.

It checks four things in order: the analysis is right, the point lands fast, the chart reads at the size it will be seen, and there is no junk on it. It is lenient by design: only problems that mislead or block a quick read are must-fix; everything else is polish. A "Karthik's preferences" section, built from a this-or-that quiz with Karthik, sets the taste it judges against.

## Why it is optional

Do not auto-load `dataviz-eval` during normal repair. Use it when the user asks for a verdict on a chart. Its verdict may guide the next revision, but it must not suppress the strongest valid artifact already produced.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

- Use `dataviz-selector` to choose a visual form before plotting.
- Use `karthik-data-visualization` to create and style the chart.
- Use `dataviz-critique` for open-ended diagnosis and alternatives.
- Use `dataviz-eval` for a send/revise verdict.
- Use `dataviz-fix` to execute revisions and preserve the feedback trail.

## Edit rule

Keep both `SKILL.md` files identical and update the human documentation in the same change.

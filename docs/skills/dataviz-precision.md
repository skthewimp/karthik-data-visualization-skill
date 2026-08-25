# Dataviz Precision Skill

`dataviz-precision` decides how many significant digits to show for numbers on a chart or in a table - axis ticks, data labels, and table cells.

It exists because precision is usually chosen wrong: people show every digit a number happens to have, or round to whatever looks tidy. Neither answers the real question, which is how precise the reader must be to tell the displayed numbers apart. That is a property of the *spread* of the column, not of any single value.

## The rule

Precision is keyed to the range - `max - min` - of the values shown together, and expressed as significant digits, not decimal places. Every value in a column or axis is rounded to one uniform place so digit-length itself reads as magnitude.

The **`recommend_precision`** MCP tool computes it:

- the range over the values that must be distinguished,
- a uniform rounding place from `place = floor(log10(range)) - (target_steps - 1)`, where `target_steps` (~2) is how many significant figures of the range the reader needs to just about resolve the information,
- a formatted preview of every value rounded to that place.

For example, `{12483, 9210, 15040}` spans ~5830, so the place is hundreds and the column shows `12,500 / 9,200 / 15,000` - and no more. If the smallest meaningful difference `d` is known, the place is taken from `d` directly.

The rule is the same for charts and tables; apply it per axis and per column, each with its own spread. In tables it works alongside `karthik-table-style` for decimal alignment and tabular figures.

## Exact-digit override

The spread rule is the default for every displayed number. It is overridden in one case only - **identifiers or a genuine exact-lookup requirement**, where a reader must read a value off verbatim. `recommend_precision(values, role, exact=True)` preserves every source digit and returns `exact_override: true`. The override is never silent: the reason for it is recorded in the build result's `recommendations_used.number_formats` entry, whose `reason` field is required.

In the staged pipeline the decision is made upstream at the form-selection stage, not inferred by the builder from prose: select emits a structured `exact_lookup_required` flag (with a reason) for each numeric display group in `number_display_groups`, and the build stage obeys it. Carrying the decision as a flag rather than a paragraph is what lets a weaker build model apply it reliably.

The installable skill lives in `dataviz-precision/{codex,claude}/SKILL.md`.

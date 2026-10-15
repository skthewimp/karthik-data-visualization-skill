# Dataviz Eval Skill

`dataviz-eval` answers one question: can this rendered chart go out?

It returns a verdict - `Send`, `Revise`, `Redesign` or `Not evaluable` - and every real problem it found, ranked, one line each: the element, the problem, what the reader loses, and the fix. No tables, no failure codes.

## What it checks

1. **The analysis is right.** Values match the data, the measure suits the claim (rate or share versus raw total), the scale doesn't distort, and the title claims no more than the chart shows.
2. **The point lands fast.** One clear point, the eye goes to the finding first, the form makes the comparison directly.
3. **It reads at the size it will be seen.** Judged on the export at display width, not native pixels: nothing to zoom for, no overlaps or clipping, a canvas that fits its content.
4. **No junk.** No notes about how the chart was made, no titles or legends repeating what labels already say, no more digits than the spread needs.

## How strict

Lenient. A problem is **must fix** only if it misleads or stops a quick read. Everything else - text that is small but readable, a slightly better form that exists - is **polish**, listed but never required. A clean chart gets `Send` and the loop stops.

## Whose taste

The skill carries a "Karthik's preferences" section built from a this-or-that quiz: direct labels over legends (repelled labels when they crowd), labels instead of value axes, points on lines, axes fitted to the data, whole numbers where the spread allows, claim titles, small footnotes for definitions and source, short explanatory callouts, one shared panel for a handful of lines and small multiples once they crowd, lines for shares over time, separate panels instead of dual axes, log axes for huge ranges, labelled pies for two or three parts, and tables for dense lookup.

An earlier version was a heavy audit framework: blind expert and audience reads, six gates, a failure-code taxonomy and a benchmark mode. It judged on things Karthik didn't care about, so it was cut down to this. An attempt to infer his taste from his exploratory R notebooks was also reverted: quick notebook charts keep default legends and axes because nobody bothered to change them, not because he prefers them.

## Relationship to other skills

- `dataviz-selector` chooses the visual form.
- `karthik-data-visualization` creates and styles the chart.
- `dataviz-critique` diagnoses and proposes alternatives.
- `dataviz-eval` gives the send/revise verdict.
- `dataviz-fix` performs the changes and records the iterative feedback.

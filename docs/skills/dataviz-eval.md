# Dataviz Eval Skill

`dataviz-eval` is the repo's *render readiness gate*: use it after a chart already exists and you need to decide whether it can be sent, should be revised, or needs a redesign.

It exists because repeated chart repairs exposed the same failure modes:

- clipped labels
- overlapping labels
- title/subtitle/header collisions
- whitespace that makes the chart feel unbalanced
- export-vs-viewport mismatches
- charts that work at design size but fail in chat/thumbnail form

## When to use

Use `dataviz-eval` when you have a rendered artifact and need a clear verdict on whether it is good enough to ship.

Typical triggers:

- "is this readable?"
- "does this look right?"
- "should I send it?"
- "what still needs fixing?"
- "the preview looks fine but the exported image seems off"

## What it checks

- readability at the intended size
- overlap, clipping, and label crowding
- geometry and whitespace
- title, axis, source, and unit fit
- whether the artifact survives chat compression or slide delivery
- whether the form is still the right one, or whether the chart should be redesigned

## Relationship to other skills

- Use `dataviz-critique` when the chart form itself may be wrong.
- Use `dataviz-selector` before charting when the visual form is still open.
- Use `karthik-data-visualization` when the chart is conceptually right but the rendering needs work.
- Use `dataviz-fix` when the work should be iterated through user feedback and revision logs.

## Output

A good evaluation should end with one of:

- `Send`
- `Revise`
- `Redesign`

and a short explanation of why.

## Documentation note

This skill was added on 2026-08-10 alongside documentation updates for the dataviz repair loop, the new `dataviz-eval` inspection gate, and the updated chart-selection / chart-style guidance.

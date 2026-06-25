---
name: dataviz-critique
description: Critique charts with Fung's trifecta, then suggest 2-3 stronger visualization alternatives.
---

# Dataviz Critique

Use this when reviewing an existing chart, dashboard, infographic, AI-generated visualization, or slide visual.

Core job: diagnose whether the visual makes the right thing easy to see, hard to misread, and worth seeing; then propose 2-3 better visualization alternatives.

## First pass

Identify chart type, encodings, apparent question, apparent claim, likely viewer interpretation, and assumptions from missing context.

## Trifecta checkup

Use Kaiser Fung's question-data-visual triangle:

- **Question**: clear, worthwhile, one main job?
- **Data**: right grain, units, denominators, time window, baseline, uncertainty, transformations?
- **Visual**: right chart type, axes, labels, scale, ordering, colour, hierarchy, annotation?

Check pairwise fit:

- Question ↔ Data: right measure for claim? bad proxy? bad denominator?
- Data ↔ Visual: preserves magnitude, rank, distribution, uncertainty, comparison?
- Visual ↔ Question: answers intended question or shows a different story?

## Karthik lens

Apply these standards:

- Clarity first: chart must stand alone; unclear axes/units/encodings are major failures.
- Intentional design: every colour, shade, line, sort, layout choice must earn its place.
- Fundamentals first: dimensional consistency, denominators, uncertainty, and meaningful comparisons matter more than polish.
- Narrative with evidence: communicate a defensible point, not just numbers.
- No tool worship: reject dashboard clutter, BI defaults, AI aesthetics, and flashy chart types when they add friction.
- Repeatable fixes: recommend improvements that survive reruns/new data.

## Common failures

- No clear question or too many questions.
- Rate/count confusion; wrong denominator; nonsensical unit comparison.
- Aggregation hides distribution/outliers/subgroups/sample changes.
- Cherry-picked dates, missing baseline/counterfactual/uncertainty.
- Ambiguous form, e.g. line chart shaded like area chart.
- Bars not starting at zero, dual axes, 3D, area/volume for 1D values.
- Map for ranking, pie/donut for precise comparison, stacked bars for tiny differences, spaghetti lines.
- Arbitrary colour, too many similar hues, poor contrast, red/green dependence.
- Descriptive rather than claim-first title; legend lookup where direct labels would work.

## Severity

- **Fatal**: changes conclusion or makes chart uninterpretable.
- **Major**: materially slows/misleads interpretation.
- **Minor**: polish/readability.

Fix fatal data/question issues before style issues.

## Redesign alternatives

After critique, propose 2-3 alternatives when useful. Do not list random chart types; each option must have a distinct purpose.

Default set:

1. **Minimal repair** — keep chart form; fix labels, title, axis, scale, colour, ordering, annotation, caveats.
2. **Better analytical redesign** — change chart form to better answer the stated question.
3. **Different story lens** — reframe around a more revealing question: totals → rates, average → distribution, snapshot → trend, level → change, ranking → decomposition, geography → comparison, dashboard → interpreted action.

For each option: best when, chart, encoding, what it fixes/reveals, tradeoff. If only one redesign is defensible, give one strong option rather than padding.

## Output

Default structure:

```markdown
## Quick read
- What it is: ...
- What it seems to say: ...
- Verdict: works / partly works / fails, because ...

## Trifecta checkup
- Question: ...
- Data: ...
- Visual: ...
- Main mismatch: ...

## Issues to fix
1. **[Fatal/Major/Minor] Issue** — impact. Fix: ...
2. ...
3. ...

## Recommended alternatives

### Option A — Minimal repair
- Best when: ...
- Chart: ...
- Encoding: ...
- What it fixes: ...
- Tradeoff: ...

### Option B — Better analytical redesign
- Best when: ...
- Chart: ...
- Encoding: ...
- What it fixes/reveals: ...
- Tradeoff: ...

### Option C — Different story lens
- Best when: ...
- Chart: ...
- Encoding: ...
- What it reveals: ...
- Tradeoff: ...

## Implementation notes
- Title/annotation: ...
- Caveats/checks: ...
```

For quick asks: verdict, top 3 fixes, and 2 redesign alternatives.

---
name: dataviz-critique
description: Critique charts with Fung's trifecta, then suggest 2-3 stronger visualization alternatives.
---

# Dataviz Critique

Use this when the user gives a visualization, screenshot, chart spec, code output, dashboard, or slide and asks whether it works or how to improve it.

Core job: diagnose whether the visual makes the right thing easy to see, hard to misread, and worth seeing; then offer a small set of better visualization alternatives, not just criticism.

Own diagnosis, severity, and alternative interventions. Do not create a parallel chart-style rubric here. Apply `dataviz-selector` to judge form, `karthik-data-visualization` to judge execution, and `chart-annotations` to judge on-chart callouts. Use `dataviz-eval` instead when the job is a formal `Send`/`Revise`/`Redesign` gate.

## Inputs to seek or infer

Prefer not to block. If context is missing, critique from what is visible and mark assumptions.

- Visualization: image, code, description, or rendered chart.
- Question: what decision, claim, or curiosity the chart is meant to answer.
- Data: fields, grain, units, source, transformations, missingness, uncertainty.
- Audience: expert/general/manager; expected data literacy; viewing medium.
- Intended message: the one sentence the viewer should leave with.

## First pass: say what it is

Before critique, identify:

1. Chart type and encodings.
2. Apparent question or claim.
3. Main thing the visual makes salient.
4. Likely audience interpretation.
5. Any assumptions due to missing context.

If the chart is impossible to interpret, say so directly and explain why.

## Trifecta checkup

Apply Kaiser Fung's trifecta as the top-level diagnostic:

- **Question**: Is there a clear, worthwhile question or decision? Is the chart answering one main thing rather than trying to be everything?
- **Data**: Does the chosen data actually answer that question? Check grain, units, denominators, time windows, baselines, selection effects, missing values, transformations, and uncertainty.
- **Visual**: Does the encoding faithfully and efficiently reveal the relevant pattern? Check chart type, axes, scales, labels, colours, ordering, grouping, annotations, legends, and visual hierarchy.

Then inspect pairwise fit:

- **Question ↔ Data**: Right measure for the claim? Any proxy pretending to be the real thing? Any bad denominator or nonsensical comparison?
- **Data ↔ Visual**: Does the visual preserve magnitudes, ranks, distributions, uncertainty, and comparisons without distortion?
- **Visual ↔ Question**: Does the first-read visual answer the intended question, or does it surface a different story?

A chart can be visually attractive and still fail if any side of this triangle is weak.

## Diagnostic ownership

- Judge the question-data relationship here: dimensional consistency, denominators, statistical meaning, uncertainty, and whether the claim outruns the evidence.
- Import form and visual-execution findings from the owning skills rather than restating their rules.
- Recommend repeatable changes that survive new data and reruns, not one-off cosmetic coordinates, colours, or dimensions learned from the supplied image.

## Failure modes to look for

### Meaning and data

- No clear question, too many questions, or a chart that answers the wrong question.
- Numerator/denominator mismatch; rates vs counts confusion; market cap vs GDP-style dimensional nonsense.
- Aggregation hiding distribution, outliers, subgroup reversal, cohort differences, or sample-size changes.
- Cherry-picked start/end dates, missing baseline, missing counterfactual, missing uncertainty.
- Derived metrics unexplained; index values without base; log/normalization not disclosed.

### Visual form and execution

- Apply `dataviz-selector` to test whether the form exposes the intended comparison.
- Apply `karthik-data-visualization` to test hierarchy, identification, colour, spacing, typography, integrity, and delivery-size execution.
- Apply `chart-annotations` only when on-chart marking is part of the problem.

### Communication

- Compare the apparent question and claim with the intended ones.
- Flag missing context or caveats that change the reading.
- Keep adjacent narration out of scope; `chart-explainer` owns the note that travels with a finished chart.

## Severity rubric

Assign severity to each issue:

- **Fatal**: likely changes the conclusion or makes the chart uninterpretable. Must fix before use.
- **Major**: materially slows or misleads interpretation. Fix strongly recommended.
- **Minor**: polish/readability issue; fix if time allows.

Do not over-focus on minor style while fatal data/question problems remain.

## Improvement workflow

1. Restate the intended claim in one sentence. If absent, propose the strongest defensible claim.
2. Name the top 3 problems by severity, not by order seen.
3. For each problem, explain impact: what would a viewer misunderstand or miss?
4. Give concrete fixes: data change, chart-type change, encoding change, annotation/copy change, or layout change.
5. Propose 2-3 visualization alternatives when the user wants redesign, the current chart is weak, or multiple defensible story angles exist.
6. For each alternative, explain the analytical purpose, chart form, encoding, what it fixes/reveals, and its tradeoff.
7. If useful, give a before/after title: current descriptive title → claim-first title.
8. If context is insufficient, list exact checks needed rather than pretending certainty.

## Redesign alternatives

When proposing alternatives, do not list random chart types. Each option must represent a distinct intervention level or analytical purpose. Prefer two options when the fix is obvious; use three when there are genuinely different story angles.

Use this option set by default:

1. **Minimal repair** — keep the original chart form where possible; fix labels, title, axis, scale, colour, ordering, annotation, and caveats. Best when the chart type is basically right but execution is poor.
2. **Better analytical redesign** — change the chart form to better answer the stated question. Best when the current encoding is wrong for the comparison.
3. **Different story lens** — reframe the view around a more revealing analytical question: totals → rates, average → distribution, snapshot → trend, level → change, ranking → decomposition, geography → comparison, dashboard → interpreted action. Best when the original question is underspecified or less useful than another defensible question.

For each option, include:

- Best when: when this option is appropriate.
- Chart: the form to use.
- Encoding: x/y/colour/facet/label/scale/order.
- What it fixes or reveals: the viewer benefit.
- Tradeoff: what this option loses, simplifies, or assumes.

If only one redesign is defensible, say so and give one strong option rather than padding.

## Output format

Use this structure by default:

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

For quick requests, compress to: verdict, top 3 fixes, and 2 redesign alternatives.

## Tone

Be direct but useful. Avoid generic praise. Praise only what materially helps interpretation. Do not say "nice visualization" unless the question-data-visual fit is actually strong.

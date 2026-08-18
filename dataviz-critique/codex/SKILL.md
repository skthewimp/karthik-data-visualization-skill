---
name: dataviz-critique
description: Critique charts with the question-data-visual triangle, semantic clarity, and evidence-fit principles, then suggest alternatives when useful.
---

# Dataviz Critique

Use this when the user gives a visualization, screenshot, chart spec, code output, dashboard, or slide and asks whether it works or how to improve it.

Core job: diagnose whether the visual makes the right thing easy to see, hard to misread, and worth seeing. In a `dataviz-fix` case, return a structured repair brief that becomes the creator's first implementation contract, not advisory prose.

## Inputs to seek or infer

Prefer not to block. If context is missing, critique from what is visible and mark assumptions.

- Visualization: image, code, description, or rendered chart.
- Question: what decision, claim, or curiosity the chart is meant to answer.
- Data: fields, grain, units, source, transformations, missingness, uncertainty.
- Audience: expert/general/manager; expected data literacy; viewing medium.
- Intended message: the one sentence the viewer should leave with.

## First pass: say what it is

Run a semantic ambiguity scan before stylistic critique: does the visual invite a materially wrong interpretation of the measure, denominator/universe, time/context, claim strength, or units? Classify each ambiguity as fatal/major/minor based on how much it changes the reader's interpretation.

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

## Karthik critique lens

Use these standards aggressively:

- **Clarity first**: the chart must stand on its own. Missing axis labels, unclear units, ambiguous chart type, unexplained shading, or mystery encodings are major failures.
- **Intentional design**: every colour, annotation, shade, line, sort order, and layout choice must earn its place. Defaults are not a defence.
- **Fundamentals before polish**: check dimensional consistency, denominators, statistical meaning, uncertainty, and whether comparisons make analytical sense.
- **Narrative with evidence**: a good chart communicates a point of view, not just numbers. If there is no claim, propose one; if the claim outruns the data, pull it back.
- **No tool worship**: do not excuse dashboard clutter, BI defaults, AI-generated aesthetics, or flashy chart types if they add friction.
- **Repeatable improvement**: recommend changes that can survive new data and reruns, not one-off cosmetic hacks.

## Failure modes to look for

### Meaning and data

- No clear question, too many questions, or a chart that answers the wrong question.
- Numerator/denominator mismatch; confusion between levels, counts, rates, shares, indices, changes, or other measures; incompatible units.
- Aggregation hiding distribution, outliers, subgroup reversal, cohort differences, or sample-size changes.
- Cherry-picked start/end dates, missing baseline, missing counterfactual, missing uncertainty.
- Derived metrics unexplained; index values without base; log/normalization not disclosed.

### Visual encoding

- Use a form that preserves the relevant magnitude, comparison, uncertainty, and spatial meaning; commonly risky forms require explicit justification rather than blanket prohibition.
- Poor ordering: alphabetical when value/rank/time/order matters.
- Overplotting, excessive categories, illegible labels, crowded legends.
- Colour without meaning, too many similar hues, inaccessible contrast, red/green dependence, decorative palettes.

### Communication

- Title describes chart mechanics instead of making a claim.
- Annotation explains the obvious, not the insight.
- Legend forces back-and-forth lookup when direct labels would work.
- Important caveats hidden in footnotes or absent.
- Dashboard gives metrics but no interpretation, action, or priority.

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

For a repair brief, make the repair/redesign decision explicit. Choose `redesign` when the question, evidence-to-claim relationship, or chart form blocks the intended comparison; otherwise choose `repair`. Set `form_questioned` independently so `dataviz-selector` is invoked whenever the form is implicated. State observable conditions the replacement must satisfy and what must survive unchanged.

## Redesign alternatives

Offer alternatives only when they address a diagnosed mismatch. Choose the number and kind of alternatives from the question, data, audience, medium, and constraints; do not force a fixed taxonomy or count. A minimal repair may be enough, and a redesign may be inappropriate when the evidence or question is the real limitation.

## Structured repair brief

For every `dataviz-fix` handoff, return this contract as JSON (or the equivalent structure when no case manager is present):

```json
{
  "context_version": 1,
  "apparent_question": "...",
  "apparent_claim": "...",
  "evidence_limitations": ["..."],
  "findings": {
    "fatal": [{"id": "c1", "problem": "...", "reader_consequence": "...", "observable_condition": "..."}],
    "major": [{"id": "c2", "problem": "...", "reader_consequence": "...", "observable_condition": "..."}],
    "minor": [{"id": "c3", "problem": "...", "reader_consequence": "...", "observable_condition": "..."}]
  },
  "highest_consequence_findings": ["c1", "c2", "c3"],
  "misleading_reader_interpretation": "...",
  "defensible_interpretation": "...",
  "intervention": "repair|redesign",
  "form_questioned": false,
  "required_delivered_outcomes": ["..."],
  "preserve": ["..."]
}
```

Always identify exactly three highest-consequence findings, while retaining every additional fatal, major, and minor finding in its severity list. `required_delivered_outcomes` must be observable in the replacement artifact. `preserve` must name source context, evidence, wording, mappings, or geometry that should not regress.

For a critique that is not part of repair implementation, use this reader-facing structure:

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

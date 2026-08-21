---
name: dataviz-critique
description: Critique charts with the question-data-visual triangle, semantic clarity, and evidence-fit principles, then suggest alternatives when useful.
---

# Dataviz Critique

Use this when the user gives a visualization, screenshot, chart spec, code output, dashboard, or slide and asks whether it works or how to improve it.

Core job: diagnose whether the visual makes the right thing easy to see, hard to misread, and worth seeing. In the default `dataviz-fix` path, keep this diagnosis concise and move directly to a repaired artifact. Return a structured repair brief only when the user explicitly requests an audited workflow.

## Inputs to seek or infer

Prefer not to block. If context is missing, critique from what is visible and mark assumptions.

- Visualization: image, code, description, or rendered chart.
- Question: what decision, claim, or curiosity the chart is meant to answer.
- Data: fields, grain, units, source, transformations, missingness, uncertainty.
- Audience: expert/general/manager; expected data literacy; viewing medium.
- Intended question, takeaway, decision, or honest null result.

## First pass: say what it is

Run a semantic ambiguity scan before stylistic critique: does the visual invite a materially wrong interpretation of the measure, denominator/universe, time/context, claim strength, or units? Classify each ambiguity as fatal/major/minor based on how much it changes the reader's interpretation.

Before critique, identify:

1. Chart type and encodings.
2. Apparent question or claim.
3. Main thing the visual makes salient.
4. Likely audience interpretation.
5. Any assumptions due to missing context.

For a repair handoff, also freeze a source inventory before proposing changes: chart/panel structure; every visible period, category, series, unit, qualification, source note, and annotation that can change the reading; semantic colour/shape/order mappings; repeated instances; and anything too uncertain to reproduce. Diagnose the full artifact and neighbouring zones, not only the defect named by the user. The inventory is the raw catalogue of what is present; the key-messages judgment below decides which of it must survive.

If the chart is impossible to interpret, say so directly and explain why.

## Key messages and required content

Cataloguing what a chart contains is not the same as judging what matters. After the inventory, decide - as a judgment call, not a preserve-everything rule - what the rebuild must carry.

- **Key messages.** From the trifecta and the source, state the one or few messages the chart exists to carry (for example: "total usage is growing exponentially" *and* "the mix is shifting away from a dominant incumbent"). A chart may legitimately carry more than one.
- **The form declares its messages.** What a chart encodes as its primary structure is presumptively a key message. A stacked, multi-series, or faceted chart exists to show composition or comparison across those categories - that comparison *is* a message, not optional detail. Treat the primary encoded dimension (whatever colour, stack, or facet carries) as key unless the prompt explicitly redirects to a different question. Reducing such a chart to a single total or one series deletes its reason to exist; that is a drop of a key message, however tidy the result looks.
- **Required content per message.** For each key message, name the data and encoding a rebuild must show to support it - the specific series, periods, breakdowns, comparisons, or annotations without which the message collapses. A per-category breakdown is required content for a "the mix is shifting" message; it is not for a "the total is growing" message.
- **"Hard to recover" is not "not key".** Difficulty is never grounds to drop a dimension. "Values are approximate", "read from a screenshot", "too many categories to read exactly", "crowded legend", "would invent unreadable precision" - these are reasons to choose a *better form* (small multiples, direct-labelled lines, top-N plus an explicit "other", a share-of-total or streamgraph view), not to delete the data. Source illegibility triggers a redesign of the form; it never authorises removing the information. Approximate category values, labelled approximate, still carry the message - exact precision was never the point.
- **Explicit drops.** A drop is legitimate only when the information serves no key message - not when it is merely inconvenient to recover or render. Name what you drop and why, in message terms. Silence is not a decision: the a16z stacked chart came back as a bare total because no one decided to lose the model mix, and "category precision is unreadable" is a form problem, not a reason the mix stopped mattering.
- **One chart or several.** Note when the messages need more than one chart's worth of content (a whole-and-parts split, a totals view alongside a per-category view). Decide the messages and their required content here; leave the actual chart count, decomposition, and form to reconstruction.

Keep what carries a key message; drop what does not - out loud. When a dimension is hard to read but central, redesign the form to show it; do not drop it to avoid the difficulty.

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
- **Purpose with evidence**: a good chart communicates its analytical job and defensible result. An honest null or exploratory outcome is valid; do not invent a claim to create drama.
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

1. State the intended question, takeaway, or null result briefly. Do not manufacture a claim when the evidence is exploratory or inconclusive.
2. Rank the consequential problems by severity and reader impact. Include as many as the decision needs and no quota fillers.
3. For each problem, explain what a viewer would misunderstand or miss.
4. Give a concrete data, form, encoding, copy, or layout operation.
5. Offer alternatives only when they answer a diagnosed mismatch; choose their number and kind from the evidence, audience, medium, and constraints.
6. For each useful alternative, explain its analytical purpose, encoding, benefit, and tradeoff.
7. If context is insufficient, list the checks needed rather than pretending certainty.

For an audited repair brief, make the repair/redesign decision explicit. Choose `redesign` when the question, evidence-to-claim relationship, or chart form blocks the intended comparison; otherwise choose `repair`. Set `form_questioned` independently so `dataviz-selector` is invoked whenever the form is implicated. State observable conditions the replacement must satisfy and what must survive unchanged.

## Redesign alternatives

Offer alternatives only when they address a diagnosed mismatch. Choose the number and kind of alternatives from the question, data, audience, medium, and constraints; do not force a fixed taxonomy or count. A minimal repair may be enough, and a redesign may be inappropriate when the evidence or question is the real limitation.

## Optional structured repair brief

When an audited `dataviz-fix` workflow is explicitly selected, return this contract as JSON:

```json
{
  "context_version": 1,
  "apparent_question": "...",
  "apparent_claim": "...",
  "evidence_limitations": ["..."],
  "source_inventory": {
    "structure": ["..."],
    "required_content": ["every visible period, category, unit, qualification, source note, and annotation that must survive"],
    "semantic_mappings": ["..."],
    "uncertainties": ["..."]
  },
  "key_messages": [
    {"message": "...", "required_content": ["series/periods/breakdowns/comparisons this message needs"]}
  ],
  "dropped_as_not_key": [{"item": "...", "reason": "..."}],
  "chart_count_hint": "one|several - several when messages need whole-and-parts or separate views",
  "layout_risks": ["longest labels, dense regions, neighbouring zones, repeated placements, and outer-edge risks"],
  "findings": {
    "fatal": [],
    "major": [{"id": "c1", "problem": "...", "reader_consequence": "...", "observable_condition": "..."}],
    "minor": []
  },
  "highest_consequence_findings": ["c1"],
  "misleading_reader_interpretation": "...",
  "defensible_interpretation": "...",
  "intervention": "repair|redesign",
  "form_questioned": false,
  "required_delivered_outcomes": ["..."],
  "preserve": ["..."]
}
```

Rank the findings that actually determine the intervention; do not require or invent a fixed number. Retain every additional fatal, major, and minor finding in its severity list. `required_delivered_outcomes` must be observable in the replacement artifact. `preserve` must name source context, evidence, wording, mappings, or geometry that should not regress.

`source_inventory.required_content` and `semantic_mappings` are not optional summaries. Enumerate the source elements whose omission, shortening, reassignment, or relabelling could change the reading. `layout_risks` must anticipate the most failure-prone geometry before implementation, including long text and adjacent zones.

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

## Key messages and required content
- Key message(s): ...
- Required content for each: ...
- Dropped as not key (with reason): ...
- One chart or several: ...

## Issues to fix
1. **[Fatal/Major/Minor] Issue** — impact. Fix: ...
2. ...
3. ...

## Recommended alternatives

Repeat this block only for alternatives that solve a diagnosed mismatch:

### <Purpose>
- Best when: ...
- Encoding: ...
- What it fixes or reveals: ...
- Tradeoff: ...

## Implementation notes
- Title/annotation: ...
- Caveats/checks: ...
```

For quick requests, return the verdict and the smallest consequential fix set. Add alternatives only when redesign is useful.

## Tone

Be direct but useful. Avoid generic praise. Praise only what materially helps interpretation. Do not say "nice visualization" unless the question-data-visual fit is actually strong.

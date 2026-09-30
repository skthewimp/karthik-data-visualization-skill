---
name: dataviz-critique
description: Critique charts with the question-data-visual triangle and evidence fit, suggest alternatives, and write the repair brief (key messages, constraints, edit-vs-redesign) before a rebuild.
---

# Dataviz Critique

Use when the user gives a visualization, screenshot, chart spec, code output, dashboard, or slide and asks whether it works or how to improve it. Core job: diagnose whether the visual makes the right thing easy to see, hard to misread, and worth seeing.

## Three roles

1. **Standalone review** - the user shows a chart and asks "what's wrong?" or "how do I improve it?". Run the full diagnosis below and return the reader-facing structure. Primary use.
2. **Repair brief** - at the **start** of a chart repair, before any chart is chosen or built, state what the replacement must say and carry. See [Repair brief](#repair-brief); it replaces the standalone output structure.
3. **Checker against an existing brief** - a candidate arrives with a brief that already names the intent (key messages and required content). Run *after* the candidate is built, as a checker not the designer: don't re-derive the key messages (the brief owns them) and don't reopen the form choice unless the candidate genuinely fails a message. Answer: does the candidate carry the brief's intent (every key message with its required content, nothing key silently dropped, prompt constraints honoured), and is it a good chart (mechanical and semantic)? Run in-context, consolidate into one focused revision per pass, cap at two passes, exit as soon as no fatal or major defect remains.

## Inputs to seek or infer

Prefer not to block. If context is missing, critique from what's visible and mark assumptions.

- Visualization: image, code, description, or rendered chart.
- Question: what decision, claim, or curiosity the chart answers.
- Data: fields, grain, units, source, transformations, missingness, uncertainty.
- Audience: expert/general/manager; expected literacy; viewing medium.
- Intended question, takeaway, decision, or honest null result.

## First pass: say what it is

Run a semantic ambiguity scan before stylistic critique: does the visual invite a materially wrong interpretation of the measure, denominator/universe, time/context, claim strength, or units? Classify each ambiguity fatal/major/minor by how much it changes the reading.

Before critique, identify: chart type and encodings; apparent question or claim; the main thing made salient; likely audience interpretation; assumptions from missing context.

For a repair handoff, also freeze a source inventory before proposing changes: chart/panel structure; every visible period, category, series, unit, and annotation that can change the reading; qualifications that change how the data reads (projected, excludes X, fiscal year); semantic colour/shape/order mappings; repeated instances; anything too uncertain to reproduce. Diagnose the full artifact and neighbouring zones, not only the defect the user named. The inventory is the raw catalogue; the key-messages judgment below decides which of it must survive. Furniture (axis titles, legends, notes, the source's hedges) is catalogued for its information, not as something to keep: it survives only if the rebuild has no better home for that information.

If the chart is impossible to interpret, say so directly and explain why.

## Key messages and required content

This section is the reasoning for **standalone review** and for **writing the repair brief**. When checking a candidate against a brief that already names the key messages and required content, that judgment is the brief's - verify against it, don't re-make it.

Cataloguing what a chart contains is not judging what matters. After the inventory, decide - as a judgment call, not a preserve-everything rule - what the rebuild must carry.

- **Key messages.** From the trifecta and source, state the one or few messages the chart exists to carry (e.g. "total usage is growing exponentially" *and* "the mix is shifting away from a dominant incumbent"). More than one is legitimate.
- **The form declares its messages.** What a chart encodes as its primary structure is presumptively a key message: a stacked, multi-series, or faceted chart exists to show that composition or comparison. Treat the primary encoded dimension (whatever colour, stack, or facet carries) as key unless the prompt redirects to a different question. Reducing such a chart to a single total or one series drops a key message, however tidy the result.
- **Preserving the message is not preserving the form.** The data must survive; the *encoding* often should not. Re-rendering the source form more cleanly fails the message when that form was what made it hard to read - a tidier many-series stack no reader can trace one series through, a dual-axis chart implying an unsupported correlation, a map used for a ranking, a too-fine pie. When the source form is why a key message is hard to read, changing the form *is* the repair; reproducing it is the bug.
- **Required content per message.** For each key message, name the data and encoding a rebuild must show - the specific series, periods, breakdowns, comparisons, or annotations without which it collapses. A per-category breakdown is required for "the mix is shifting", not for "the total is growing".
- **"Hard to recover" is not "not key".** Difficulty (approximate values, too many categories, unrecoverable labels, a legend naming fewer categories than encoded) is grounds for a *better form* (small multiples, direct-labelled lines, top-N plus explicit "other", share-of-total), never to delete data. When some labels can't be recovered, keep the categories and name the unrecovered ones generically. A value the source draws but does not print is measured from the mark's geometry and used, not dropped, gapped, or noted as missing. Approximate values and imperfect labels still carry the message - and the chart never says they are approximate; that goes in the report.
- **Explicit drops.** A drop is legitimate only when the information serves no key message, not when it's inconvenient to recover or render. Name what you drop and why, in message terms. Silence is not a decision: a multi-category chart reduced to a bare total has silently lost the breakdown.
- **One chart or several.** Note when the messages need more than one chart (whole-and-parts, a totals view alongside a per-category view). Decide messages and required content here; leave chart count, decomposition, and form to reconstruction.

## Repair brief

Run at the start of a repair, in parallel with `dataviz-extract` (which recovers the data table). Its job is the intent the replacement must serve, so everything downstream is designed *forward* from it rather than patched onto the source.

**Don't critique the source here.** A repair that opens with a fault-list anchors on the existing image, and the path of least resistance becomes "re-render the same form, tidied" - which fails a whole class of charts, most visibly a many-series stacked bar whose message is per-series comparison. Freeze the source inventory, then decide the key messages, required content per message, and explicit drops exactly as in [Key messages and required content](#key-messages-and-required-content). Decide *what the chart must say and carry*, never *how it should look*: form is `dataviz-selector`'s, chosen afterwards and cold.

Then add what a rebuild needs that a standalone review doesn't:

- **Audience and medium:** who reads it, expected literacy, viewing size (slide, chat, thumbnail, print).
- **Story:** the one-sentence point, if the prompt or evidence implies one. Don't manufacture a claim when the evidence is exploratory.
- **Constraints from the prompt:** requested chart type, annotations, wording, brand/style, what to fix. These are authoritative and survive the whole repair; when a later redesign impulse conflicts with one, the constraint wins.
- **Mode**, which decides whether the form is reopened:
  - **`bounded-edit`** - a literal, self-contained change leaving the form intact and correct ("fix the axis labels", "change the title", "recolour series 3", "remove the gridlines"). Choose only when the existing form genuinely serves the messages and the prompt doesn't question it.
  - **`redesign`** - everything else: a new question, a weak or misleading form, a per-series message trapped in a stack, "make this clearer", or no prompt. The source form gets no vote.

  When in doubt, choose `redesign` - a bounded edit that needs a form change can be widened; a redesign wrongly narrowed to an edit reproduces the source's weakness.
- **Keep-notes (thin):** a genuinely reusable source idea - a smart annotation, a sensible top-N-plus-"other" grouping, a sensible period window. Not a fault-list, not a defence of the form; "none" is a fine answer. A magnitude **scale or baseline is never a keep-note**: where a length encoding starts and the range an axis spans are form decisions the selector and build own from the data. A source whose bars start above the quantity's zero is defective, and recording its zoomed range as context to carry is exactly how a truncated source reproduces itself.

```markdown
Key messages:
  - <message> - required content: <series/periods/breakdowns/comparisons>
Dropped as not key (with reason): <item - why, in message terms | none>
One chart or several: <...>
Audience / medium: <who, literacy, viewing size>
Story: <one-sentence point | exploratory, no single claim>
Constraints (authoritative): <chart type, annotations, wording, style, what to fix | none>
Mode: bounded-edit | redesign
Keep-notes: <reusable source ideas | none>
```

## Trifecta checkup

Kaiser Fung's trifecta as the top-level diagnostic:

- **Question:** a clear, worthwhile question or decision? Answering one main thing, not everything?
- **Data:** does the chosen data actually answer it? Check grain, units, denominators, time windows, baselines, selection effects, missing values, transformations, uncertainty.
- **Visual:** does the encoding faithfully and efficiently reveal the pattern? Check chart type, axes, scales, labels, colours, ordering, grouping, annotations, legends, hierarchy.

Then pairwise fit:

- **Question ↔ Data:** right measure for the claim? A proxy pretending to be the real thing? A bad denominator or nonsensical comparison?
- **Data ↔ Visual:** does the visual preserve magnitudes, ranks, distributions, uncertainty, and comparisons without distortion?
- **Visual ↔ Question:** does the first read answer the intended question, or surface a different story?

A chart can be attractive and still fail if any side of the triangle is weak.

## Karthik critique lens

- **Production, not provenance:** every chart is for publication. Text that hedges, reports provenance, or explains what the source lacks is a major failure wherever it sits; limitations go in the accompanying report. The title keeps the source's subject and scope, and its numbers carry only the precision the spread supports.
- **Clarity first:** the chart must stand alone. Unrecoverable units, ambiguous type, unexplained shading, mystery encodings are major failures. The test is whether the reader can recover the information, not whether a particular element carries it: an axis title that repeats the ticks or the title is ink, not clarity.
- **Less is more:** every axis, axis title, legend, gridline, subtitle and note must carry something the reader can't get from the title, direct labels, or tick labels. A legend the reader has to look back and forth to is a major failure when the series could be labelled in place or keyed by coloured words.
- **Read at display size:** judge type and layout at the width the reader sees the image, not native pixels. A canvas whose shape fights its content (many panels in a narrow column, big marks with tiny labels, equal space for unequal panels) is a major failure.
- **Intentional design:** every colour, annotation, shade, line, sort order, and layout choice earns its place. Defaults are not a defence.
- **Fundamentals before polish:** dimensional consistency, denominators, statistical meaning, uncertainty, whether comparisons make analytical sense.
- **Purpose with evidence:** communicate the analytical job and a defensible result. An honest null or exploratory outcome is valid; don't invent a claim for drama.
- **No tool worship:** don't excuse dashboard clutter, BI defaults, AI-generated aesthetics, or flashy types that add friction.
- **Repeatable improvement:** recommend changes that survive new data and reruns, not one-off cosmetic hacks.

## Failure modes to look for

**Meaning and data:** no clear question, too many, or the wrong one; numerator/denominator mismatch or confusion between levels, counts, rates, shares, indices, changes; incompatible units; aggregation hiding distribution, outliers, subgroup reversal, cohort differences, or sample-size changes; cherry-picked dates, missing baseline/counterfactual/uncertainty; unexplained derived metrics, index without base, undisclosed log/normalization.

**Visual encoding:** a form that loses the relevant magnitude/comparison/uncertainty/spatial meaning (risky forms need justification, not blanket prohibition); poor ordering (alphabetical when value/rank/time matters); overplotting, excessive categories, illegible labels, crowded legends; colour without meaning, too many similar hues, inaccessible contrast, red/green dependence, decorative palettes.

**Communication:** title describing mechanics instead of a claim; annotation explaining the obvious not the insight; a legend forcing lookup where direct labels would work; hedges or provenance notes on the chart that belong in the accompanying report; a dashboard giving metrics but no interpretation, action, or priority.

## Severity rubric

- **Fatal:** likely changes the conclusion or makes the chart uninterpretable. Must fix.
- **Major:** materially slows or misleads interpretation. Fix strongly recommended.
- **Minor:** polish/readability; fix if time allows.

Don't over-focus on minor style while fatal data/question problems remain. Contrast, colour and emphasis rank by the reading they break: text that reads at delivery size, series the reader can tell apart, and one uncontested focal are not findings, however you would have styled them.

## Improvement workflow

1. State the intended question, takeaway, or null briefly. Don't manufacture a claim when the evidence is exploratory.
2. Rank consequential problems by severity and reader impact - as many as the decision needs, no quota fillers.
3. For each, explain what a viewer would misunderstand or miss.
4. Give a concrete data, form, encoding, copy, or layout operation.
5. Offer alternatives only when they answer a diagnosed mismatch; choose their number and kind from evidence, audience, medium, constraints.
6. For each useful alternative, explain its analytical purpose, encoding, benefit, tradeoff.
7. If context is insufficient, list the checks needed rather than pretending certainty.

## Redesign alternatives

Offer alternatives only when they address a diagnosed mismatch; choose their number and kind from question, data, audience, medium, and constraints - no fixed taxonomy or count. A minimal repair may be enough; a redesign may be wrong when the evidence or question is the real limitation.

Return this reader-facing structure:

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

## Recommended alternatives

Repeat this block only for alternatives that solve a diagnosed mismatch:

### <Purpose>
- Best when: ...
- Encoding: ...
- What it fixes or reveals: ...
- Tradeoff: ...

## Implementation notes
- Title/annotation: ...
- Checks for the run report (never on the chart): ...
```

For quick requests, return the verdict and the smallest consequential fix set; add alternatives only when redesign is useful.

## Tone

Be direct but useful. Avoid generic praise; praise only what materially helps interpretation. Don't say "nice visualization" unless the question-data-visual fit is actually strong.

---
name: dataviz-eval
description: Evaluate rendered data visualizations for send/revise/redesign decisions, blind expert and audience reads, chart-agent benchmarks, regression tests, and reusable failure analysis.
---

# Dataviz Eval

Measure whether a visualization does its job. Do not turn evaluation into a generic style critique or a second attempt at chart creation.

Use two modes:

1. **Artifact gate** - decide whether one rendered visualization can be sent.
2. **Creator-system benchmark** - measure whether a chart-producing agent, prompt, or skill improves across representative cases.

Read `references/evaluation-framework.md` when setting up a benchmark, assigning failure codes, calibrating reviewers, or deciding whether an observed failure should change a skill.

## Keep the roles separate

- `dataviz-selector` chooses a form before plotting.
- `karthik-data-visualization` guides chart construction and styling.
- `dataviz-critique` diagnoses broadly and proposes alternatives.
- `dataviz-eval` measures the current artifact against an intended outcome and sets the pass line.
- `dataviz-fix` executes the revisions and records feedback.

An evaluation may recommend `Revise` or `Redesign`, but it should not silently rebuild the chart.

## Artifact gate

### 1. Establish the evaluation packet

Capture, when available:

- the actual exported artifact
- the source data or source chart
- the intended analytical question
- the intended insight, including an honest "no clear pattern" outcome
- the audience and what they should understand or do
- the delivery medium and real display size
- the active user corrections, each rewritten as an observable before-to-after acceptance check

Set the evidence scope explicitly:

- **Data validation** when underlying data and calculations are available or factual verification is requested.
- **Source fidelity** when repairing a supplied chart without its underlying data. Verify that the repair preserves the source values, categories, qualifications, and provenance; do not pretend to validate the upstream source.

Keep intended question and insight out of the first two reads. If either is missing, do not invent it. Mark the comparison `Unknown` later.

Do not block on every missing field. Judge evidence against the declared scope. A source-fidelity check can pass without underlying data, but state that upstream accuracy was not tested.

### 2. Inspect the delivered artifact

Open the PNG, SVG, PDF, slide, screenshot, or dashboard at the size the audience will actually see. For chat, inspect the thumbnail or compressed image. For slides, inspect the full slide from normal viewing distance.

Do not invent a fixed display width. If the exact size is unknown, use a representative preview and report the assumption. Mark delivery `Fail` only when the tested artifact breaks or the failure is clear across plausible sizes; otherwise use `Concern` or `Unknown`. Distinguish a self-contained thumbnail requirement from a tap-to-expand chat image.

Treat the export as the source of truth. Do not approve a browser viewport, plotting window, HTML source, or code path that differs from the delivered media file. For a chat workflow, evaluate the exact PNG, JPEG, SVG, or PDF that will be attached.

### 3. Run an expert blind read

Without using the stated intent, record:

- the question the chart appears to answer
- the main point it appears to make
- how much effort the reading requires
- whether title, chart form, metrics, encodings, labels, highlights, and notes agree
- render-specific failures such as clipping, overlap, truncation, false precision, or broken mappings

Focus on relationships the creator can miss. Do not mechanically replay every chart-making rule.

### 4. Run an audience blind read

Adopt the audience's knowledge, time, and viewing conditions. Without using the stated intent, record:

- what question the chart answers
- what point is remembered after a quick look
- what remains uncertain or easy to misread
- what action or conclusion follows, if one is intended
- how much work the reading takes

For every creator-system release gate, use a fresh reviewer so the blind read is genuine. The chart creator cannot also issue `Send`. Give the reviewer the raw source and delivered artifact, not the creator's diagnosis, claimed fixes, intended verdict, or rendering code.

### 5. Reveal intent and verify evidence

Compare both blind reads with the intended question and insight. Mark each `Match`, `Partial`, `Mismatch`, or `Unknown`.

Then verify what appearance cannot establish:

- values, calculations, denominators, baselines, scales, and transformations
- units, time periods, sources, uncertainty, and material caveats
- colour, label, and legend mappings
- whether removing an axis or legend also removed information the reader still needs

Run a literal element audit before passing `Information fit` or `Delivery`:

- every required category, time point, and group remains identifiable and aligned with the correct marks; repeated labels are allowed when the structure requires them, but orphaned, duplicated, or misbound data are not
- every direct value matches its mark and source value
- the chosen identification system fits the chart's density and geometry: direct labels must remain legible and unambiguous; axes, legends, grouping, or small multiples are valid when direct labels would not
- each category or series has one clear primary identification route; if a direct label supplies the same identity as a categorical axis or legend, the duplicate scaffolding must justify its reading value
- every legend entry has plotted marks, and its swatch exactly matches those marks
- every encoded colour remains perceptually distinct from adjacent series and the background under the intended delivery conditions
- every requested removal is absent from the delivered artifact
- every requested addition or relocation appears in the requested place

Run five release checks across chart types:

1. **Visual integrity** - inspect text against text, text against marks, marks against marks, panel boundaries, clipping, truncation, occlusion, and export geometry. Any collision or damage that changes or slows the reading fails delivery; do not solve geometry first by shrinking type.
2. **Relationship traceability** - confirm that each label, value, mark, legend entry, annotation, and reference line pairs with its target immediately at delivery size. For every label, compare the intended target with nearby competing labels and marks: the intended bond must be perceptually strongest. Judge distance to the visible target, not merely to a shared row, plot edge, or baseline; alignment alone does not bridge unstructured whitespace. Judge the complete identity-value-mark unit, not a value label in isolation. If direct placement cannot preserve that relationship, an axis, legend, grouping, or different structure is preferable.
3. **Spatial economy** - inspect whitespace by relationship: title-to-plot, labels-to-marks, between panels, plot-to-notes, and outer margins. Whitespace must establish grouping, separation, or emphasis. Blank area that splits related elements, weakens hierarchy, or wastes the delivery surface is a geometry failure; dense but well-grouped layouts can pass.
4. **Encoding semantics** - state the role of every salient colour, size, shape, order, and highlight. It must encode data, structure, uncertainty, or a declared focal point. A visually dominant encoding with no recoverable role is not optional decoration; it redirects attention and fails the relevant gate.
5. **Delivery robustness** - inspect the exact export at the intended viewing condition, including representative downscaling or compression. A full-size file cannot pass on behalf of an unreadable delivered version.

These are invariants, not prescriptions. Do not infer a preferred chart type, palette, pixel margin, number of highlights, or density threshold from one example. Judge whether the relationships remain accurate, legible, and intentional in context.

Do not accept a generic visual summary as proof of a specific edit. Inspect the named element directly. If the latest user correction fails its acceptance check, the verdict cannot be `Send`.

For stacked bars, identify what the reader must compare. Only segments that begin or end on an aligned baseline support precise visual comparison; in a fixed-total 100% stack, both outer edges align, while internal segments still float. Direct segment labels support value lookup but do not repair difficult across-bar pattern comparison. If the intended claim depends on precise component values or trends, choose a form with aligned component baselines.

Run a colour audit whenever colour carries meaning:

- state the role of colour: identity, order, direction, or emphasis; purposeless colour is a concern
- verify the scale type fits the data and the same meaning keeps the same colour across panels
- verify focal colour, saturation, and warmth match the information hierarchy rather than creating an accidental highlight
- test normal text near 4.5:1, large text near 3:1, and small or thin essential marks near 3:1 against the background as practical targets, not substitutes for visual judgment
- verify adjacent regions differ clearly, key distinctions survive grayscale and chat compression, and hue is not the only channel

Fail the relevant gate for legend-to-mark mismatch, essential marks that disappear into their background, colour-only distinctions that fail under common colour-vision deficiencies, or series that collapse into one another at delivery size. Do not require every large decorative fill to satisfy text-level WCAG contrast when labels, boundaries, and other channels make the reading robust.

For a repair, require preservation of context present in the source. Do not demand a new organisation, period, source, or denominator merely because the original also omitted it, unless the user's brief requires factual defensibility or the omission makes the claim unsafe.

Do not punish an exploratory chart for lacking a dramatic story. If the intended result is "no defensible pattern", evaluate whether that is what the reader understands.

### 6. Apply gates, not an average

Rate each gate `Pass`, `Concern`, `Fail`, or `Unknown`, and mark whether it is required by the declared scope:

1. **Evidence** - the chart is correct, complete enough, and not misleading.
2. **Question** - the intended analytical question is recoverable.
3. **Insight** - the intended point, caveat, or null result is recoverable.
4. **Visual reasoning** - chart form and encodings support the comparison rather than fighting it.
5. **Information fit** - title, labels, units, source, time, legend-to-mark mappings, and annotations agree; active correction checks pass.
6. **Delivery** - the exact media file works in its intended medium without clipping, overlap, illegibility, broken geometry, or missing attachment.

For a rendered artifact, Evidence, Visual reasoning, Information fit, and Delivery are always required. Question and Insight may be non-required only when the task genuinely supplies no intended outcome to compare; leave them `Unknown` and state what is missing. A reviewer cannot opt out of the four core artifact gates.

Accessibility or an explicit target style becomes a gate when it changes comprehension, excludes part of the audience, or is part of the stated brief. Taste alone is not a fatal failure.

Never average away a fatal error. A beautiful chart with wrong evidence, the wrong question, or unreadable delivery does not pass.

Record evidence for every gate and every release check. `Send` requires every required gate and all release checks to pass. A non-required gate must remain `Unknown`, with the missing intent or evidence named; do not manufacture a pass. A generic statement such as "clean and readable" is not evidence: name the inspected relationship, encoding role, or delivery condition.

### 7. Set the verdict

- **Send** - all gates required by the declared scope pass; only optional polish remains.
- **Revise** - the analytical design works, but bounded changes are required.
- **Redesign** - the question or insight does not land, or the visual form blocks the comparison.
- **Not evaluable** - the artifact cannot be inspected, or a required decision depends on evidence or context that is unavailable.

When some checks are possible, report them before `Not evaluable`. Never translate `Unknown` into `Pass`.

### 8. Return the minimum pass set

Rank only consequential issues. Prefer a short set that gets the artifact over the pass line.

Write every required change as an operation:

```text
Target: <element>
From: <current state>
To: <required state>
Why: <reader consequence>
Codes: <failure codes>
```

Fix geometry before shrinking type. Preserve title, subtitle, source, units, time, and mappings when changing forms. Direct labels are useful only when they remain visible, unambiguous, and complete.

## Creator-system benchmark

Do not call a handful of attractive outputs an evaluation.

1. Freeze the creator version, input contract, renderer, and delivery conditions.
2. Build a representative case set across analytical tasks, densities, audiences, media, and null/no-story cases.
3. Have reviewers label cases independently with the artifact-gate protocol.
4. Adjudicate disagreements and freeze a golden set with acceptable outcomes, not one canonical layout.
5. Compare versions using all-gates pass rate, failure modes by slice, regressions, cost, and latency.

Use open coding for novel failures, then consolidate repeated failures into stable codes. Change a creator skill only when evidence points to a reusable rule, missing tool, or ambiguous instruction. Keep one-off chart preferences in the case record.

## Output format

```markdown
## Evaluation conditions
Artifact: ...
Audience and medium: ...
Evidence available: ...

## Blind reads
Expert: question ...; point ...; effort ...
Audience: question ...; point ...; uncertainty ...; next action ...

## Gate results
| Gate | Required? | Result | Evidence |
|---|---|---|---|
| Evidence | Yes / No | Pass / Concern / Fail / Unknown | ... |
...

## Release checks
| Check | Result | Evidence |
|---|---|---|
| Visual integrity | Pass / Concern / Fail / Unknown | ... |
| Relationship traceability | Pass / Concern / Fail / Unknown | ... |
| Spatial economy | Pass / Concern / Fail / Unknown | ... |
| Encoding semantics | Pass / Concern / Fail / Unknown | ... |
| Delivery robustness | Pass / Concern / Fail / Unknown | ... |

## Verdict
Send / Revise / Redesign / Not evaluable

## Required before send
1. Target ...; from ...; to ...; why ...; codes ...

## Optional after pass
- ...
```

Omit `Optional after pass` when nothing useful remains. For a benchmark, add pass rate, slice failures, reviewer agreement, regressions, cost, and latency.

## Karthik calibration

- Judge the actual export at chat or slide size, not a large local preview.
- Treat clipping, overlap, missing necessary labels, off-canvas text, and unreadable delivery-size views as blockers.
- Match the aspect ratio to the comparison density, label geometry, and delivery medium rather than inheriting the source or renderer canvas.
- Prefer forms that expose the intended comparison directly and labels that reduce lookup effort.
- Do not remove legends, axes, sources, units, time periods, or context unless the replacement carries the same information.
- Treat low contrast and redundant encodings as comprehension costs, not merely aesthetic defects.
- Evaluate subtitle copy by what it tells the reader, not by whether it describes the chart-making process.

## Stop conditions

Stop when the artifact crosses the stated pass line. Do not keep revising for preference after `Send`.

Escalate to `dataviz-critique` when the failure is conceptual. Hand the minimum pass set to `dataviz-fix` when the changes are executable. Record repeated failure codes before proposing a skill change.

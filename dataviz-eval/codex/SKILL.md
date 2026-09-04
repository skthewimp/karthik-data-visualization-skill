---
name: dataviz-eval
description: Evaluate rendered data visualizations for send/revise/redesign decisions, blind expert and audience reads, chart-agent benchmarks, regression tests, and reusable failure analysis.
---

# Dataviz Eval

Measure whether a visualization does its job. Do not turn evaluation into a generic style critique or a second attempt at chart creation.

Two modes:

1. **Artifact gate** - decide whether one rendered visualization can be sent.
2. **Creator-system benchmark** - measure whether a chart-producing agent, prompt, or skill improves across representative cases.

Read `references/evaluation-framework.md` when setting up a benchmark, assigning failure codes, calibrating reviewers, or deciding whether a failure should change a skill.

## Keep the roles separate

- `dataviz-selector` chooses a form before plotting.
- `karthik-data-visualization` guides construction and styling.
- `dataviz-critique` diagnoses broadly and proposes alternatives.
- `dataviz-eval` measures the current artifact against an intended outcome and sets the pass line.
- `dataviz-fix` executes revisions and records feedback.

An evaluation may recommend `Revise` or `Redesign` but must not silently rebuild the chart.

## Artifact gate

### Semantic ambiguity audit (mandatory)

Before passing Evidence, Question, Insight, or Information fit, test whether the visual semantics support the reader's likely interpretation - not only whether the numbers are legible:

- **Measure meaning:** mark, scale, wording, and units make clear whether the quantity is a level, count, rate, share, index, change, or other derived measure. The form must not invite a materially different dimensional reading.
- **Time and context:** claims about periods, transitions, interventions, or events need a supported, understandable boundary. Don't leave a meaningful reference point implicit or use a vague temporal phrase when its reading changes the conclusion.
- **Universe and denominator:** make clear what the categories include, exclude, and sum to. A subset, proxy, or selected decomposition must not appear exhaustive without evidence.
- **Claim strength:** titles, annotations, takeaways must not imply causation, comparison, improvement, or an outcome unless the baseline, comparator, mechanism, and direction are established.
- **Audience meaning:** units, transformations, and conventions must be interpretable for the audience; add context or an equivalent representation without silently changing the measure.

Record each ambiguity as a concrete required check with the misleading reading, the defensible reading, and the evidence needed to tell them apart. These are principles, not a vocabulary list or a prescribed visual fix. When the packet supplies a `semantic_checks` template, return one result per named dimension; don't collapse them into the six gates or assume a clear axis fixes a conflicting title, universe, claim, or convention. Treat the creator's semantic preflight as a hypothesis to challenge against source and exact artifact.

### 1. Establish the evaluation packet

Capture when available: the exported artifact; source data or source chart; intended question; intended insight (including an honest "no clear pattern"); audience and desired understanding/action; delivery medium and real display size; the active change contract (each requested addition, removal, relocation, and preservation constraint as an observable before-to-after check); the original critique and any prior repair plan; the frozen source inventory, preservation mappings, and pre-build layout-risk plan; every open action from prior evaluations and every active user acceptance check; deterministic full/delivery/panel/hierarchy/dense-placement views plus the revision comparison.

Treat these as one contract stack for the exact replacement artifact - don't evaluate a generic idea of the chart or substitute a new critique. **Every fatal/major critique finding, active user check, prior evaluator action, semantic check, and mechanical defect must get an explicit result; only `Pass` closes it.**

Audit the pre-build plan against the source before judging the candidate. If the inventory omitted a visible period, category, qualification, mapping, repeated instance, or neighbouring-zone risk that could change the reading, fail plan compliance and add the missing item to the minimum pass set. A creator cannot pass by faithfully executing an incomplete plan. Then verify every inventoried required item and semantic mapping in the candidate.

Set evidence scope explicitly:

- **Data validation** when underlying data/calculations are available or factual verification is requested.
- **Source fidelity** when repairing a supplied chart without its data: verify the repair preserves source values, categories, qualifications, and provenance; don't pretend to validate the upstream source, and state that upstream accuracy was not tested.

Missing underlying data is a hard boundary: do not pass invented, reconstructed, or visually estimated subcomponents as factual evidence. If a redesign needs values not in the source, omit those encodings, label them approximate, or mark the artifact Not evaluable.

Keep intended question and insight out of the first two reads; if either is missing, don't invent it (mark the comparison `Unknown` later). After intent reveal, compare every structured context field's provenance with the verbatim request - an `inferred` question, message, or purpose is not user intent and cannot justify a pass the source or artifact doesn't support.

Audit claim strength separately from rendering: every title, subtitle, annotation, and takeaway must be no stronger than the evidence shown. A plausible narrative is not evidence of causation or effect; downgrade or fail Information fit when copy asserts a mechanism the data can't establish.

Treat the change contract as authoritative. "Only change X", "remove Y", "keep the rest" are release conditions. A reviewer recommendation cannot retain, restore, or modify something in conflict with an active user check. When a later user correction conflicts with an older evaluator action, the user correction supersedes.

### 2. Inspect the delivered artifact

Open the exact export (PNG, JPEG, SVG, PDF, slide, screenshot, dashboard) at the size the audience actually sees - the thumbnail/compressed image for chat, the full slide at viewing distance for slides. The export is the source of truth; do not approve a browser viewport, plotting window, HTML source, or code path that differs from the delivered file. Distinguish a self-contained thumbnail requirement from a tap-to-expand chat image. Don't invent a fixed display width; if unknown, use a representative preview and report the assumption. Mark delivery `Fail` only when the tested artifact breaks or the failure is clear across plausible sizes; otherwise `Concern` or `Unknown`.

When deterministic render inspection is available, require its artifact hash to match this export and record it. Known metadata-backed failures are evidence and can't be overridden by a clean-looking overview; an incomplete report leaves uncovered geometry unknown and can't itself support a pass, so inspect that coverage visually and state the limitation. Deterministic checks supply mechanical evidence but never decide the analytical or communication verdict.

On the first pass, open the full export, delivery-size view, every panel, every hierarchy region, and each densest repeated-placement view. **Audit repeated structures completely, not by sampling the easiest instance**, and inspect neighbouring zones around each proposed correction (a title fix must not create a subtitle/panel-heading collision, a legend fix must not damage plot hierarchy, a label fix must not create a new mark/margin failure). Use the revision comparison to name introduced, persistent, and resolved defects. Start with the pre-build risks (longest text, densest region, legend/direct-label footprint, annotations, footer, margins, adjacent zones) but treat the plan as a hypothesis and discover any consequential problem it missed.

### 3. Run an expert blind read

Without using stated intent, record: the question the chart appears to answer; the main point it appears to make; how much effort the reading takes; whether title, form, metrics, encodings, labels, highlights, and notes agree; render failures (clipping, overlap, truncation, false precision, broken mappings). Focus on relationships the creator can miss; don't mechanically replay every chart-making rule.

Also freeze one structured reading and uncertainty statement per semantic dimension (measure, time/context, universe/denominator, claim strength, audience units), using `Unknown` where the artifact doesn't establish the answer. Copy these unchanged into the final report; post-reveal context can't rewrite the first interpretation.

### 4. Run an audience blind read

Adopt the audience's knowledge, time, and viewing conditions. Without using stated intent, record: what question the chart answers; the point remembered after a quick look; what stays uncertain or easy to misread; what action follows if any; how much work the reading takes.

For every creator-system release gate, use a fresh reviewer so the blind read is genuine - the chart creator cannot also issue `Send`. Give the reviewer the raw source and delivered artifact, not the creator's diagnosis, claimed fixes, intended verdict, or code.

### 5. Reveal intent and verify evidence

Compare both blind reads and the frozen semantic fields with intended question and insight. In the narrative comparison use `Match`/`Partial`/`Mismatch`/`Unknown`; encode them in the report as `Pass`/`Concern`/`Fail`/`Unknown`.

Then verify what appearance cannot establish: values, calculations, denominators, baselines, scales, transformations; units, time periods, sources, uncertainty, caveats; colour/label/legend mappings; whether removing an axis or legend also removed information the reader still needs.

**Literal element audit** (before passing Information fit or Delivery):

- every required category, time point, and group stays identifiable and aligned with the correct marks; repeated labels are fine when the structure requires them, but orphaned, duplicated, or misbound data are not
- every direct value matches its mark and source value
- the identification system fits density and geometry: direct labels legible and unambiguous, else axes/legends/grouping/small multiples
- each category/series has one primary identification route; duplicate scaffolding (a direct label plus the axis/legend giving the same identity) must justify its reading value
- each axis, tick set, gridline, baseline, and reference line performs a distinct reading task (estimation, alignment, interpolation, threshold, comparison of unlabelled marks); a scale/grid that merely repeats direct values is redundant, not neutral decoration
- every legend entry has plotted marks and its colour/form/channels match them exactly; no unused categories or generic swatches misstating geometry
- every encoded colour stays perceptually distinct from adjacent series and background under delivery conditions
- every requested removal is absent; every requested addition/relocation appears in the requested place

**Five release checks** (across chart types; invariants, not prescriptions - don't infer a preferred chart type, palette, pixel margin, highlight count, or density threshold from one example):

1. **Visual integrity** - text vs text, text vs marks, marks vs marks, panel boundaries, clipping, truncation, occlusion, export geometry. Test clearance, not only bounding-box intersection: touching, nearly-touching, or crowded elements fail when the gap no longer separates their roles at delivery size. Text over a mark isn't "clear" - classify as intentional inside-labelling or collision, then test contrast and padding. Check the worst example in every repeated placement pattern. Don't solve geometry by shrinking type.
2. **Relationship traceability** - each label, value, mark, legend entry, annotation, and reference line pairs with its target immediately at delivery size; the intended bond must be perceptually strongest against nearby competitors. Judge distance to the visible target, not a shared row, edge, or baseline; alignment alone doesn't bridge whitespace. Judge the complete identity-value-mark unit. If direct placement can't hold the relationship, an axis/legend/grouping/different structure is preferable.
3. **Spatial economy** - inspect whitespace by relationship: title-to-plot, labels-to-marks, between panels, plot-to-notes, outer margins. Whitespace must group, separate, or emphasise; blank area that splits related elements, weakens hierarchy, or wastes the surface fails. Dense but well-grouped layouts can pass.
4. **Encoding semantics** - state the role of every salient colour, size, shape, order, and highlight; each must encode data, structure, uncertainty, or a declared focal point. A visually dominant encoding with no recoverable role fails the relevant gate.
5. **Delivery robustness** - inspect the exact export at the intended viewing condition, including representative downscaling/compression. A full-size file can't pass on behalf of an unreadable delivered version.

For every release check, record a `stress_test` naming the tightest/most crowded element, pair, or region inspected and why it survives or fails - a generic "no overlap" can't support `Pass`.

For a narrow repair, apply the checks in two zones:

- **Changed/targeted regions:** full absolute standard above.
- **Untouched regions:** verify preservation and no regression against source or latest accepted candidate. Record unchanged pre-existing defects outside scope in `baseline_concerns`; don't convert them into required actions or block `Send` unless they prevent the correction from working or leave the artifact materially misleading. This is not permission to hide a new failure as "pre-existing" - any regression the repair introduces is a release failure.

**Completeness across repeated structures:** when a removed shared legend or global key served several panels, inspect every panel using the mapping and count required replacement labels in each. One correctly labelled panel can't pass for an unlabelled sibling unless the replacement is intentionally shared and each panel stays immediately interpretable.

**Carry-forward:** carry every unresolved required action into the next revealed packet, reinspect each named target, and record a result with direct evidence. Only an explicit `Pass` closes it - not an improved overall gate, not a new reviewer's silence. Drop an evaluator action only when the user explicitly supersedes it; if an old action and a new acceptance check conflict, follow the user check and mark the old one superseded.

**Stacked bars:** identify what the reader must compare. Only segments on an aligned baseline compare precisely; a 100% stack aligns both outer edges while internal segments float. Direct segment labels support lookup but not across-bar pattern comparison. If the claim needs precise component values or trends, choose a form with aligned baselines. If component values are only visually estimated, don't reconstruct heights: show the defensible total, mark a clear approximation, or switch forms.

**Colour audit** (whenever colour carries meaning; palette-choice workflow: `dataviz-color`):

- state colour's role (identity, order, direction, emphasis); purposeless colour is a concern
- scale type fits the data; the same meaning keeps the same colour across panels; focal colour/saturation/warmth match the hierarchy rather than an accidental highlight
- practical contrast targets: normal text ≈4.5:1, large text ≈3:1, small/thin essential marks ≈3:1 - not substitutes for visual judgment
- adjacent regions differ clearly; key distinctions survive grayscale and chat compression; hue isn't the only channel
- trace each mapping end to end: data condition → mark/connector → direct label/annotation → legend; all appearances of one meaning agree, every legend meaning appears in the chart
- for signed/directional change, every encoding derives from the same stated direction; sign, position, wording, or shape preserves meaning without colour alone

Fail the relevant gate for legend-to-mark mismatch, essential marks disappearing into the background, colour-only distinctions failing under common CVD, or series collapsing at delivery size. Don't require every large decorative fill to meet text-level WCAG when labels, boundaries, and other channels make the reading robust.

### Presentation checks (mandatory)

Record these separately from the outcome gates and release checks. Each needs `Pass`/`Concern`/`Fail`/`Unknown`, direct evidence, and a `stress_test`; `Send` requires both to pass.

1. **Colour distinction** - identify the closest pair of competing encoded colours and test at delivery size, in grayscale, and under common CVD. A palette name or "colours are consistent" can't support `Pass`. If there are no competing encoded colours, state that as the evidence.
2. **Copy style** - after the blind read is frozen and intent revealed, load the applicable installed writing or brand style skill and inspect every title, subtitle, annotation, caption, and note against it; if none applies, require plain, specific, evidence-bounded copy. Accuracy alone can't pass when language is generic, inflated, or off-voice. Keep style skills out of the pre-intent blind read.

For a repair, require preservation of context present in the source; don't demand a new organisation, period, source, or denominator the original also omitted unless the brief requires factual defensibility or the omission makes the claim unsafe. Don't punish an exploratory chart for lacking a dramatic story; if the intended result is "no defensible pattern", evaluate whether the reader understands that.

### 6. Apply gates, not an average

Rate each gate `Pass`/`Concern`/`Fail`/`Unknown` and mark whether the declared scope requires it:

1. **Evidence** - correct, complete enough, not misleading.
2. **Question** - the intended analytical question is recoverable.
3. **Insight** - the intended point, caveat, or null is recoverable.
4. **Visual reasoning** - form and encodings support the comparison rather than fighting it.
5. **Information fit** - title, labels, units, source, time, legend-to-mark mappings, and annotations agree; active correction checks pass.
6. **Delivery** - the exact media file works in its medium without clipping, overlap, illegibility, broken geometry, or missing attachment.

For a rendered artifact, Evidence, Visual reasoning, Information fit, and Delivery are always required; a reviewer cannot opt out of those four. Question and Insight may be non-required only when the task genuinely supplies no intended outcome - leave them `Unknown` and state what's missing. Accessibility or an explicit target style becomes a gate when it changes comprehension, excludes part of the audience, or is in the brief; taste alone is not fatal.

Never average away a fatal error - a beautiful chart with wrong evidence, the wrong question, or unreadable delivery does not pass. Record evidence for every gate, release check, and presentation check. `Send` requires every fatal/major critique finding, active user check, semantic check, mechanical check, carried evaluator action, required gate, release check, and presentation check to pass; a non-required gate stays `Unknown` with the missing intent named. A generic "clean and readable" is not evidence: name the inspected relationship, encoding role, phrase, delivery condition, and artifact-bound view.

### 7. Set the verdict

- **Send** - all scope-required gates pass; only optional polish remains.
- **Revise** - the analytical design works but bounded changes are required. Return the complete minimum pass set; the creator applies all of it to the latest candidate.
- **Redesign** - the question, evidence-to-claim relationship, or form blocks the comparison. Say whether form is implicated so `dataviz-critique` and, when needed, `dataviz-selector` rerun before rebuilding from underlying evidence.
- **Not evaluable** - the artifact can't be inspected, or a required decision depends on unavailable evidence/context.

When some checks are possible, report them before `Not evaluable`. Never translate `Unknown` into `Pass`.

### 8. Return the minimum pass set

Rank only consequential issues; prefer a short set that gets the artifact over the pass line. Every required action stays inside the authorized scope and must not conflict with an active acceptance check. The actions together must be the complete minimum pass set - don't defer a related neighbouring-zone failure to the next evaluation. Out-of-scope observations go in `baseline_concerns`. If the change can't pass without a dependent out-of-scope adjustment, name that dependency; don't silently broaden the redesign.

Write every required change as an operation:

```text
Target: <element>
From: <current state>
To: <required state>
Why: <reader consequence>
Codes: <failure codes>
Affected zones: <title/subtitle/legend/plot/annotation/footer/panels>
```

Fix geometry before shrinking type. Preserve title, subtitle, source, units, time, and mappings when changing forms. Direct labels are useful only when they stay visible, unambiguous, and complete.

## Creator-system benchmark

Do not call a handful of attractive outputs an evaluation.

1. Freeze the creator version, input contract, renderer, and delivery conditions.
2. Build a representative case set across analytical tasks, densities, audiences, media, and null/no-story cases.
3. Have reviewers label cases independently with the artifact-gate protocol.
4. Adjudicate disagreements and freeze a golden set with acceptable outcomes, not one canonical layout.
5. Compare versions using all-gates pass rate, failure modes by slice, regressions, cost, and latency.

Use open coding for novel failures, then consolidate repeats into stable codes. Change a creator skill only when evidence points to a reusable rule, missing tool, or ambiguous instruction; keep one-off chart preferences in the case record.

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

## Presentation checks
| Check | Result | Evidence | Stress test |
|---|---|---|---|
| Colour distinction | Pass / Concern / Fail / Unknown | ... | ... |
| Copy style | Pass / Concern / Fail / Unknown | ... | ... |

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
- Match aspect ratio to comparison density, label geometry, and medium rather than inheriting the source or renderer canvas.
- Prefer forms that expose the comparison directly and labels that reduce lookup effort.
- Do not remove legends, axes, sources, units, time periods, or context unless the replacement carries the same information or the user explicitly requests it - and the request must still leave the chart interpretable within scope.
- Treat low contrast and redundant encodings as comprehension costs, not merely aesthetic defects.
- Evaluate subtitle copy by what it tells the reader, not whether it describes the chart-making process.

## Stop conditions

Stop when the artifact crosses the stated pass line; don't keep revising for preference after `Send`. Escalate to `dataviz-critique` when the failure is conceptual; hand the minimum pass set to `dataviz-fix` when changes are executable. Record repeated failure codes before proposing a skill change.

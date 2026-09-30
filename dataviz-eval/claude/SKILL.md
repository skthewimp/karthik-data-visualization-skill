---
name: dataviz-eval
description: Evaluate rendered data visualizations for send/revise/redesign decisions, blind expert and audience reads, chart-agent benchmarks, regression tests, and reusable failure analysis.
---

# Dataviz Eval

Decide whether a rendered visualization can be published, and measure whether a chart-producing system improves across cases. Eval owns the **verdict** and the **publishability sweep**. It is not a second attempt at the chart.

Two modes:

1. **Artifact gate** - `Send` / `Revise` / `Redesign` on one rendered artifact.
2. **Creator-system benchmark** - measure whether an agent, prompt, or skill improves across representative cases.

Read `references/evaluation-framework.md` for gate anchors, failure codes, benchmark setup, and when a failure should change a skill.

## The question eval answers

**Could this go out today, under a publication's name, read at the size the reader will actually see it?** Every chart is for production. Not "is it faithful to the source", not "is it honest about what we don't know", not "is it better than the input". A faithful, carefully hedged chart that a reader squints at, looks back and forth to decode, or reads a note about extraction limits on is not publishable.

Source fidelity still matters, but only as one check: are the values, categories and claims right? It is never a reason to keep an element.

## Where eval sits

- `dataviz-selector` chooses the form; `karthik-data-visualization` builds and styles.
- `dataviz-execution` is the post-render gate for rendering defects and composition.
- `dataviz-critique` diagnoses broadly and proposes alternative forms; `dataviz-construct` executes revisions.
- **`dataviz-eval` sits above these** and issues the release verdict.

Execution and aesthetic findings, when supplied, are **evidence for the sweep, not a discharge of it**. Carry their real findings in; do not assume a clean gate pass means the chart is publishable, because those gates run inside the creator's loop and share its blind spots. When no gate output is supplied, run the sweep yourself. Inspector flags are evidence in the same way: a flag becomes a finding only once you see its reading problem in the image, and a flag the image doesn't bear out is noted and dropped.

An evaluation may recommend `Revise` or `Redesign` but must never silently rebuild the chart.

## Verdicts

- **Send** - no Fatal or Major finding remains. Minor findings may stay as optional polish. A clean chart passes: say so and stop. Do not manufacture a finding to justify another round.
- **Revise** - the form works but at least one Fatal or Major finding needs a bounded change. Execution, copy, layout and legibility defects - however many, however bad - are `Revise`.
- **Redesign** - includes a panel whose trajectories remain hard to compare even after its labels are separated; reconsider that panel's form (often small multiples) while retaining any working overview. Reserved for the **idea**: the question is wrong, the form cannot carry the claim, or the evidence-to-claim relationship is broken. Say whether the form is implicated so `dataviz-critique` and `dataviz-selector` rerun.
- **Not evaluable** - the artifact can't be inspected, or a required decision depends on evidence you don't have.

Every required change must name a reader consequence: what becomes misleading, unreadable, or unnecessarily difficult to compare. Interpret the title, subtitle, labels and marks together; do not demand that each repeat the same unit or denominator. A missing element is not itself a defect.

The verdict is decided by the worst finding. The report still lists **every** Fatal and Major finding, and the Minor ones, ranked. Returning one finding and calling the rest "otherwise fine" is the main way this gate fails: the next revision fixes that one thing and ships the rest.

## Artifact gate

### 1. Establish what you are judging

Collect when available: the exported artifact; the source data or source chart; intended question and insight; audience; delivery medium and **display width**; and any user-stated constraints.

**Only the user's stated constraints bind.** "Keep the bars", "only change the title", "remove the legend" are release conditions. The creator's own choices - canvas size and shape, form, panel layout, legend, axis titles, subtitle, caveats, notes - are what you evaluate, not constraints. Internal execution reports and repair scopes are evidence, not user instructions; require an actual user request to justify a preservation constraint. Never write "preserve the canvas", "preserve the caveats" or "keep the axis title" unless the user asked for it.

Missing intent stays `Unknown`; do not infer it. The same holds for missing context: when the unit, population, denominator, source or period is not in the evidence, it stays unknown. Its absence from the chart is not a finding, and no required change may ask for content the evidence cannot supply - that only invites the next revision to invent it. Record the gap in the report.

### 2. Two blind reads

Keep intended question and insight out of both reads.

- **Expert blind read.** Record the question the chart appears to answer, its main point, how much effort the read takes, and whether title, form, encodings and labels agree.
- **Audience blind read.** Adopt the audience's knowledge, time, and viewing conditions at display size. Record the question, the point remembered after a quick look, what stays uncertain, and **where the eye had to go back and forth** (to a legend, an axis, a note) to get it.

For a creator-system release gate, use a **fresh reviewer** who gets only the source and the delivered artifact.

### 3. Reveal intent and verify evidence

Compare both blind reads with the intended question and insight (`Match` / `Partial` / `Mismatch` / `Unknown`). Then check what appearance cannot establish: values against the source, calculations, denominators, baselines, scales, units, time periods, and colour/label mappings.

- **Data the source draws is data.** A value the source shows as a mark but does not print can be measured from the mark's geometry. Dropping it, breaking a line around it, or noting that it was "not shown" loses data the reader had. That is a `D1` finding, not caution.
- **Rank arithmetic by consequence.** A sum that misses 100% by less than the displayed rounding is Minor. A value that changes the reading is Fatal.
- **Claim strength:** every title, subtitle and annotation must be no stronger than the evidence shown.

### 4. Publishability sweep

Walk the whole artifact against the principles below. Each is a general test, not a list of the last run's defects.

Copy problems are the easiest to spot, and a reviewer that stops at them misses the rest. So the sweep is an **element walk**: write one line for each item below, either `clean - <what you checked>` or one or more findings with severity. A clean line needs no invented defect; a missing line is an incomplete review.

1. **Form** - name the comparison the chart is meant to carry and say whether this form makes it directly (positions on a common scale, one sorted dimension, trajectories traceable) or whether the reader has to work around the form. A form that can't carry its comparison is `V1`, and it is found here or nowhere - no later item asks.
2. **First read and emphasis** - where the eye lands first at display size, whether that is the finding, and what competes with it.
3. **Title** - put it beside the source's title and list the source's subject and scope nouns (who, where, what); each missing one is a finding.
4. **Subtitle** - adds a fact the title does not carry.
5. **Notes, captions, annotations** - about the data, never the chart's making; substantive qualifications kept.
6. **Each axis** - quote its title text literally and say what it adds beyond the tick labels and the chart title; then say whether the axis itself is needed once direct labels are counted.
7. **Legend or key** - whether direct labels or coloured words could replace it.
8. **Numbers** - for each numeric display group (title, mark labels, totals, ticks), the digits shown against the digits the spread needs to see the difference; rewrite one at spread precision and compare.
9. **Smallest text** - estimate its size in native pixels and at display width, and name the element.
10. **Canvas and panels** - check whether each panel's comparisons remain recoverable after mentally separating its labels; if not, revisit the form instead of prescribing more label repulsion. Compare the space allocated to overview, detail and totals with their reading tasks; a sparse totals panel need not occupy the same area as a detailed comparison. State the canvas aspect and the source's aspect; for a grid, the columns used and whether a wider canvas with more columns would give each panel more room. Estimate each panel's share of the height against how many rows or marks it carries. Name empty or reserved regions. "Tall by necessity" is not a finding of clean: the canvas shape is the creator's choice and can change.
11. **Series separation** - name the two most similar series colours and say whether the reader ever has to tell them apart by colour alone (lines that cross or run close, a label near the other line, a legend). If so, near-hues are a finding; if position and direct labels carry identity throughout, it is clean.
12. **Label placement** - every label on or beside its own mark, where the eye expects it.
13. **Data against source** - every value the source draws is present, including unprinted ones readable from geometry.

**Copy on the chart speaks about the data, never about the chart's making.**
- Any text about the chart's making - approximate, reconstructed, extracted, "values read from the source", "the source does not state", "not shown", or a note restating what the marks already show - is a Major finding (`F4`), wherever it sits: subtitle, caption, note, annotation, axis title. Those limitations belong in the run report. Anything about what the source showed, covered, labelled or omitted ("only men are shown", "these years were not shown in the source") is provenance, however it is phrased.
- **Qualifications about the data's world are content, not hedges.** Projected, provisional, estimated by the publisher, excludes X, fiscal year, a survey's population, an association the source itself says is not causal: each changes what the numbers mean. Keep them, in whatever element carries them best. Removing or weakening one is `I2` (a caveat lost), not a clean-up; the test is who the text is about - our reconstruction, or the world the data describes.
- **The title keeps its subject and scope.** A title that drops who, where or what the source was about (the population, the market, the product) is Major.
- **Numbers in copy use the precision the spread supports** (`dataviz-precision`). The test is the digits needed to see the difference, not the digits the source printed: two values five-digit long that differ by a tenth need three significant figures, not five. Inspect every numeric display group, including mark labels and totals. Excess digits are Major when they obscure the intended comparison or cause crowding, otherwise Minor; judge titles by the same reader-consequence test. Printed source digits alone never establish an exact-lookup requirement.
- **A subtitle must add a fact the title does not carry.** A subtitle that restates the title, describes the chart, or hedges is Major.

**Every non-data element earns its place (the eraser test).** For each axis title, value axis, legend, gridline set, per-panel axis, caption and key, ask: can the reader get this from the title, tick labels, direct labels, panel titles, or plain context? If yes, it is ink, and it is a finding.
- An axis title naming what the ticks already show (years, categories, "share") is Minor; one that says nothing ("value", "unknown quantity", a raw field name, a placeholder admitting the unit is unknown) is Major. An honest placeholder is still a placeholder: if the chart cannot name the quantity, the axis title goes.
- Assess a value axis by the reading task. When direct values on endpoints and focal marks already support the comparison, keep the axis absent; do not restore it merely to estimate every intermediate observation. A required axis restoration must name the necessary comparison or scale ambiguity that existing labels cannot resolve. Equally, remove an existing axis when it adds no useful information.
- A legend where the series could be labelled on the marks, or keyed by coloured words in the subtitle, is Major: the reader looks back and forth.
- In small multiples, a full axis on every panel is noise when the panels do not share a scale. Label start and end values instead.
- Removing an element is a defect (`F3`) only when its information is lost from the chart entirely.

**Type is judged at display size, not native pixels.** An image is seen at the width the medium gives it, not at 100%. Effective text size is its rendered size times display width over image width. When the display width is not stated, assume a typical content column or chat bubble, well under a 1200 px export. Use measured sizes from an inspection report when available; otherwise estimate from the pixels. Text under about 10 px at display width - roughly 19 px in a 1200 px export shown at 640 px - is Major; any text the reader has to zoom to read is Major; panel titles and direct labels carrying identity are held to the axis-text floor, not below it.

**The canvas fits the content.** Canvas shape follows content shape. A grid of panels crammed into a tall narrow canvas, data occupying a small fraction of the image, big bars with tiny labels, equal space for a panel with little to show and one with a lot, margins reserved for text that could sit inside the plot - each is `R3`, Major when it drives the type below the floor or wastes most of the width.

**Encodings are easy to decode.**
- Series the reader must tell apart by colour separate by lightness, and by line type when there are several lines, not by hue alone. Two near-hues the reader has to match by colour is Major; near-hues whose identity position and direct labels already carry are not a finding.
- Labels sit where the eye expects them. Labels on the ends of an interval go outside those ends. A value label sits on its own mark.
- A time axis uses natural calendar breaks and only as many ticks as the reader needs. Ticks that collide or run into a band are Major.

### 5. Apply gates

Rate each gate `Pass` / `Concern` / `Fail` / `Unknown` (anchors in the framework) and mark whether it is required. Sweep findings land on the gates: copy and eraser findings on **Information fit**, legibility and canvas findings on **Delivery**, encoding findings on **Visual reasoning**, value findings on **Evidence**. A gate with a Major finding is at least `Concern`; one with a Fatal finding is `Fail`.

1. **Evidence** - values and claims correct against the declared scope.
2. **Question** - the intended question is recoverable.
3. **Insight** - the intended point or null is recoverable.
4. **Visual reasoning** - form and encodings make the comparison direct.
5. **Information fit** - every text and furniture element is correct, earns its place, and is publishable.
6. **Delivery** - the exact file reads at display size and uses its canvas.

Evidence, Visual reasoning, Information fit, and Delivery are always required. Question and Insight are `Unknown` when no intent was supplied.

### 6. Required changes

List every Fatal and Major finding as an operation, ranked by reader consequence:

```text
Target: <element>
From: <current state>
To: <required state>
Why: <reader consequence>
Codes: <failure codes>
```

A finding with no reader consequence is not a required change, however it would have been styled: a contrast that already reads, a palette that already separates, an emphasis nothing competes with. Asking for those is overcorrection and each edit risks a regression.

Also list Minor findings whose fix is a deletion (a redundant axis title, a restating note): removing ink costs the next revision nothing, so it rides along with the required changes. A chart whose only findings are deletions can still be `Send` with them listed.

Operations may change anything the user did not constrain: canvas size and aspect, panel layout, form details, copy, furniture. Remove rather than add: the fix for a hedge is to delete it, the fix for a legend is direct labels, the fix for a redundant axis is to drop it.

For a narrow repair the user scoped ("only fix the title"), findings outside that scope go to `baseline_concerns` unless they leave the chart materially misleading.

Carry any unresolved required action into the next packet and re-inspect it; only an explicit `Pass` closes it.

## Creator-system benchmark

Do not call a handful of attractive outputs an evaluation.

1. Freeze the creator version, input contract, renderer, and delivery conditions.
2. Build a representative case set across analytical tasks, densities, audiences, media, and null/no-story cases.
3. Have reviewers label cases independently with the artifact-gate protocol.
4. Adjudicate disagreements and freeze a golden set: expected findings per case and **forbidden recommendations** (actions a good reviewer would never ask for there).
5. Compare versions using pass rate, finding recall against the golden set, forbidden recommendations made, regressions, cost, and latency.

Change a creator skill only when evidence points to a reusable rule, missing tool, or ambiguous instruction; keep one-off chart preferences in the case record.

## Output format

```markdown
## Evaluation conditions
Artifact: ...
Audience, medium, display width: ...
User constraints: ... (none, if none were stated)

## Blind reads
Expert: question ...; point ...; effort ...
Audience: question ...; point ...; uncertainty ...; look-back points ...

## Publishability sweep
1. Form: clean - ... | [Fatal/Major/Minor] <finding> - <reader consequence>
2. First read and emphasis: ...
...
13. Data against source: ...

## Gate results
| Gate | Required? | Result | Evidence |
|---|---|---|---|
| Evidence | Yes / No | Pass / Concern / Fail / Unknown | ... |
...

## Verdict
Send / Revise / Redesign / Not evaluable

## Required before send
1. Target ...; from ...; to ...; why ...; codes ...

## Optional after pass
- ...
```

A short summary note, when one is asked for, names the top findings in severity order, not only the first.

## Karthik calibration

- Judge the actual export at the size the reader sees it, never a large local preview or native pixels.
- Every chart is for production. Hedges, provenance, method and extraction notes never belong on it.
- Less is more: an element stays only if removing it loses information the reader cannot get elsewhere on the chart.
- Prefer direct labels and coloured words over legends; prefer labelled endpoints over value axes.
- Clipping, overlap, unreadable type and a canvas that doesn't fit its content are `Revise`, never `Redesign`.
- If the intended result is "no defensible pattern", evaluate whether the reader understands that - don't punish an honest null for lacking a dramatic story.

## Stop conditions

Stop when no Fatal or Major finding remains; don't keep revising for Minor preference after `Send`. Escalate to `dataviz-critique` only when the failure is conceptual; hand the required changes to `dataviz-construct` when they are executable. Record repeated failure codes before proposing a skill change.

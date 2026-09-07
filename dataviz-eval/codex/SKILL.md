---
name: dataviz-eval
description: Evaluate rendered data visualizations for send/revise/redesign decisions, blind expert and audience reads, chart-agent benchmarks, regression tests, and reusable failure analysis.
---

# Dataviz Eval

Decide whether a rendered visualization can be sent, and measure whether a chart-producing system improves across cases. Eval owns the **verdict** and the **reader-outcome and evidence-honesty** judgement. It is not a second attempt at the chart, and not a re-run of the render-defect gates.

Two modes:

1. **Artifact gate** - `Send` / `Revise` / `Redesign` on one rendered artifact.
2. **Creator-system benchmark** - measure whether an agent, prompt, or skill improves across representative cases.

Read `references/evaluation-framework.md` for gate anchors, failure codes, benchmark setup, and when a failure should change a skill.

## Where eval sits

- `dataviz-selector` chooses the form; `karthik-data-visualization` builds and styles.
- `dataviz-execution` is the post-render gate for **rendering defects** - geometry, overlap, label-to-mark association, colour contrast, CVD/grayscale survival, precision as displayed, redundant ink.
- `dataviz-aesthetic` is the post-render gate for **composition** - first read, single emphasis, earned ink, whitespace.
- `dataviz-critique` diagnoses broadly and proposes alternative forms; `dataviz-fix` executes revisions.
- **`dataviz-eval` sits above these**: it decides `Send`/`Revise`/`Redesign` and judges whether the artifact answers the intended question with honest evidence for its audience and medium.

**Eval does not re-run the defect gates.** Execution already owns pixel defects; aesthetic already owns composition. When their verdicts are in hand, **consume them** - a clean execution pass plus a clean aesthetic pass *is* the render evidence; do not re-derive geometry, colour, precision, or composition findings the model will only half-reconstruct. When you are handed a bare artifact with no gate output, look for a render failure that would **block the reading**, and flag only what actually blocks it - do not rebuild execution's and aesthetic's full checklists and do not hunt for defects to fill a form.

An evaluation may recommend `Revise` or `Redesign` but must never silently rebuild the chart.

## The verdict is the point

Prefer the **lightest verdict the evidence supports**. A chart that reads and is honest gets `Send`, even when you can imagine a nicer one.

- **Send** - every scope-required gate passes; only optional polish remains. A clean chart passes: say so and stop. Do not manufacture a defect to justify another round.
- **Revise** - the analytical design works but a bounded, executable change is needed to clear a specific gate. Return the minimum set that crosses the line.
- **Redesign** - reserved for the **idea**: the intended question is wrong, the form cannot carry the claim, or the evidence-to-claim relationship is broken. A fixable execution defect (an overlap, a low-contrast series, a missing label, a bad aspect ratio) is **never** a `Redesign` - it is at most a `Revise`. When you do call `Redesign`, say whether the form is implicated so `dataviz-critique` and, if needed, `dataviz-selector` rerun before rebuilding.
- **Not evaluable** - the artifact can't be inspected, or a required decision depends on evidence you don't have.

Two disciplines keep this honest:

- **"Clean, nothing to flag" is a valid result.** Its evidence is the absence of a defect at the inspected relationship - you do not owe a finding per check. Generic praise ("looks great") is not evidence; a named relationship that survives inspection is.
- **Unknown and unavailable-evidence are footnotes, not blockers.** Never translate `Unknown` into `Fail`. Never withhold `Send` for a residual that does not mislead the reader. Reserve `Not evaluable` for a genuine inability to judge.

## Artifact gate

### 1. Establish what you are judging

Collect when available: the exported artifact (not code or an editor viewport); source data or source chart; intended question; intended insight (including an honest "no clear pattern"); audience and desired understanding/action; delivery medium and real display size; and, for a repair, the change contract - each requested addition, removal, relocation, and preservation constraint written as an observable before-to-after check. Missing fields stay `Unknown`; do not infer them, and an `inferred` question or purpose is not user intent.

Set evidence scope explicitly:

- **Data validation** when underlying data or calculations are available, or factual verification is requested.
- **Source fidelity** when repairing a supplied chart without its data: verify the repair preserved the source's values, categories, qualifications, and provenance, and state that upstream accuracy was not tested.

Missing underlying data is a hard boundary: never pass invented, reconstructed, or visually estimated values as factual evidence. If a redesign needs values not in the source, omit those encodings, label them approximate, or mark the artifact `Not evaluable`.

Treat the change contract as authoritative. "Only change X", "remove Y", "keep the rest" are release conditions; a reviewer recommendation cannot retain, restore, or modify something in conflict with an active user check, and a later user correction supersedes an older evaluator action.

### 2. Two blind reads

Keep intended question and insight out of both reads. If either is missing, don't invent it - mark the comparison `Unknown` later.

- **Expert blind read.** Without stated intent, record: the question the chart appears to answer; the main point it appears to make; how much effort the read takes; whether title, form, encodings, labels, and highlights agree; and any render failure that blocks the reading (clipping, overlap, truncation, false precision, broken mapping). Focus on relationships a creator can miss.
- **Audience blind read.** Adopt the audience's knowledge, time, and viewing conditions. Record: what question the chart answers; the point remembered after a quick look; what stays uncertain or easy to misread; what action follows, if any.

For a creator-system release gate, use a **fresh reviewer** for the blind read - the chart's creator cannot also issue `Send`. Give the reviewer only the raw source and the delivered artifact, not the creator's diagnosis, claimed fixes, intended verdict, or code.

### 3. Reveal intent and verify evidence

Compare both blind reads with the intended question and insight (`Match` / `Partial` / `Mismatch` / `Unknown`). Then verify what appearance cannot establish within the declared scope: values, calculations, denominators, baselines, scales, transformations; units, time periods, sources, caveats; colour/label/legend mappings; and whether removing an axis or legend also removed information the reader still needs.

Audit claim strength separately: every title, subtitle, annotation, and takeaway must be no stronger than the evidence shown. A plausible narrative is not evidence of causation or effect - downgrade Information fit when the copy asserts a mechanism the data can't support.

### 4. Semantic honesty

Test whether the visual semantics support the reader's likely interpretation, not only whether the numbers are legible. These are principles to challenge the chart with, **not a mandatory per-dimension checklist to fill**:

- **Measure:** mark, scale, wording, and units make clear whether the quantity is a level, count, rate, share, index, or change - the form must not invite a materially different reading.
- **Time and context:** claims about periods, transitions, or interventions have a supported, understandable boundary.
- **Universe and denominator:** what the categories include, exclude, and sum to is clear; a subset or selected decomposition doesn't masquerade as exhaustive.
- **Claim strength:** copy doesn't imply causation, comparison, or improvement without the baseline, comparator, and direction being established.
- **Audience meaning:** units and conventions are interpretable for this audience.

Record only the ambiguities that could actually flip the conclusion, each as: the misleading reading, the defensible reading, and the evidence needed to tell them apart.

### 5. Render soundness

If execution and aesthetic verdicts are supplied, **consume them**: a clean execution pass and a clean aesthetic pass discharge render defects and composition. Note them as the evidence and move on. A known metadata-backed failure from those gates is real and can't be waved off by a clean-looking overview.

If no gate output is supplied, inspect the exact export at the audience's real size for a render failure that would **block the reading** - clipping, off-canvas text, overlap that destroys a mapping, illegibility at delivery size, or an export that differs from what was inspected. Flag only blockers here; anything below that is optional polish, not a gate failure. Don't reconstruct execution's or aesthetic's full checklists.

### 6. Apply gates, not an average

Rate each gate `Pass` / `Concern` / `Fail` / `Unknown` (anchors in the framework) and mark whether the declared scope requires it:

1. **Evidence** - correct, complete enough, not misleading.
2. **Question** - the intended analytical question is recoverable.
3. **Insight** - the intended point, caveat, or null is recoverable.
4. **Visual reasoning** - form and encodings support the comparison rather than fighting it.
5. **Information fit** - title, labels, units, source, time, legend-to-mark mappings, and annotations agree; active correction checks pass.
6. **Delivery** - the exact media file works in its medium without a blocking render failure.

Evidence, Visual reasoning, Information fit, and Delivery are always required for a rendered artifact. Question and Insight are non-required only when the task genuinely supplies no intended outcome - leave them `Unknown` and name what's missing. Never average away a fatal error: wrong evidence, the wrong question, or unreadable delivery fails regardless of how the rest looks. But a `Concern` on a secondary element is not a `Fail`, and a required gate that passes needs only its named evidence - not a defect quota.

### 7. Return the minimum pass set

Rank only consequential issues; prefer the short set that gets the artifact over the pass line. Every action stays inside the authorized scope and cannot conflict with an active acceptance check. Write each required change as an operation:

```text
Target: <element>
From: <current state>
To: <required state>
Why: <reader consequence>
Codes: <failure codes>
```

For a repair, apply the full standard to the changed regions and check the untouched regions only for regression and preservation. Record unchanged pre-existing defects outside scope as `baseline_concerns`; don't convert them into required actions unless they block the change or leave the artifact materially misleading. Fix geometry before shrinking type; preserve title, subtitle, source, units, time, and mappings when changing forms.

Carry any unresolved required action into the next revealed packet and re-inspect it; only an explicit `Pass` closes it, and a later user correction supersedes an older evaluator action.

## Creator-system benchmark

Do not call a handful of attractive outputs an evaluation.

1. Freeze the creator version, input contract, renderer, and delivery conditions.
2. Build a representative case set across analytical tasks, densities, audiences, media, and null/no-story cases.
3. Have reviewers label cases independently with the artifact-gate protocol.
4. Adjudicate disagreements and freeze a golden set with acceptable outcomes, not one canonical layout.
5. Compare versions using all-required-gates pass rate, failure modes by slice, regressions, cost, and latency.

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

## Render soundness
Execution/aesthetic verdicts consumed, or blocking render failures found (or none).

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
- Treat clipping, overlap, missing necessary labels, off-canvas text, and unreadable delivery-size views as blockers - but as `Revise`, not `Redesign`.
- Prefer forms that expose the comparison directly and labels that reduce lookup effort.
- Do not remove legends, axes, sources, units, time periods, or context unless the replacement carries the same information or the user explicitly requests it.
- Evaluate subtitle copy by what it tells the reader, not whether it describes the chart-making process.
- If the intended result is "no defensible pattern", evaluate whether the reader understands that - don't punish an honest null for lacking a dramatic story.

## Stop conditions

Stop when the artifact crosses the stated pass line; don't keep revising for preference after `Send`. Escalate to `dataviz-critique` only when the failure is conceptual; hand the minimum pass set to `dataviz-fix` when the changes are executable. Record repeated failure codes before proposing a skill change.

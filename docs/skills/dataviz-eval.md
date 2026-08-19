# Dataviz Eval Skill

`dataviz-eval` is the repo's measurement layer. It answers two different questions:

1. Is this rendered visualization ready to send?
2. Is this chart-producing skill, prompt, model, or renderer getting better?

The old version was a useful final visual check, but it was too narrow. It mostly checked clipping, overlap, whitespace, and thumbnail legibility. Those things matter, but a perfectly rendered chart can still answer the wrong question, bury the intended insight, lose its source or units, or encode the data incorrectly.

The rebuilt skill evaluates the complete path from evidence and intent to what the audience actually understands.

## Why this skill is optional

`dataviz-eval` is a formal audit, not a routine step in chart repair. It adds a fresh reviewer, blind expert and audience reads, structured evidence checks, and strict release gates. Inside an audited workflow, those gates are allowed to block `Send` until the stated conditions pass.

That behaviour becomes a problem when evaluation is inserted into every `dataviz-fix` run. A normal repair can already build a valid artifact, inspect the exact export, and improve it from user feedback. Adding `dataviz-eval` by default introduces extra model calls and can turn concerns, unknowns, or optional context into repeated revision cycles. It can delay or suppress a useful output without improving the requested edit.

Use it when the user explicitly asks for independent evaluation, when a materially misleading claim may survive visual polish, for a consequential redesign, or when benchmarking a chart-producing system. Do not auto-load it for ordinary repairs. Even when it is used, its verdict informs the next revision; it does not withhold the strongest valid artifact from the user.

## Live artifact gate

The evaluator first inspects the actual deliverable at its real viewing size. A browser preview or plotting window is not enough. Telegram thumbnails, slide distance, exported dimensions, and PDF rendering can introduce failures that do not exist in the editor.

When renderer metadata exists, the evaluator also receives a deterministic inspection report tied to the same artifact hash. Known clipping or collision failures become evidence for the release checks and cannot be overridden by a clean-looking overview. Incomplete coverage remains unknown and must be assessed visually rather than converted into a deterministic pass. The report helps with mechanical failures but does not decide whether the chart asks the right question or communicates the right point.

It then gives the source and artifact to a fresh reviewer and saves two blind reads before revealing the intended message, audience, medium, or active corrections. The chart creator cannot issue its own `Send`; creator reasoning, claimed fixes, preferred verdict, and code are withheld throughout.

- **Expert read:** What question and point does the artifact appear to communicate? Do the title, metrics, form, labels, highlights, and notes agree? Are there evidence or rendering problems?
- **Audience read:** What would this audience notice, misunderstand, remember, or act on under the real viewing conditions?

Only after those reads does the evaluator reveal the intended question and insight, compare perceived with intended meaning, and verify the evidence. In a chart-repair case, that evidence check can be scoped to fidelity with the supplied source chart. It does not pretend that pixels prove the upstream data, but it also does not block a repair because the original dataset was never supplied.

## Six gates

Each gate is marked `Pass`, `Concern`, `Fail`, or `Unknown`:

- evidence
- question recovery
- insight recovery, including a valid no-story result
- visual reasoning
- information fit
- delivery

These are gates, not inputs to an average score. Evidence, visual reasoning, information fit, and delivery are always required for a rendered artifact. The report marks whether the declared scope also requires question and insight recovery; genuinely missing, non-required intent stays `Unknown` rather than being forced into a pass. Wrong evidence, the wrong question, or an unreadable export cannot be cancelled out by attractive typography. The evaluator records the tested display size instead of assuming one universal Telegram or slide width.

The report also records five general release checks: visual integrity, relationship traceability, spatial economy, encoding semantics, and delivery robustness. These ask whether elements collide or become visibly crowded, whether the chosen identification system fits the chart and each label's bond with its mark is perceptually stronger than competing relationships, whether whitespace supports hierarchy, whether salient encodings have a recoverable job, and whether the exact export survives delivery. Every check must name its most failure-prone element, pair, or region; a generic “no overlap” claim cannot support a pass. Text drawn over a mark is treated as inside-labelling and must retain enough contrast and padding. Direct labels, axes, legends, grouping, and small multiples are alternatives chosen from density and geometry; none is mandatory. Quantitative ticks and gridlines must still perform distinct estimation, alignment, interpolation, threshold, or comparison work rather than merely repeat exact value labels. Shared-row alignment alone does not bridge blank space. The checks do not prescribe a chart type, palette, fixed margin, or density threshold.

For a narrow repair, the reviewer treats the user's requested changes and preservation requirements as a change contract. Changed regions must pass the full standard. Untouched regions are compared with the source or latest accepted candidate for regressions. An unchanged pre-existing defect outside the authorized scope is recorded as a baseline concern, not turned into an unrelated required action, unless it blocks the requested correction or leaves the artifact materially misleading. Explicit user instructions outrank reviewer preferences, so an evaluator cannot keep or restore an element the user asked to remove.

## Verdicts

- **Send:** all required gates pass.
- **Revise:** the analytical design works, but bounded changes are still required.
- **Redesign:** the form blocks the comparison, or the intended question or insight does not land.
- **Not evaluable:** the artifact cannot be inspected, or a required decision depends on missing evidence or context.

Required revisions are written as operations: the target element, its current state, the required state, the reader consequence, and the relevant failure codes. The evaluator also states the minimum set needed to cross the pass line, so a repair loop does not continue indefinitely for preference-level polish.

After user feedback, the evaluator turns the correction into a literal acceptance check with a stable id. Every active, non-superseded check needs its own result and direct evidence; omitting one makes the report invalid, and any non-pass blocks `Send`. It verifies that requested removals are absent, requested additions are present in the right place, every expected category appears once in every applicable panel or repeated structure, and legend keys match the plotted colour and mark form. A general "looks clearer" inspection cannot clear these checks.

The same persistence now applies to the evaluator's own required actions. Each unresolved action is carried into the next revealed review and must be rechecked directly. It closes only with an explicit pass, so a later reviewer cannot silently erase a crowded label or other local defect by improving the overall gate.

The evaluator also checks whether a stacked form supports the intended comparison. A total label does not reveal the intermediate or top components. If the story depends on those values across bars, the chart needs segment labels or a different form.

Colour evaluation checks whether colour has a job, whether the scale fits the data, whether mappings remain stable end to end across marks, connectors, labels, annotations, and legends, whether saturation creates the intended hierarchy, whether adjacent colours stay distinct from one another and the background, and whether the chart still works in grayscale and after chat compression. Directional encodings must derive from one stated comparison direction; audience conventions determine hues, while sign, position, wording, or shape supplies a redundant channel. WCAG-style ratios guide text and small-mark contrast without forcing every large fill into a mechanical threshold.

The reviewer inspects the full artifact, a representative delivery-size preview, and overlapping deterministic detail regions when supplied. These are views of the same hashed export. A full-view pass cannot erase a local collision or semantic mismatch visible in a required detail view.

## Creator-system benchmark

The same protocol can evaluate the system that produces charts. A proper benchmark freezes the creator version and input contract, uses representative cases across analytical tasks and media, obtains independent labels, adjudicates disagreements, and stores a golden set.

The golden set defines acceptable reader outcomes and hard failures. It does not require one canonical chart design. Several solutions can pass if they preserve the evidence and make the intended question and insight easy to recover.

Useful benchmark outputs include:

- all-required-gates pass rate
- failures by gate, code, and case type
- paired improvements and regressions between versions
- reviewer agreement before adjudication
- cost and latency

A single average quality score is deliberately avoided because it hides fatal errors.

## Learning from repair sessions

The evaluation framework includes a compact failure taxonomy for intent, evidence, visual reasoning, information fit, rendering, accessibility, and explicit style constraints. Accepted repairs can be coded against it and traced to a likely owner: creator instruction, evaluator, renderer/tooling, missing input, or a one-off preference.

A skill should change only when several cases reveal a reusable missing rule, an ambiguous instruction, a tooling assumption, or a missing input. One chart preference stays in the case record.

The calibration examples come from Karthik's observed repair sessions. They include thumbnail illegibility, redundant colour encodings, redesigns that lost source and time context, and a slopegraph that worked in the viewport but repeatedly failed in the exported PNG.

## Where the framework came from

This version combines Karthik's chart principles and the observed repair history with ideas from Vikram Nayak's Fifth Elephant 2026 talk, *Measuring “good” when your agent's output is subjective*. The talk's most useful contribution was the separation between creator, expert reviewer, and audience reviewer, followed by explicit failure synthesis and benchmark design.

## Relationship to other skills

- `dataviz-selector` chooses the visual form.
- `karthik-data-visualization` creates and styles the chart.
- `dataviz-critique` diagnoses and proposes alternatives.
- `dataviz-eval` optionally measures the current artifact and sets a formal pass line.
- `dataviz-fix` performs the changes and records the iterative feedback.

# Dataviz evaluation framework

Use this reference for calibrated artifact reviews, creator-system benchmarks, failure coding, and decisions about changing a skill.

## Contents

1. [Evaluation model](#evaluation-model)
2. [Gate anchors](#gate-anchors)
3. [Failure codes](#failure-codes)
4. [Priority and synthesis](#priority-and-synthesis)
5. [Benchmark design](#benchmark-design)
6. [Learning from failures](#learning-from-failures)
7. [Calibration cases](#calibration-cases)

## Evaluation model

A chart is not good in the abstract. It is good for a particular question, evidence base, audience, situation, and form factor.

Evaluate the path from input to reader outcome:

```text
evidence + question + intended insight + audience + medium
                         ↓
              creator's visual choices
                         ↓
               delivered artifact
                         ↓
        perceived question, insight, effort, action
```

The creator controls chart selection, execution, and storytelling. The evaluator measures whether those choices produced the intended reader outcome.

Use two deliberately different blind reads:

- **Expert reviewer:** reconstruct meaning, inspect inter-element fit, and detect evidence or rendering failures the creator may miss.
- **Audience reviewer:** adopt the intended reader's knowledge and viewing conditions, then report what the artifact communicates without privileged context.

Reveal the intended question and insight only after both reads. The gap between perceived and intended meaning is the main communication signal.

### Required packet

For a consequential evaluation, collect:

| Field | Why it matters |
|---|---|
| Delivered artifact | The export, not the code or editor viewport, is what the reader sees. |
| Source data or source chart | Needed to verify values, transformations, and omissions. |
| Analytical question | Establishes what comparison the artifact should make easy. |
| Intended insight | Establishes the point, caveat, or null result the reader should recover. |
| Audience | Sets knowledge, vocabulary, likely misreads, and action needs. |
| Situation | Distinguishes exploration, explanation, decision support, teaching, and monitoring. |
| Medium and display width | Sets the size text is actually read at, plus compression, distance, and interaction constraints. |
| Change contract | Names each user-requested addition, removal, relocation, and preservation constraint as an observable release check. The creator's own choices are not part of it. |
| Creator version | Required for regression tests and skill attribution. |

Missing fields become `Unknown`; they are not silently inferred. Declare whether the evidence gate covers **data validation** or only **source fidelity**. In a repair workflow, the supplied source chart can establish whether values and categories were carried over correctly. That does not validate the upstream data, but the narrower gate can still pass. Source fidelity is about values and claims; it never obliges the repair to keep the source's furniture, notes, or form, and it never obliges the chart to disclose what the source did not say.

### Reviewer separation

The creator and release reviewer must have separate contexts. A creator who has just chosen the form, written the code, and described its own fixes is anchored to intent and cannot supply a genuine blind read. First give a fresh reviewer only the source and delivered artifact and save its blind reads. Then reveal the user request, audience, medium, and acceptance checks. Withhold creator reasoning, claimed fixes, preferred verdict, and code throughout. Record different creator and reviewer identities, artifact hash, tested size, observed evidence, verdict, and minimum pass set in a durable report.

`dataviz-execution` (rendering defects) and `dataviz-aesthetic` (composition) run inside the creator's loop. When their findings are supplied, carry them into the sweep as evidence. A known metadata-backed failure from those gates is real and can't be waved off by a clean-looking overview. A clean pass from them does not discharge the publishability sweep: they share the creator's context and have endorsed hedging captions and redundant furniture before.

Run the publishability sweep on the exact export at display size whether or not gate output is supplied. Record every finding the sweep principles support, with severity. Do not manufacture a finding to fill a form: a principle the chart satisfies needs no entry.

Evidence, Visual reasoning, Information fit, and Delivery are always required for a rendered artifact. Question and Insight can be non-required only when the task supplies no intended outcome to compare; they remain `Unknown`, not fake passes. `Send` requires no Fatal or Major finding to remain - it does not require a defect logged against every relationship. A required gate that passes needs only its named evidence; the absence of a defect at an inspected relationship is valid evidence.

Carry unresolved required actions forward between iterations. Treat every active, non-superseded user acceptance check the same way: one stable id, one explicit result, and direct evidence from the current artifact. Reveal them only after the next blind read, then require the reviewer to reinspect each named target. A prior action or user check closes only with an explicit `Pass`; silence or a better overall gate does not clear it. Do not carry forward a preference-level observation as though it were a blocker.

The change contract outranks reviewer preference. An explicit user “only change X”, “remove Y”, or “preserve the rest” instruction is a release condition. A required action cannot contradict it. Nothing the creator chose becomes a preservation constraint by having been chosen: canvas, aspect, form, legend, axis titles, subtitle and notes stay open to required actions. When later user feedback replaces an evaluator action, record that action as superseded instead of carrying two incompatible gates.

For narrow repairs the user scoped, evaluate changed or targeted regions against the full standard. Evaluate untouched regions for preservation and regression against the source or latest accepted candidate. Keep unchanged pre-existing defects outside the authorized scope as explicit baseline concerns; they do not become minimum-pass actions unless they block the requested change or leave the artifact materially misleading. New regressions always fail.

For every change that applies across repeated structures, derive the expected instance set from the source and change contract, then verify each applicable instance. Passing one instance cannot stand in for untested siblings.

## Gate anchors

Use `Pass`, `Concern`, `Fail`, or `Unknown`. These are anchored judgments, not numbers to average.

### Evidence

- **Pass:** within the declared evidence scope, values, calculations, denominators, scales, and transformations are correct and complete enough for the claim.
- **Concern:** a non-fatal value or precision error, or a value the source draws that the chart dropped without changing the reading.
- **Fail:** a value, denominator, scale, encoding, omission, or claim materially misleads the reader.

The presence of a caveat is never evidence of a Pass, and its absence is never a Concern. Disclosure of what the source lacks belongs in the run report.
- **Unknown:** the evidence required by the declared scope is unavailable.

### Question recovery

- **Pass:** a blind reader states substantially the intended analytical question.
- **Concern:** the broad topic is clear but the exact comparison or denominator takes work.
- **Fail:** the reader answers a different question or cannot identify the comparison.
- **Unknown:** no intended question was supplied.

### Insight recovery

- **Pass:** a blind reader recovers the intended point, caveat, or null result without narration.
- **Concern:** direction is visible but magnitude, exception, uncertainty, or practical meaning is blurred.
- **Fail:** the reader misses, reverses, or invents the intended point.
- **Unknown:** no intended insight was supplied and the task is not explicitly exploratory.

For exploration, an honest "no defensible pattern" is a valid intended outcome. Do not manufacture a stronger story to make the artifact score better.

### Visual reasoning

- **Pass:** chart form, scale, ordering, geometry, and visual channels make the intended comparison direct under the selection principles owned by `dataviz-selector`.
- **Concern:** the comparison is possible but requires avoidable lookup or decoding.
- **Fail:** the form or encoding obscures, distorts, or redirects the comparison.
- **Unknown:** the artifact is missing or too broken to inspect.

### Information fit

- **Pass:** every text and furniture element is correct, publishable, and earns its place: the title keeps its subject and scope, numbers carry the precision the spread supports, the subtitle adds a fact, and no axis title, legend, value axis, or note restates what the reader already has.
- **Concern:** a Major sweep finding - a hedge or provenance note, a legend where direct labels would read, a redundant value axis, an empty subtitle, a title that lost its scope - with the reading otherwise stable.
- **Fail:** elements conflict, a mapping is ambiguous, or information the reader needs is gone from the chart entirely.
- **Unknown:** required context or source material was not supplied.

### Delivery

- **Pass:** the delivered artifact is legible and intact at display width, and its canvas fits its content.
- **Concern:** reading is possible but crowded, imbalanced, or effortful; space is wasted on reserved margins or equal allocation to unequal panels.
- **Fail:** clipping, overlap, cropping, text that needs zooming at display width, a canvas shape that crushes its content, off-canvas labels, compression, or export mismatch blocks the reading.
- **Unknown:** the evaluator saw only code, a viewport, or an unavailable link rather than the deliverable, or no defensible display-size assumption can be made.

Judge type at display width, not native pixels: effective size is rendered size times display width over image width. Record the display width assumed. When it is not stated, assume a typical content column or chat bubble, well under a wide export's native width, and never 100% native size. A clean read at native size proves nothing about the reader's view.

### Accessibility and target style

- **Pass:** contrast, colour use, type, language, and explicit style constraints serve the audience. Colour has a declared role, the scale matches the data, mappings remain stable, and key distinctions survive delivery conditions without hue alone.
- **Concern:** a purposeless or over-saturated colour adds effort or creates an accidental highlight without changing the conclusion.
- **Fail:** colour, contrast, type, or an explicit brief prevents a material part of the audience from reading the chart; mappings conflict; essential colours merge with the background or each other; or a colour-only distinction fails.
- **Unknown:** audience or target profile is not known.

Do not treat personal taste as a hard gate. Aesthetic mismatch becomes consequential when it affects comprehension, accessibility, trust, or an explicit delivery brief.

Apply the colour and contrast principles owned by `karthik-data-visualization`. Record the tested viewing conditions, whether essential mappings agree end to end, and whether the reading survives without hue alone. Do not copy the creator skill's palette or threshold guidance into the evaluation rubric.

## Failure codes

Assign the smallest set of codes that explains the failure. Do not tag every minor symptom.

### Intent and outcome

| Code | Failure |
|---|---|
| `I1` | Intended question is not recoverable or a different question dominates. |
| `I2` | Intended insight, caveat, or null result is absent, weak, reversed, or overstated. |
| `I3` | Intended action or decision is unclear or unsupported. |

### Evidence and integrity

| Code | Failure |
|---|---|
| `D1` | Data, calculation, denominator, transformation, or plotted value is wrong or incomplete. |
| `D2` | A unit, time period, baseline, or denominator the reader needs is missing from the chart and not recoverable from context. |
| `D3` | Scale, precision, uncertainty, or omission materially misleads. |

### Visual reasoning

| Code | Failure |
|---|---|
| `V1` | Chart form does not fit the analytical comparison. |
| `V2` | Encodings are redundant, conflicting, inaccessible, insufficiently distinct, or impose avoidable decoding. |
| `V3` | Ordering, hierarchy, highlight, or annotation directs attention to the wrong thing. |

### Information fit

| Code | Failure |
|---|---|
| `F1` | Title, subtitle, takeaway, or annotation conflicts with the chart or describes process instead of meaning. |
| `F2` | Labels, legend, direct labels, or colour mappings are ambiguous, incomplete, or inconsistent. |
| `F3` | A redesign removed information the reader still needs and cannot recover anywhere else on the chart. |
| `F4` | Hedge, provenance, method, or extraction note on the chart; a subtitle or caption that adds no fact; redundant furniture (axis title, value axis, legend, per-panel axes) that restates what the reader already has. |

### Rendering and medium

| Code | Failure |
|---|---|
| `R1` | Clipping, cropping, overlap, truncation, or off-canvas content damages the artifact. |
| `R2` | Type, marks, or labels fail at the intended thumbnail, slide, print, or screen size. |
| `R3` | Aspect ratio, whitespace, margins, placement, or canvas geometry weakens the reading. |
| `R4` | Export or attached media differs materially from the inspected viewport, recorded artifact, or intended dimensions; or no media is attached. |

### Access and explicit style

| Code | Failure |
|---|---|
| `A1` | Contrast, colour dependence, type, or language excludes the intended audience; essential marks disappear into their background or fail under common colour-vision deficiencies. |
| `A2` | An explicit target style or delivery constraint is violated in a consequential way. |

When no code fits, record the observed failure in plain language. Promote it into the taxonomy only after it recurs and has a stable correction.

## Priority and synthesis

Prioritize by reader consequence:

1. False or misleading evidence
2. Wrong analytical question
3. Wrong, absent, or overstated insight
4. Unreadable at display size, or a canvas that crushes its content
5. Unpublishable copy: hedges, provenance, lost title scope, excess precision
6. Look-back effort: legends, redundant axes, labels away from their marks, indistinct series
7. Polish

Reviewer agreement strengthens confidence, but it does not override consequence. An expert-only integrity failure can be fatal even when an audience reviewer does not notice it.

Use effort as a tie-breaker. List every consequential finding, not only the top one: a reviewer that names one issue and calls the rest fine sends the chart round the loop once per issue.

Translate each diagnosis into a chart-spec operation:

```text
Target: canvas
From: 16:9 landscape with empty side margins
To: portrait canvas sized to the row count, with room outside both endpoints
Why: endpoint labels become legible at Telegram thumbnail size
Codes: R2, R3
```

State which operations are required to cross the pass line (every Fatal and Major finding, plus Minor deletions). Keep other improvements below that line in an optional section.

## Benchmark design

### Freeze the system under test

Record:

- creator skill, prompt, model, renderer, and version or hash
- input fields supplied to the creator
- allowed tools and retry budget
- output format and delivery conditions
- cost and latency ceiling

A changed model, prompt, renderer, or retry loop is a changed creator system.

### Build representative cases

Include different analytical jobs, not just different datasets:

- rank and grouped comparison
- time trend and regime change
- two-point change
- part-to-whole composition
- distribution and uncertainty
- relationship or correlation
- geography
- dense tables, dashboards, or small multiples
- null, ambiguous, and no-story results
- multiple delivery media and audience knowledge levels

Include ordinary cases, hard edge cases, and known historical failures. Do not fill the set only with charts that suit one house style.

### Create labels

1. Have at least two qualified reviewers label cases independently.
2. Compare verdict and high-impact failure codes.
3. Adjudicate disagreements using the anchors, not majority taste.
4. Rewrite anchors when reasonable reviewers repeatedly interpret them differently.
5. Freeze the adjudicated packet as the golden set.

The golden set should define acceptable reader outcomes and hard failures. It should not require one canonical layout. Several visual forms can pass if they preserve evidence and make the intended question and insight recoverable.

### Report results

Prefer:

- all-required-gates pass rate
- `Send / Revise / Redesign / Not evaluable` distribution
- gate failures and failure codes by case slice
- paired regressions and improvements against the previous version
- reviewer agreement before adjudication
- median and tail latency and cost

Avoid a single average quality score. If a scalar is externally required, first enforce a gate floor: any fatal failure caps the overall result below passing.

Use live evaluation when stakes justify immediate review and a human can intervene. Use offline evaluation for prompt, model, renderer, and skill changes where stable comparisons matter more than latency.

## Learning from failures

Do not edit a skill because one chart needed a preference-level tweak.

For every accepted repair, record:

- original artifact and final accepted artifact
- user feedback by iteration
- blind-read mismatch and failed gates
- failure codes
- the operation that fixed the issue
- suspected owner: creator instruction, evaluator, renderer/tooling, missing input, or one-off preference

Use open coding to capture new failure language. Periodically group repeated codes into broader causes. Change a skill when several cases show one of:

- a missing repeatable decision rule
- an ambiguous or conflicting instruction
- a renderer or inspection step the skill assumes but does not perform
- an input the creator needs but the contract does not request

After a change, rerun the golden set. A fix is not an improvement if it solves one case and introduces regressions elsewhere.

## Calibration cases

These cases come from Karthik's observed repair sessions. They are not templates; they establish what counts as consequential.

### Pie to horizontal bars: pass after one repair

The first bar-chart repair made the comparison easier, carried the source values over, and read at the intended size. The original had no underlying dataset, so the evidence gate covered source fidelity rather than upstream validation. This should not be kept in revision merely because a tighter crop or another palette could also improve it. Once no Major finding remains, stop.

### AI-prioritisation chart: repeated effort failures

Several outputs remained unreadable at chat size despite looking substantial at full size. Row labels and values were too small, colour mappings were confusing, and colour shading repeated the same quantity already shown by bar length. These are `R2`, `F2`, and `V2`, not vague "make it prettier" feedback.

### Annual growth chart: redesign lost information

Changing grouped bars to lines and direct labels improved the time comparison. Removing axes and the legend also removed the time period and other context that no remaining element carried. Deleting furniture the direct labels already covered was fine; losing information nothing else carried was not. The test is recoverability, not preservation: a deleted element is `F3` only when nothing else on the chart carries its information.

### Two-year debt chart: viewport success, export failure

A slopegraph was the right analytical form, but repeated wide canvases, off-canvas endpoint labels, collisions, and cropping failed in the delivered PNG. The repair required a tall canvas, labels outside both endpoints, wrapped text, and inspection of the actual export. These are stable `R1` to `R4` failures and justify a geometry-first export check in the creator workflow.

### Two-panel finance chart: false `Send` from a generic inspection

The first repair was marked `Send`, but FY20 appeared as a floating label inside the top plot rather than on the x-axis. A later colour edit changed the legend swatch without changing the corresponding stacked bars, while yellow segments sat against a white background. More fundamentally, the stacked bars labelled only their totals, so the disinvestment and dividend components named in the claim could not be compared precisely. The case then recorded HTML as the iteration while sending a browser screenshot, and only the first of four iterations received an evaluation. The overall chart looked plausible, but the form, colour, and named elements were wrong. This is why the gate must inspect exact delivered media, audit every expected label and legend mapping, test colour separation, ask whether stacked components are actually readable, and rerun after every revision.

### Canonical repair run: a reviewer defending the wrong things

An independent reviewer ran on eight repaired charts and found about one in six of the issues the maintainer later marked, while recommending the opposite of the maintainer on about ten. It praised extraction caveats as honest disclosure and asked for them to be kept, asked for a legend to be added back, kept an axis title that said nothing, froze the creator's canvas as a constraint while the canvas was the main defect, called text legible at native pixels that was unreadable at display width, and asked for a line to break around years the source drew but did not label. Each note named one issue and called the rest fine. The causes were in this rubric: fidelity framed as keeping the source's qualifications, a keep-by-default rule for legends and axes, a blockers-only render check, and the creator's choices treated as a change contract. The fixes are the publishability frame, the eraser test, display-width type, and user-only constraints.

## Provenance

This framework combines Karthik Shashidhar's chart principles and observed repair failures with ideas from Vikram Nayak's Fifth Elephant 2026 talk, *Measuring “good” when your agent's output is subjective*. The talk supplied the creator/expert/audience separation, blind-read method, failure-mode synthesis, and benchmark discipline. The wording and rubric here are adapted for this skill rather than copied from the slides.

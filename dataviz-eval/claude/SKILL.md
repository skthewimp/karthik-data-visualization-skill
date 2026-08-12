---
name: dataviz-eval
description: Evaluate rendered data visualizations for send/revise/redesign decisions, blind expert and audience reads, chart-agent benchmarks, regression tests, and reusable failure analysis.
---

# Dataviz Eval

Measure whether a rendered visualization achieves its intended reader outcome. Own the evaluation packet, blind-review protocol, release gates, verdict, minimum pass set, benchmark method, and failure taxonomy.

Do not choose or rebuild the chart. `dataviz-selector` owns form choice, `karthik-data-visualization` owns visual construction, `chart-annotations` owns on-chart callouts, `dataviz-critique` owns broad diagnosis and alternatives, and `dataviz-fix` owns revision state.

Read `references/evaluation-framework.md` for gate anchors, failure codes, benchmark design, calibration, and skill-learning criteria. That reference is authoritative for evaluation details; do not create chart-specific release rules in this file.

Use two modes:

1. **Artifact gate** - decide whether one exact export can be sent.
2. **Creator-system benchmark** - compare frozen creator versions across representative cases.

## Artifact gate

### 1. Establish the packet

Capture, when available:

- exact exported artifact;
- source data or source chart;
- intended question and insight, including a null result;
- audience, medium, and real display condition;
- active change contract, with each addition, removal, relocation, and preservation constraint rewritten as an observable check.

Declare the evidence scope:

- **Data validation:** verify underlying values and calculations when data is available or factual verification is requested.
- **Source fidelity:** verify preservation against a supplied source chart without claiming upstream data validation.

Missing intent or evidence becomes `Unknown`, not an inferred pass. The change contract outranks reviewer preference. Later user feedback supersedes conflicting earlier checks or evaluator actions without deleting their history.

### 2. Inspect the delivered artifact

Inspect the exact PNG, JPEG, SVG, PDF, slide, or dashboard the audience will receive. Test it at the intended size and compression. If that condition is unknown, use a representative preview, state the assumption, and reserve `Fail` for breakage that is clear across plausible conditions.

Treat the export as truth. Code, HTML, plotting windows, and larger local previews cannot pass for a different delivered artifact.

### 3. Preserve reviewer independence

Use a fresh reviewer for creator-system release gates. Give the reviewer the source and exact artifact first, withholding intended question, insight, creator reasoning, claimed fixes, preferred verdict, and rendering code.

Record an expert blind read and an audience blind read before revealing intent. The creator cannot issue `Send` for its own artifact.

### 4. Reveal intent and verify evidence

Compare both blind reads with the intended question and insight. Verify values, calculations, denominators, scales, transformations, units, time periods, sources, uncertainty, material caveats, and semantic mappings within the declared evidence scope.

Run a literal element audit:

- every required category, period, group, value, and provenance element is present and correctly bound;
- every requested removal is absent and every requested addition or relocation is present;
- every active check and carried evaluator action has a direct result from the current artifact;
- every applicable instance in a repeated structure is checked, not only the easiest instance.

Do not use one chart family, palette, layout, pixel threshold, or fixture as a universal standard. Apply the principles from the owning creator skills to the artifact, then record observable evidence rather than repeating those principles here.

### 5. Run the release checks

Record `Pass`, `Concern`, `Fail`, or `Unknown` plus a named stress test for each:

1. **Visual integrity:** elements remain intact, legible, and sufficiently separated at delivery size.
2. **Relationship traceability:** labels, values, marks, guides, and annotations pair with their intended targets without guesswork.
3. **Spatial economy:** geometry and whitespace support grouping, separation, and emphasis.
4. **Encoding semantics:** each salient visual channel has a recoverable role and mappings agree end to end.
5. **Delivery robustness:** the exact export survives the intended medium, size, distance, and compression.

Name the most failure-prone element, pair, or region inspected for every check. A generic statement such as “clean” or “no overlap” is not evidence.

For a narrow repair:

- judge changed or targeted regions against the absolute release standard;
- judge untouched regions for preservation and regression against the source or latest accepted candidate;
- keep unchanged out-of-scope defects as `baseline_concerns` unless they block the requested change or leave the artifact materially misleading;
- treat every new regression as a failure.

Inspect the full artifact, representative delivery preview, and deterministic detail views when supplied. No one view can overrule a failing required view.

### 6. Apply outcome gates

Rate each gate `Pass`, `Concern`, `Fail`, or `Unknown`, and mark whether scope makes it required:

1. **Evidence** - correct, complete enough, and not misleading.
2. **Question** - intended analytical question is recoverable.
3. **Insight** - intended point, caveat, or null result is recoverable.
4. **Visual reasoning** - form and encodings support the comparison.
5. **Information fit** - title, labels, units, source, time, mappings, annotations, and active checks agree.
6. **Delivery** - exact media works in its intended medium.

Evidence, Visual reasoning, Information fit, and Delivery are always required for a rendered artifact. Question and Insight may be non-required only when the task supplies no intended outcome; leave them `Unknown` and name what is missing.

Never average away a fatal error. `Send` requires every required outcome gate, every release check, every active user check, and every carried evaluator action to pass.

### 7. Set the verdict

- **Send** - all required checks pass; only optional polish remains.
- **Revise** - the analytical design works, but bounded changes are required.
- **Redesign** - the question, insight, or selected form does not work.
- **Not evaluable** - a required judgment depends on an unavailable artifact, condition, context, or evidence source.

Report the checks that were possible before using `Not evaluable`. Never translate `Unknown` into `Pass`.

### 8. Return the minimum pass set

Rank only consequential actions needed to cross the pass line. Keep them inside the authorized scope and compatible with active user checks. Put useful out-of-scope observations in `baseline_concerns`.

Write each required action as:

```text
Target: <element or relationship>
From: <observed state>
To: <required state>
Why: <reader consequence>
Codes: <failure codes>
```

Escalate conceptual failures to `dataviz-critique`. Hand executable actions to `dataviz-fix`.

## Creator-system benchmark

1. Freeze creator version, input contract, renderer, and delivery conditions.
2. Build a representative case set across tasks, chart structures, densities, audiences, media, and null outcomes.
3. Keep accepted examples and prior feedback hidden from creators; use them only for adjudication.
4. Have independent reviewers apply the artifact gate and freeze acceptable outcomes rather than one canonical layout.
5. Compare all-gates pass rate, failures by slice, regressions, reviewer agreement, cost, and latency.

Treat fixtures as regression evidence, not prose-rule sources. Promote a new rule only after it recurs across structurally different cases, survives a counterexample, and has one clear owning skill. Execution misses normally require enforcement or observability, not more prose.

## Output format

```markdown
## Evaluation conditions
- Artifact:
- Tested size/medium:
- Evidence scope:
- Missing context:

## Blind reads
- Expert:
- Audience:

## Outcome gates
| Gate | Required? | Result | Evidence |

## Release checks
| Check | Result | Stress test and evidence |

## Active-check results
| Check/action id | Result | Evidence |

## Verdict
Send / Revise / Redesign / Not evaluable

## Required before send
1. Target ...; from ...; to ...; why ...; codes ...

## Baseline concerns
- ...
```

Omit empty optional sections. Stop after `Send`; do not keep revising for preference.

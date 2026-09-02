---
name: dataviz-idea-critique
description: Pre-render gate that critiques a chart's idea - is the data right, the expression right, the insight right, and honest - before it is built.
---

# Dataviz Idea Critique

The **pre-render gate** of the construct process. It receives the *plan* - the facts, the
headline claim, the candidate annotations, and the selected form - and judges the **idea
before any chart is drawn**. An LLM can read a plan and the data and tell whether the chart
will work; it does not need the picture. Catching a wrong chart here is far cheaper than
rendering it, seeing it is wrong, and starting over.

## Not the same as dataviz-critique

`dataviz-critique` critiques a **rendered** chart (or recovers a brief from a source image) -
it is the standalone reviewer and the repair diagnose step, and it stays that. This skill is
different: it critiques a **design intent plus its data**, before a render exists, and its job
is to **route the plan back** to be fixed - not to hand a reader a redesign. Judge the plan,
not a picture.

## The four questions

Answer each against the evidence, and be specific about what fails and why.

- **Is the DATA right?** Do the facts actually support the headline claim? Check the
  denominator and universe, the grain, the comparison, the time window and baseline, selection
  effects, and whether the uncertainty is acknowledged. A claim resting on a proxy pretending
  to be the real measure, or on a bad denominator, fails here.
- **Is the EXPRESSION right?** Is the selected form the right vehicle for *this* claim, or will
  it mislead - hide the comparison the claim depends on, distort magnitudes, invite a wrong
  first read, or bury the message in a form no reader can follow (a deep stack for a per-series
  trajectory, a dual axis implying a correlation, a pie split too fine to compare)? A
  small-multiples grid is a specific failure to check by hand here: it claims its panels are
  commensurable, so if the panels carry different units (a length panel beside a currency panel
  beside a count), the form asserts a comparison that cannot be made - route back to `select`
  for a table or separate individually-titled charts. "The panels preserve the distinct units"
  is the rationalisation that gives this away, not a justification: distinct units are the
  reason not to face them into one grid.
- **Is the INSIGHT right?** Is the headline claim the key thing to say, and is it supported at
  the strength stated? Are the candidate annotations the right marks - each pointing at
  something a reader would miss - or are they clutter, or restatements of what the axis already
  shows?
- **Is it HONEST and COMPLETE?** Is anything key silently dropped (a breakdown the message
  needs, a caveat that changes the reading)? Does the claim's strength match the evidence, or
  is a weak signal dressed as a strong one?

## Verdict and routing

Return a verdict - `proceed`, `revise`, or `blocked` - with a short summary and, for each
issue, its severity (fatal / major / minor), a concrete fix, and where it **routes back**:

- `insight` - the claim or the evidence is wrong or missing (recompute the facts, pick a
  different headline, add the dropped breakdown).
- `select` - the claim is right but the form cannot carry it (choose a form that shows the
  comparison the claim depends on).
- `none` - a minor note the build stage can absorb without re-planning.

Resolve on the evidence what the evidence can resolve; do not defer everything to "see how it
renders" - that defeats the gate. Never return `blocked` for a missing **external** validation
(an exact denominator, an authoritative dataset, a methodology to verify against): that is
disclosed downstream as a footnote, not a reason to stop. Reserve `blocked` for a plan that
genuinely cannot be made honest and answerable from the evidence at hand.

## Handoff

Emit the verdict, the summary, the four judgements, and the ranked issues with their fixes and
routing. The exact fields are `dataviz_mcp/stage_contracts.py:IDEA_CRITIQUE_SCHEMA`; this skill
carries the reasoning, that module the shape.

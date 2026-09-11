---
name: dataviz-idea-critique
description: Pre-render gate that critiques a chart's idea - is the data right, the expression right, the insight right, and honest - before it is built.
---

# Dataviz Idea Critique

The **pre-render gate** of the construct process. It receives the *plan* - the facts, the headline claim, the candidate annotations, and the selected form - and judges the **idea before any chart is drawn**. An LLM can read a plan and the data and tell whether the chart will work; it doesn't need the picture, and catching a wrong chart here is far cheaper than rendering it and starting over.

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
  to be the real measure, or on a bad denominator, fails here. A part-to-whole gets one
  structural check, on both paths: a negative "share", or a quantity plainly a net / delta /
  difference (a waterfall, a year-on-year change) framed as a share of a total, is a category
  error visible in the framing alone - it fails here until the quantity is named correctly or the
  composition framing is dropped. Whether the parts actually constitute the whole (a missing
  slice, overlapping categories, a subset shown as exhaustive) is the universe/denominator
  question above, not a separate arithmetic test - do not chase an exact sum-to-total: correctly
  derived shares sum by construction, and parts read off an image are approximate.
- **Is the EXPRESSION right?** Is the selected form the right vehicle for *this* claim, or will
  it mislead - hide the comparison the claim depends on, distort magnitudes, invite a wrong
  first read, or bury the message in a form no reader can follow (a deep stack for a per-series
  trajectory, a dual axis implying a correlation, a pie split too fine to compare)? Shared
  value scales require commensurable quantities. Different-unit charts may align on time
  when each owns its title and labelled value scale. Apply the **Form constraints** section of
  `dataviz-selector` (read that section if it is not supplied). Judge both the permitted
  form and whether the plan makes the actual comparison readable. A **length encoding** (bar,
  column, filled area or arc) whose baseline is not the encoded quantity's zero is a **fatal**
  integrity failure here, however the plan justifies it: a baseline the plan calls *meaningful*,
  *natural*, *contextual*, or *the interesting range* is the tell, not a defense, and this check
  is never tradeable against preserving the source's "context". Route it to `select` to re-anchor
  the bars at zero, or - when the variation against a large common level is the story - to switch
  to a position form (dot, dumbbell, slope) whose scale may zoom. Respect explicit prompt
  requests and the valid comparison/uncertainty forms; route a major violation to `select`
  with `revise`.
- **Is the INSIGHT right?** Is the headline claim the key thing to say, and is it supported at
  the strength stated? Are the candidate annotations the right marks - each pointing at
  something a reader would miss - or are they clutter, or restatements of what the axis already
  shows?
- **Is it HONEST and COMPLETE?** Is anything key silently dropped (a breakdown the message
  needs, a caveat that changes the reading)? Does the claim's strength match the evidence, or
  is a weak signal dressed as a strong one?

## One pass, exhaustive - and reconcile on re-review

Run **all four questions to completion every pass** and surface **every** fatal and major
issue you can already see in one verdict. A defect visible on the plan in front of you is
raised now, not saved for a later round - drip-feeding objections (fixing the issues you
named, only to raise a fresh "major" that was equally visible the first time) is what turns
one revision into a loop that never converges. If the claim's key term is undefined or the
measure is unnamed, that is a first-pass issue, not a second-pass discovery. Rank by severity,
but list them together.

When a **prior critique of this same plan** is supplied (a re-review after a revise), do not
restart cold. Reconcile each earlier issue against the revised plan and classify it:
**fixed** (the change resolved it), **still-open** (the change did not, or introduced a new
way to fail the same point), or **regression** (the revision broke something the earlier plan
had right). Only genuinely new problems - ones the earlier plan did not exhibit - are raised
fresh; a "new major" that was present and unraised last round is a first-pass miss to own, not
a reason to keep the plan in revision. Return `proceed` when nothing fatal or major remains
open.

## Verdict and routing

Return a verdict - `proceed`, `revise`, or `blocked` - with a short summary and, for each
issue, its severity (fatal / major / minor), a concrete fix, and where it **routes back**:

- `insight` - the claim or the evidence is wrong or missing (recompute the facts, pick a
  different headline, add the dropped breakdown).
- `select` - the claim is right but the form cannot carry it (choose a form that shows the
  comparison the claim depends on).
- `none` - a minor note the build stage can absorb without re-planning.

Every fix must be **directly usable by the stage it routes to** - one it can apply without
re-litigating. Respect the constraints the plan already declares: if you propose replacement
copy, keep it inside the limit that stage enforces (a headline within its character cap, a
label within its width), and if a compliant literal will not fit, describe the change to make
rather than hand over an over-budget string the next stage must reinterpret - reinterpretation
is another round for you to object to. State the fix at the grain the receiving stage acts on.

Resolve on the evidence what the evidence can resolve; do not defer everything to "see how it
renders" - that defeats the gate. Never return `blocked` for a missing **external** validation
(an exact denominator, an authoritative dataset, a methodology to verify against): that is
disclosed downstream as a footnote, not a reason to stop. Reserve `blocked` for a plan that
genuinely cannot be made honest and answerable from the evidence at hand.

## Handoff

Emit the verdict, the summary, the four judgements, and the ranked issues with their fixes and
routing. The exact fields are `dataviz_mcp/stage_contracts.py:IDEA_CRITIQUE_SCHEMA`; this skill
carries the reasoning, that module the shape.

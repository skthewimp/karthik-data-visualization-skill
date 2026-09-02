---
name: karthik-evidence-builder
description: Compute the facts behind a chart and name the single headline claim plus candidate annotation claims - from the data, before any form is chosen.
---

# Karthik Evidence Builder

The **insight** stage of the construct process: given the evidence available for a chart,
compute the facts and decide **what the chart should say** - the one headline claim the title
will assert, and any candidate annotation claims worth marking. This runs **before a form is
chosen and before anything is rendered**, so the headline is derived from the data, not
improvised at build time.

Two entry shapes feed this stage:

- **Dataset-to-story.** A prepared dataset plus an analysis contract (the operational
  question, metric, numerator/denominator, grain, the comparison that gives the number
  meaning, falsifiers, caveats).
- **Chart repair.** A data table recovered from a source image plus its brief (key messages,
  audience, medium). Compute the claim **freshly from the recovered data** - do not inherit
  whatever headline the source chart asserted; the source may have said the wrong thing, or
  said it about the wrong number.

## Compute the facts

From the data, not from priors, compute the values that answer the question: the magnitudes,
the comparisons that make a magnitude mean something (versus a baseline, a prior period, a
peer, a whole), and the uncertainty around them. Every fact is a `claim + value`, with its
comparison and uncertainty where they exist. Do not chart, and do not reach past what the
data supports - a fact you cannot compute from the evidence is a caveat, not a fact.

State each `value` to the precision the evidence supports - the smallest difference that
actually matters, no more - and never fabricate precision to sound sharp ("up 23%", not
"up 23.4%", unless the tenth is real and meaningful). Numbers you state in the headline or a
candidate annotation are reproduced verbatim downstream; their precision is decided here,
not re-rounded at build.

## Name the headline claim

Pick the **single** claim the chart exists to assert - the one the title will make. It is the
headline when it:

- **answers the operational question** the chart was built for, not an adjacent one;
- **is supported by the computed facts** - the numbers carry it, at the strength stated;
- **survives the falsifiers** - the obvious "but is it really" checks (denominator, selection,
  time window, a confound) do not overturn it;
- **is the most decision-relevant thing true here** - of the supported claims, the one that
  most changes what a reader would think or do;
- **states its strength honestly** - a trend, a gap, a turning point, or an *honest null*.
  An exploratory or "no effect" result is a legitimate headline. Never inflate a weak signal
  into a strong claim to manufacture drama.

When more than one message genuinely must be carried (a whole-and-parts story, a total
alongside a mix-shift), name the primary headline and note the secondary message; leave the
decomposition into one or several charts to selection.

## Candidate annotation claims

List the marks worth considering - each a **claim tied to the datum, series, period, or region
that supports it**, with why it clears the bar. A mark earns its place only when it points at
something a reader would otherwise miss or misread and the data backs it.

**Start from an empty list.** The default is no candidates. Most charts carry their point in the
headline claim and the direct labels and need nothing marked. Add a candidate only when a
specific mark would change what the reader takes away; do not pad the list to look thorough, and
do not treat "5 candidates" or any count as a target. An empty list is a normal, correct output,
not a gap to fill.

**The operational test: an annotation adds value only when its content cannot be recovered from
the marks the reader already sees - their direct labels, the axes, and the title.** If removing
the annotation loses nothing the reader could not read straight off the chart, it is clutter,
not an annotation. Three benign patterns recur and never earn a mark on their own:

- restating a value a direct label or axis tick already prints (a callout '42%' beside a point
  already labelled 42%);
- naming a rank or extreme the geometry already shows (a 'highest' or 'peak' callout on the
  visibly tallest, already-labelled mark);
- restating a change the two labelled endpoints already display ('up 9 points' when both ends
  are labelled and the reader can subtract them).

Aggregate and difference are forms, not exemptions. Summing two labelled series, subtracting two
labelled endpoints, or averaging a handful of visible values is arithmetic the reader does at a
glance from numbers already on the chart; that it took a calculation does not save it. The test
is the *effort* of recovery, not whether a calculation exists - a one-step subtraction of two
printed numbers fails it. What *earns* a mark is what the reader genuinely cannot get by eye: a
share or rank across many *unlabelled* marks, a ratio or multiple that reframes the comparison
(not a subtraction of two visible values), a count over a long run - plus what is not on the
chart at all: a cause, a consequence, the meaning of a threshold crossed, context from outside
the chart, or attention directed to a feature that is easy to miss (a crossover, an inflection, a
quiet divergence). Each survivor must also carry the headline claim - a true but incidental
aggregate does not earn a mark. These categories are a filter, not a menu: clearing one does not
oblige a candidate, and if you find yourself constructing a ratio or rank mainly so the chart has
something to mark, emit none. The list is often short and, when the headline claim and direct
labels already deliver the point, correctly empty. You decide the *claim and its anchor*; the build stage words, ranks, and
places the mark.

## Honesty and boundaries

- Put anything the evidence cannot support in **caveats** - a missing denominator, an
  approximate recovered value, an unverifiable external comparison. Carry it forward; do not
  bury it and do not let it block.
- **Do not choose a chart form and do not render.** The form is the selection stage's job;
  the headline and annotation wording and placement are the build stage's. Here you decide the
  substance the idea gate will check.

## Handoff

Emit the facts, the `headline_claim`, the `candidate_annotations` (claim + anchor + why it
clears the bar; empty when none earn a mark), and the `caveats`. The exact fields are
`dataviz_mcp/stage_contracts.py:INSIGHT_SCHEMA`; this skill carries the reasoning, that module
the shape.

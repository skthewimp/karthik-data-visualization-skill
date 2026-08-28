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
something a reader would otherwise miss or misread and the data backs it; a mark that restates
the obvious, or that the axis already shows, is clutter. The list is often short and may be
empty. You decide the *claim and its anchor*; the build stage words, ranks, and places the
mark.

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

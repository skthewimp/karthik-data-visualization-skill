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

A candidate annotation is **a fact from outside the dataset that explains what the data shows**, tied to the datum, series, period, or region it explains: rainfall behind a spike when rainfall isn't a column, a regulation/tax/ban that shifts the level, an acquisition/election/war/strike at a trend break, a definition or collection-method change behind a jump. The chart can't draw these - that is why they earn a mark. (`chart-annotations` owns their wording and placement at build.)

**A quantity in the data is never a candidate** - the encoding already draws it. "Peak", "all-time high", "from X to Y", "+38%", "doubled", a rank, a crossover, an inflection, a gap between series - the reader sees the shape, so a callout restating it adds nothing. A single mark's value, where it matters, becomes a **direct label** at build (decided there); a change or comparison is neither annotation nor label - its claim belongs in the title, in words. Don't emit any of these as candidates.

**The bar is self-enforcing:** an annotation requires a fact you know from *outside* the chart (the brief, domain, source, data owner) - you can't get one by studying the data harder. So **the default is an empty list, and most charts stay empty.** If you can't name the outside event and where you know it from, there is nothing to mark. Never invent a cause to fill the slot; if you only suspect a link, leave it off or word it as coincidence in time ("coincides with..."), never established cause. You decide the *external fact and the datum it explains*; build words and places it.

## Honesty and boundaries

- Put anything the evidence cannot support in **caveats** - a missing denominator, an
  approximate recovered value, an unverifiable external comparison. Carry it forward; do not
  bury it and do not let it block.
- **Do not choose a chart form and do not render.** The form is the selection stage's job;
  the headline and annotation wording and placement are the build stage's. Here you decide the
  substance the idea gate will check.

## Handoff

Emit the facts, the `headline_claim`, the `candidate_annotations` (the external fact + the datum
it explains + where you know the fact from; empty, and usually empty, when no outside fact is at
hand), and the `caveats`. The exact fields are
`dataviz_mcp/stage_contracts.py:INSIGHT_SCHEMA`; this skill carries the reasoning, that module
the shape.

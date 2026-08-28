# Dataviz Idea Critique

The **pre-render gate** of the construct process. It receives the plan - the facts, the headline claim, the candidate annotations, and the selected form - and judges the idea **before any chart is drawn**. An LLM can read a plan and the data and tell whether the chart will work; it does not need the picture. Catching a wrong chart here is far cheaper than rendering it, seeing it is wrong, and starting over.

## Not the same as `dataviz-critique`

`dataviz-critique` critiques a **rendered** chart (or recovers a brief from a source image) - it is the standalone reviewer and the repair diagnose step, and it stays that. This skill critiques a **design intent plus its data**, before a render exists, and its job is to route the plan back to be fixed.

## The four questions

- **Is the DATA right?** Do the facts support the claim - denominator, universe, grain, comparison, time window, baseline, selection, uncertainty?
- **Is the EXPRESSION right?** Is the selected form the right vehicle, or will it mislead, hide the comparison, or bury the message?
- **Is the INSIGHT right?** Is the headline claim the key thing to say and supported at the stated strength, and are the candidate marks the right marks rather than clutter?
- **Is it HONEST and COMPLETE?** Is anything key silently dropped, and does the claim's strength match the evidence?

## Verdict and routing

Returns `proceed`, `revise`, or `blocked`, with each issue's severity, a concrete fix, and where it routes back: `insight` (wrong or missing claim or evidence), `select` (wrong form), or `none` (a minor note build can absorb). It resolves on the evidence rather than deferring to "see how it renders", and never blocks on a missing external validation. The exact fields are `dataviz_mcp/stage_contracts.py:IDEA_CRITIQUE_SCHEMA`.

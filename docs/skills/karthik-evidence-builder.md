# Karthik Evidence Builder

The **insight** stage of the construct process. Given the evidence available for a chart, it computes the facts and decides **what the chart should say** - the one headline claim the title will assert, and any candidate annotation claims worth marking. It runs before a form is chosen and before anything is rendered, so the headline is derived from the data, not improvised at build time. This fills what used to be a skill-less `facts` placeholder in the creation pipeline, and gives repair a fresh-insight step it never had.

## Two entry shapes

- **Dataset-to-story** - a prepared dataset plus an analysis contract.
- **Chart repair** - a data table recovered from a source image plus its brief. Compute the claim **freshly from the recovered data**; do not inherit whatever headline the source chart asserted.

## What it produces

- **Facts** - the values that answer the question, from the data not priors, each with its comparison and uncertainty where they exist.
- **The headline claim** - the single key insight the chart exists to assert: it answers the operational question, is supported by the facts at the strength stated, survives the falsifiers, is the most decision-relevant thing true here, and states its strength honestly (an honest null is a valid headline).
- **Candidate annotation claims** - marks worth considering, each a claim tied to the datum that supports it. Often short, sometimes empty. The operational test: a mark earns its place only when its content cannot be recovered from the marks the reader already sees - their direct labels, the axes, the title. Restating a labelled value, naming a rank the geometry already shows ("highest" on the visibly tallest labelled bar), or restating a change two labelled endpoints already display ("up 9 points") is clutter; what earns a mark is a comparison the reader would have to compute, a cause or consequence, a threshold's meaning, outside context, or attention to a feature easy to miss. The build stage (via `chart-annotations`) does the wording, ranking, and placement; here the claim and its anchor are decided so the idea gate can check them before anything is drawn.
- **Caveats** - anything the evidence cannot support, carried forward rather than buried.

It does not choose a form and does not render. The exact fields are `dataviz_mcp/stage_contracts.py:INSIGHT_SCHEMA`.

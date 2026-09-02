# Karthik Evidence Builder

The **insight** stage of the construct process. Given the evidence available for a chart, it computes the facts and decides **what the chart should say** - the one headline claim the title will assert, and any candidate annotation claims worth marking. It runs before a form is chosen and before anything is rendered, so the headline is derived from the data, not improvised at build time. This fills what used to be a skill-less `facts` placeholder in the creation pipeline, and gives repair a fresh-insight step it never had.

## Two entry shapes

- **Dataset-to-story** - a prepared dataset plus an analysis contract.
- **Chart repair** - a data table recovered from a source image plus its brief. Compute the claim **freshly from the recovered data**; do not inherit whatever headline the source chart asserted.

## What it produces

- **Facts** - the values that answer the question, from the data not priors, each with its comparison and uncertainty where they exist.
- **The headline claim** - the single key insight the chart exists to assert: it answers the operational question, is supported by the facts at the strength stated, survives the falsifiers, is the most decision-relevant thing true here, and states its strength honestly (an honest null is a valid headline).
- **Candidate annotation claims** - each a **fact from outside the dataset that explains what the data shows**: a rainy day behind a spike, a regulation or tax that shifts the level, an acquisition or election at a break in the trend, a change of definition behind a jump. The chart cannot draw these because they are not in the data - that is why they earn a mark. A quantity the chart already draws ("peak", "all-time high", "from X to Y", a rank, a trend, a crossover) is never an annotation; if a number matters it is a direct label at build. The bar is self-enforcing: an external fact cannot be got by studying the data harder, so the list is **usually empty**, and a cause must never be invented to fill it. The build stage (via `chart-annotations`) words and places them; here the external fact, the datum it explains, and its source are named so the idea gate can check them before anything is drawn.
- **Caveats** - anything the evidence cannot support, carried forward rather than buried.

It does not choose a form and does not render. The exact fields are `dataviz_mcp/stage_contracts.py:INSIGHT_SCHEMA`.

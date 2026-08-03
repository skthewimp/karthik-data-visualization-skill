# dataviz-orchestrator

Use this when the task starts with a dataset, a loose question, and an audience, and should end with an analysed, critiqued visual story rather than just a chart.

The skill coordinates the existing suite:

- `karthik-analysis-planner` for the analysis contract.
- `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation before charting.
- `r-analysis-rules` for R analysis style.
- `dataviz-selector` for chart choice.
- `karthik-data-visualization` for Karthik's chart aesthetic.
- `dataviz-critique` for rendered-output review and iteration.

Default output: code/notebook with visible cleaning rules, exported chart, compact facts table, one-sentence claim, and caveats.

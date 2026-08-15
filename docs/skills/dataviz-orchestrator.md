# dataviz-orchestrator

Use this when the task starts with a dataset, a loose question, and an audience, and should end with an analysed, critiqued visual story rather than just a chart.

The skill coordinates the existing suite:

- `karthik-analysis-planner` for the analysis contract.
- `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation before charting.
- `r-analysis-rules` for R analysis style.
- `dataviz-selector` for chart choice.
- `karthik-data-visualization` for Karthik's chart aesthetic.
- `dataviz-critique` for rendered-output review and iteration.

After rendering, the workflow uses deterministic artifact inspection when available, binds it to the export hash, and fixes concrete geometry defects before broader critique or release evaluation. Raster-only inspection does not prove that layout checks passed.

Default output: code/notebook with visible cleaning rules, exported chart, compact facts table, one-sentence claim, and caveats.

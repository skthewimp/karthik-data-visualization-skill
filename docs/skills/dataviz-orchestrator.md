# dataviz-orchestrator

Use this when the task starts with a dataset, a loose question, and an audience, and should end with an analysed, critiqued visual story rather than just a chart. For repairing an existing chart from an image, use `dataviz-fix` (the repair orchestrator) instead.

## Staged, not one context

It runs as a sequence of separate calls - **discover -> contract -> clean -> facts -> select -> build -> refine** - each carrying only the skills that stage needs plus a compact artifact handed forward. Per-stage scoping is what keeps a long pipeline from rotting a single context. The `facts` stage is a named placeholder until `karthik-evidence-builder` exists. The machine-readable contract - exact skill subset and JSON handoff schema per stage - is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE`.

The skill coordinates the existing suite:

- `karthik-analysis-planner` for the analysis contract.
- `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation before charting.
- `r-analysis-rules` for R analysis style.
- `dataviz-selector` for chart choice.
- `karthik-data-visualization` for Karthik's chart aesthetic.
- `dataviz-critique` for rendered-output review and iteration.

When deterministic rendering and inspection are available, the workflow creates the export through the metadata-producing renderer, binds inspection to that exact hash, and sends concrete geometry defects into evaluation and repair. It does not bypass metadata generation and substitute a raster-only check. Raster-only inspection does not prove that uncovered layout checks passed.

Default output: code/notebook with visible cleaning rules, exported chart, compact facts table, one-sentence claim, caveats, and matching render/inspection records when available.

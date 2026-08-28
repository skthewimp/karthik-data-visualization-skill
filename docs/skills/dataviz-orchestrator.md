# dataviz-orchestrator

Use this when the task starts with a dataset, a loose question, and an audience, and should end with an analysed, critiqued visual story rather than just a chart. For repairing an existing chart from an image, use `dataviz-fix` (the repair orchestrator) instead.

## Front half, then the shared construct tail

It runs as a sequence of separate calls. The orchestrator owns the **front half** -
**discover -> contract -> clean** - and then hands into the shared construct process
(`dataviz-construct`), whose tail is **insight -> select -> idea -> build -> execution**.
The full `STORY_PIPELINE` is therefore `discover -> contract -> clean -> insight -> select
-> idea -> build -> execution`, and its construct tail is the *same* stages repair runs.
Each stage carries only the skills it needs plus a compact artifact handed forward; per-stage
scoping is what keeps a long pipeline from rotting a single context. The old skill-less
`facts` placeholder is gone: the `insight` stage now loads `karthik-evidence-builder` and
names the headline claim from the data before a form is chosen. Handoffs are structured text
(markdown sections plus, at the branch points, a small `routing` block of `key: value`
lines), not strict JSON, so the pipeline runs on cheaper / open-weight models too; the
routing parser (`dataviz_mcp.handoff`) also accepts a JSON object. The content contract -
exact skill subset and required fields per stage - is
`dataviz_mcp/stage_contracts.py:STORY_PIPELINE`.

The skill coordinates the existing suite:

- `karthik-analysis-planner` for the analysis contract.
- `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation before charting.
- `karthik-evidence-builder` for the facts and the headline claim (the insight stage).
- `dataviz-selector` for chart choice.
- `dataviz-idea-critique` for the pre-render idea gate.
- `karthik-data-visualization` for Karthik's chart aesthetic.
- `dataviz-execution` for the post-render execution gate.

When deterministic rendering and inspection are available, the workflow creates the export through the metadata-producing renderer, binds inspection to that exact hash, and sends concrete geometry defects into evaluation and repair. It does not bypass metadata generation and substitute a raster-only check. Raster-only inspection does not prove that uncovered layout checks passed.

Default output: code/notebook with visible cleaning rules, exported chart, compact facts table, one-sentence claim, caveats, and matching render/inspection records when available.

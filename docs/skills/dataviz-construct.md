# Dataviz Construct

The shared terminal process both chart creation and chart repair hand into. Each has its own front half - creation discovers a story, contracts it, and cleans the data (`dataviz-orchestrator`); repair diagnoses a source image and extracts its data (`dataviz-fix`) - and once the front half has figured out *what to say and from what data*, both hand into this one process to turn it into a finished chart.

```text
insight -> select -> idea -> build -> execution
```

- **Creation** hands in after `clean`; **repair** hands in after `diagnose+extract`.
- A repair **`bounded-edit`** (a literal change that keeps the source form) skips `insight -> select -> idea` and goes straight to `build -> execution`.

## The stages

1. **Insight** (`karthik-evidence-builder`) - compute the facts and name the **headline claim** plus candidate annotation claims, from the data, before a form is chosen.
2. **Select** (`dataviz-selector`) - choose the simplest form that makes the claim easiest to see and hardest to misread. For a repair, choose it cold; the source form gets no vote.
3. **Idea-critique** (`dataviz-idea-critique`) - the pre-render gate: is the data right, the expression right, the insight right, and honest? Route back to insight or select until it holds.
4. **Build** (`karthik-data-visualization` or `karthik-table-style`, plus `chart-annotations` / `chart-explainer` / `dataviz-color` / `dataviz-precision` when asked) - assert the headline claim in the title, place the annotation claims insight named, and render one real artifact.
5. **Execution-critique** (`dataviz-execution`, plus a blind `dataviz-eval` for an audit) - the post-render gate: geometry, overlap, labels, colour, precision, ink.

## Two gates, in order

The idea gate runs **before** the chart is drawn; the execution gate runs **after**. There is no sense fixing label overlaps on a chart that is the wrong chart. Ideas can be judged from the plan and the data - an LLM does not need the render to know the form cannot carry the claim - so that check comes first; execution can only be judged from pixels, so it comes second. Substance before craft.

## The loop is a unit; the driver owns the count

Each gate runs the same shape: find everything wrong, decide the fixes, redo, re-check. Whether that runs zero, one, or several times is the **driver's / harness's budget** - never a fixed pass count baked into the skill or a stage. A valid rendered candidate must be delivered; an unavailable optional evaluator or a check left `unknown` for want of external ground truth is disclosed, not blocking.

The content contract - the exact skill subset and required fields per stage - is the construct tail in `dataviz_mcp/stage_contracts.py`, shared by `REPAIR_PIPELINE` and `STORY_PIPELINE`.

# Dataviz Construct

The shared terminal process both chart creation and chart repair hand into. Each has its own front half - creation discovers a story, contracts it, and cleans the data (`dataviz-orchestrator`); repair diagnoses a source image and extracts its data (`dataviz-fix`) - and once the front half has figured out *what to say and from what data*, both hand into this one process to turn it into a finished chart.

```text
insight -> select -> idea -> build -> execution
                                \-> explain   (off the finding, when the exhibit ships with prose)
```

- **Creation** hands in after `clean`; **repair** hands in after `diagnose+extract`.
- A repair **`bounded-edit`** (a literal change that keeps the source form) skips `insight -> select -> idea` and goes straight to `build -> execution`.
- **`explain`** is off the render path: it writes the accompanying note from the finding and the plan, needs no chart, and runs in parallel with build/execution when the plan ships with prose.

## The stages

1. **Insight** (`karthik-evidence-builder`) - compute the facts and name the **headline claim** plus candidate annotation claims, from the data, before a form is chosen.
2. **Select** (`dataviz-selector`) - choose the simplest form that makes the claim easiest to see and hardest to misread. For a repair, choose it cold; the source form gets no vote.
3. **Idea-critique** (`dataviz-idea-critique`) - the pre-render gate: is the data right, the expression right, the insight right, and honest? Route back to insight or select until it holds.
4. **Build** - one builder skill by `select.builder`: `karthik-data-visualization` (chart) or `karthik-table-style` (table), never both. A chart may also load `chart-annotations` (on-chart marks - chart-only, never a table); that is the only conditional skill build carries. Assert the headline claim in the title, place the annotation claims insight named, and render one real artifact. Colour, precision, and the explainer note load no skill here - colour and precision are decided at select and resolved by a tool (see below), the note is written off the render path by the explain stage.
5. **Execution-critique** (`dataviz-execution`) - the post-render gate: geometry, overlap, labels, colour, precision, ink.
6. **Explain** (`chart-explainer`, only when `select.needs_explainer`) - the short note beside the exhibit, written from the finding and the plan, not the render; runs in parallel with build/execution, never in the build call.

## Two gates, in order

The idea gate runs **before** the chart is drawn; the execution gate runs **after**. There is no sense fixing label overlaps on a chart that is the wrong chart. Ideas can be judged from the plan and the data - an LLM does not need the render to know the form cannot carry the claim - so that check comes first; execution can only be judged from pixels, so it comes second. Substance before craft.

## Colour and precision are decided at select, resolved by a tool, only applied at build

Neither is a build judgment, so the two heaviest skill bodies (`dataviz-color`, `dataviz-precision`) never enter the build call. **Decision** at `select`: precision is one `exact_lookup_required` flag per display group (claim-text numbers get their precision at `insight`, where the value is computed); colour is a compact `colour_plan` (available source, focal series, semantic meaning) - decided as fields, not by loading the colour skill there. **Resolution** by a deterministic tool: `recommend_precision` (values + flag → format) and `recommend_colours` (colour_plan → ordered palette, checked by `validate_palette`), run by the driver between select and build. `needs_precision_plan` / `needs_color_plan` are the triggers, not skill-load signals. **Application** at build: apply the resolved format to axes/labels/cells (reproducing claim-text numbers verbatim) and assign the resolved palette in order; re-decide neither. In a table the same resolved per-column format is what `karthik-table-style` aligns to, and `dataviz-execution` re-checks colour contrast + CVD/grayscale on the render as the post-build net.

## The plan carries across the gate

The tail is not a straight pipe. `insight` names the headline claim and candidate annotations; the `idea` gate emits a critique, not a plan, so `build` cannot read the stage right before it for what to draw. The insight artifact is the plan that must persist **across** the gate - `idea` and `build` both receive the insight artifact *and* the select artifact. On a mechanical / weak-model harness feed both forward explicitly (`Stage.also_reads=("insight",)` on `idea` and `build` in `dataviz_mcp/stage_contracts.py`); rely on nothing remembering the claim from two stages back. If only the select artifact reaches build, the headline claim vanishes at the gate and the title is improvised again - the exact failure the insight stage exists to prevent.

## The loop is a unit; the driver owns the count

Each gate runs the same shape: find everything wrong, decide the fixes, redo, re-check. Whether that runs zero, one, or several times is the **driver's / harness's budget** - never a fixed pass count baked into the skill or a stage. A valid rendered candidate must be delivered; an unavailable optional evaluator or a check left `unknown` for want of external ground truth is disclosed, not blocking.

The content contract - the exact skill subset and required fields per stage - is the construct tail in `dataviz_mcp/stage_contracts.py`, shared by `REPAIR_PIPELINE` and `STORY_PIPELINE`.

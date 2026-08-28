# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

**Repair is forward design, not critique-plus-patch.** The flow does not start by critiquing the source chart - that anchored everything on the existing image and made "re-render the same form, tidied" the path of least resistance. Instead it extracts the intent and the data first, then the shared construct process computes the insight, selects a form cold from it, builds, and only then checks. Critique of the source is a diagnosis step, not the whole flow.

Two anchors govern the flow. A valid rendered candidate must always be delivered. And the repair may redesign freely against the input image - the source form gets no vote - while staying faithful to the prompt: any instruction that arrives with the image (chart type, annotations, what to fix, wording, style) is authoritative and must survive. Preserving a message is not preserving a form: the data and messages survive, the encoding usually should not.

## Front half, then the shared construct tail

`dataviz-fix` owns one stage of its own - **diagnose+extract** - and then hands into the shared construct process (`dataviz-construct`) that both repair and dataset-to-story creation use:

```text
diagnose+extract  ->  [ insight -> select -> idea -> build -> execution ]   (dataviz-construct)
```

Separate calls per stage is the default and the right way (each call carries only that stage's skills plus a compact artifact handed forward; loading every skill into one context rots it). The stages are mandatory whether or not a driver splits them: a single-turn run still walks every stage in order and may not skip one on the assumption another call did it. Handoffs are structured text (markdown sections plus, at the branch points, a small `routing` block of `key: value` lines), not strict JSON, so the pipeline runs on cheaper / open-weight models too; the routing parser (`dataviz_mcp.handoff`) also accepts a JSON object. The content contract - the exact skill subset and required fields per stage - is `dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE` (the diagnose stage plus the shared construct tail); the skill carries the reasoning, the module carries the shape.

## Stage 1 - Diagnose and extract (the front half)

Run `dataviz-brief` on the image and prompt for the key messages and required content, explicit drops, audience and medium, authoritative constraints, and the **edit-vs-redesign mode**; in parallel run `dataviz-extract` to recover the full period-by-category table (a value for every period and every category/series/stack), so any chosen form can be built. `dataviz-critique` supplies the source inventory and diagnosis. Do not choose a form here.

- **`bounded-edit`** (a literal change that keeps the source form - "recolour series 3") makes the construct tail skip `insight -> select -> idea` and go straight to `build -> execution`.
- **`redesign`** (the default when unsure) runs the full construct tail.

## The construct tail

- **Insight** (`karthik-evidence-builder`) computes the facts from the recovered data and names the headline claim + candidate annotations **freshly** - not inherited from what the source asserted.
- **Select** (`dataviz-selector`) chooses the form **cold**; the source form gets no vote. A table is a valid cold verdict.
- **Idea-critique** (`dataviz-idea-critique`) checks the plan before any render - data, expression, insight, honesty - and routes back to insight or select.
- **Build** constructs the deliverable, carrying every key message with its required content, honouring every prompt constraint.
- **Execution-critique** (`dataviz-execution`) checks the rendered export - geometry, overlap, colour, precision, ink - and confirms a redesign build carries a cold form decision (a tidied re-render of the source form routes back to select).

How many revision passes either gate runs is the driver's budget, not a fixed pass count. See `dataviz-construct` for the shared tail in full.

## Tables

Cold selection can return a table. When it does, the repair builds it with `karthik-table-style` instead of `karthik-data-visualization`, delivers it via `gt` (or markdown/HTML), and gates it through the same render path as a chart - `render_and_inspect_chart` with `content="table"` - where the execution gate reads cell alignment, decimal alignment, overflow, and font size instead of axis and baseline.

## Rendering and inspection

`render_and_inspect_chart` is the preferred mechanical path when available. If the MCP tool fails, fall back to a direct local renderer and visual inspection, and state that deterministic inspection was unavailable. Do not fabricate metadata or describe incomplete checks as complete.

## Case logging

The case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default repair path and never suppresses a valid artifact.

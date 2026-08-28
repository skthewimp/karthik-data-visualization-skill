# dataviz-fix

The **repair front half**: image in, repaired artifact out. Use it when the task is not merely to critique a chart, but to repair it and return a real artifact. (For raw data in, visual story out, use `dataviz-orchestrator`.)

`dataviz-fix` owns one stage of its own - **diagnose+extract** - and then hands into the shared construct process (`dataviz-construct`) that both repair and dataset-to-story creation use: **diagnose+extract -> [ insight -> select -> idea -> build -> execution ]**. Each stage is a separate call carrying only its own skills plus a compact artifact handed forward; that per-stage scoping is the fix for context rot. The machine-readable contract - exact skill subset and handoff schema per stage - is `dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE` (the diagnose stage plus the shared construct tail).

The path is **forward design, not critique-plus-patch**: extract the intent (`dataviz-brief`) and the data (`dataviz-extract`) from the source, then in the construct tail compute the insight freshly (`karthik-evidence-builder`), choose a form cold (`dataviz-selector`, source form gets no vote), check the idea before rendering (`dataviz-idea-critique`), build with the builder skill the select stage picks, and check the render (`dataviz-execution`). How many revision passes either gate runs is the driver's budget; a blind `dataviz-eval` reviewer runs only for an audit or high-risk decision. User feedback drives later revisions.

## Design principles

- **Forward design, not critique-first.** Repair does not begin by critiquing the source chart - that anchors on the existing image and makes "re-render the source form, tidied" the default. Intent and data come first; the form is chosen cold with the source form removed from the room. Preserving a message is not preserving a form.
- **Redesign against the image, stay faithful to the prompt.** The input image is not sacred and the source form gets no vote; any instruction that arrives with it (chart type, annotations, what to fix, wording, style) is authoritative throughout.
- **One shared construct process.** After the diagnose+extract front half, repair hands into the same `insight -> select -> idea -> build -> execution` tail that dataset-to-story creation uses. Ideas are checked before the render, execution after; the number of revision passes is the driver's budget, not a fixed cap.
- **One blind spawn, only when warranted.** The construct tail runs in the current session (cheap). Independent evaluation is the single subagent spawn - a real blind read on the converged candidate for an audit or high-risk decision, run once, never looped.

## What it does

- Extracts the repair's intent with `dataviz-brief`: key messages and required content, explicit drops, audience, story, authoritative constraints, thin keep-notes, and the edit-vs-redesign mode. A `bounded-edit` stays anchored to the source form; a `redesign` (the default when unsure) reopens it.
- Extracts the full period-by-category data table from the image with `dataviz-extract` (every category/series/period), not just totals, so any chosen form can be built.
- Hands the diagnose artifact into the construct tail, where `karthik-evidence-builder` computes the facts and names the headline claim + candidate annotations freshly from the recovered data (not inherited from the source).
- Chooses the form cold with `dataviz-selector` on the insight and data - the source chart's form is not an input and gets no vote; there is no "unless the form is clearly correct" escape hatch in the redesign path.
- Checks the idea before rendering with `dataviz-idea-critique` (data, expression, insight, honesty), routing back to insight or select.
- Rebuilds as a real PNG, SVG, or PDF with `karthik-data-visualization`, carrying every key message with its required content (which may take more than one chart, whole plus parts). Asserts the headline claim in the title and, via `chart-annotations`, ranks, words, and places the candidate marks the insight stage named.
- Checks the render with `dataviz-execution` (geometry, overlap, colour, precision, ink), confirming a redesign build carries a cold form decision; the number of passes is the driver's budget.
- Spawns one blind `dataviz-eval` reviewer on the converged candidate for an audit or high-risk decision; skips it for a purely literal or cosmetic edit.
- Falls back to direct rendering and visual inspection when MCP inspection is unavailable.
- Iterates from short user feedback without restarting the chart each time.
- Records a reusable skill lesson after acceptance only when the miss reveals a general rule or tool defect.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/scripts/case_manager.py`](codex/scripts/case_manager.py) and [`claude/scripts/case_manager.py`](claude/scripts/case_manager.py) - deterministic case logger.
- [`tests/test_case_manager.py`](tests/test_case_manager.py) - state, budget, context, and termination regression tests.

## Relationship to other skills

`dataviz-fix` is the repair front half. It opens with `dataviz-brief` (intent), `dataviz-extract` (data), and `dataviz-critique` (source diagnosis), then hands into the shared construct process (`dataviz-construct`): `karthik-evidence-builder` (insight), `dataviz-selector` (form, chosen cold), `dataviz-idea-critique` (pre-render gate), `karthik-data-visualization` / `karthik-table-style` and `chart-annotations` (build), and `dataviz-execution` (post-render gate) - plus the installed writing or brand-style skill when one is available. `dataviz-eval` is the single independent reviewer spawned once for an audit; the case manager is an optional audited path, not a default release gate.

## Edit rule

Mirror behavioural and script changes across the Codex and Claude surfaces.

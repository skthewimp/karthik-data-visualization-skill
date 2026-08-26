# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

**Repair is forward design, not critique-plus-patch.** The flow no longer starts by critiquing the source chart - that anchored everything on the existing image and made "re-render the same form, tidied" the path of least resistance. Instead it extracts the intent and the data first, selects a form cold from those, builds, and only then checks. Critique is a downstream checker here, not the first move.

Two anchors govern the flow. A valid rendered candidate must always be delivered. And the repair may redesign freely against the input image - the source form gets no vote - while staying faithful to the prompt: any instruction that arrives with the image (chart type, annotations, what to fix, wording, style) is authoritative and must survive. Preserving a message is not preserving a form: the data and messages survive, the encoding usually should not.

## Staged, not one context

`dataviz-fix` is the **repair orchestrator**, and it runs as a sequence of separate calls - **diagnose+extract -> select -> build -> refine** - each carrying only the skills that stage needs plus a compact structured artifact handed forward. Loading every skill into one context rots it; the build stage has no use for the discovery or evaluation skills. The eight steps below map onto those four stages (1-2 diagnose, 3 select, 4 build, 5-7 refine). Handoffs are structured text (markdown sections plus, at the branch points, a small `routing` block of `key: value` lines), not strict JSON, so the pipeline runs on cheaper / open-weight models too; the routing parser (`dataviz_mcp.handoff`) also accepts a JSON object. The content contract - the exact skill subset and required fields per stage - is `dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE`; the skill carries the reasoning, the module carries the shape.

## Default workflow

1. **Intent - build the brief.** Run `dataviz-brief` on the image and prompt: key messages and required content, explicit drops, audience and medium, story, authoritative constraints, thin keep-notes, and the **edit-vs-redesign mode**. `bounded-edit` stays anchored to the source form (skip steps 2-3, apply the named edit in step 4); `redesign` (the default when unsure) reopens the form.
2. **Data - extract the full table.** In parallel, run `dataviz-extract` to recover the full period-by-category table (a value for every period and every category/series/stack), not just totals - so any chosen form can be built.
3. **Select - choose the form cold.** Run `dataviz-selector` on the intent and data, **cold**: the source chart's form is not an input and gets no vote. For "many series over time, compare trajectories" this is small multiples or direct-labelled lines - the source stack is not in the room. There is no "unless the source form is clearly correct" escape hatch in the redesign path.
4. **Build.** Construct with `karthik-data-visualization`, carrying every key message with its required content - which may be more than one chart (whole plus parts). Invoke `chart-annotations` whenever the chart may have a point worth marking and let it judge whether any mark clears the bar. Compose the headline and subhead here (claim from `chart-annotations`, style from `karthik-data-visualization`, voice from an installed writing skill if any). Honour every prompt constraint; build one PNG, SVG, or PDF. For a `bounded-edit`, skip the cold selection and apply the named edit to the source form.
5. **Critique - the downstream checker loop.** Run `dataviz-critique` on the exact export at delivery size, in the same chat, as a checker: does the candidate carry the step-1 intent (every key message, nothing key silently dropped, constraints honoured), and is it a good chart (mechanical and semantic)? It does not re-derive the messages or reopen the form unless a message genuinely fails. Consolidate into one focused revision per pass, cap at two passes, exit on no fatal or major defect.
6. **One independent evaluation.** Spawn exactly one subagent to run `dataviz-eval` as a blind reviewer on the converged candidate - artifact plus a short brief (prompt, inferred style, headings, intended message), **not** the source image, diagnosis, or code. It returns one verdict and is never re-spawned. Skip for a purely literal or cosmetic edit.
7. **One final revision.** Apply at most one in-context revision from the eval findings, without spawning again. An expensive redesign is applied when cheap; otherwise deliver and surface the concern in one sentence.
8. **Deliver and continue.** Deliver with its actual status. User feedback is the main release signal: continue from the latest candidate, change the smallest relevant part, inspect the named element, and return it.

## Why the order changed

Three consecutive prose patches to the old critique-first flow each fixed a symptom and exposed the next (drop the categories → drop them with a justification → keep them but re-render the same stack). All three traced to one root cause: the flow started by critiquing the source chart, so the path of least resistance was always "re-render the source form, tidied", and prose guardrails could not overcome the ordering. The fix is structural: extract intent and data first, then choose the form cold with the source form removed from the room. See [`../design/dataviz-fix-repair-flow.md`](../design/dataviz-fix-repair-flow.md).

## Why one chat and one spawn

Invoking a skill loads its instructions into the current session - it is not a new LLM session. So the brief, extract, selection, build, and checker loop are all cheap: same model, same context, different instruction files. A subagent (the `Agent`/`Task` tool) is a genuinely separate session with a cold start. The flow spawns exactly once, on the converged candidate, to recover a real blind read at bounded cost. A same-session checker catches mechanical regressions well but conceptual blind spots poorly; the single independent eval closes that gap.

## Tables

Cold selection can return a table. When it does, the repair builds it with `karthik-table-style` instead of `karthik-data-visualization`, delivers it via `gt` (or markdown/HTML), and gates it through the same render path as a chart - `render_and_inspect_chart` with `content="table"` - where the checker reads cell alignment, decimal alignment, overflow, and font size instead of axis and baseline.

## Rendering and inspection

`render_and_inspect_chart` is the preferred mechanical path when available. If the MCP tool fails, fall back to a direct local renderer and visual inspection, and state that deterministic inspection was unavailable. Do not fabricate metadata or describe incomplete checks as complete.

## Case logging

The case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default repair path and never suppresses a valid artifact.

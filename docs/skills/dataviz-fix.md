# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

Two anchors govern the flow. A valid rendered candidate must always be delivered. And the repair may redesign freely against the input image while staying faithful to the prompt: any instruction that arrives with the image - requested chart type, annotations, what to fix, wording, brand or style preferences - is authoritative and must survive the whole process.

## Default workflow

1. **Critique the source once.** Run `dataviz-critique` in the current chat as a single pass (JSON is fine), with no maker-checker on the critique. Judge the right form, the trifecta, whether the chart conveys its message (including the semantic scan), the requested style, and repair-versus-redesign with a bias toward redesign. In parallel, infer the raw data from the image.
2. **Reconstruct.** Rebuild from the critique, prompt, inferred data, and inferred style. Load `dataviz-selector` by default (unless the form is clearly correct), `karthik-data-visualization`, and the installed writing or brand-style skill when available. Invoke `chart-annotations` whenever the chart may have a point worth marking and let it judge whether any mark is warranted - it can decide the chart stays unmarked. Compose the headline and subhead here: title claim from `chart-annotations`, style from `karthik-data-visualization`, voice from the writing skill if installed (there is no dedicated headline skill). Honour every prompt constraint. Build one PNG, SVG, or PDF.
3. **In-context checker loop.** Critique the exact export at delivery size in the same chat, consolidate issues into one focused revision, and reinspect the changed regions. Cap the loop at two passes and exit as soon as no fatal or major defect remains.
4. **One independent evaluation.** Spawn exactly one subagent to run `dataviz-eval` as a blind reviewer on the converged candidate. Give it only the rendered artifact and a short brief (prompt, inferred style, inferred headings and subheadings, intended message) - not the source image, the maker's diagnosis, the claimed fixes, or the rendering code. It returns one verdict and ranked findings; it is never re-spawned. Skip this step for a purely literal or cosmetic edit.
5. **One final revision.** Apply at most one in-context revision from the eval findings, without spawning again or re-entering the loop. An expensive redesign is applied when cheap; otherwise deliver the current candidate and surface the concern to the user.
6. **Deliver and continue.** Deliver the artifact with its actual status. User feedback is the main release signal: continue from the latest candidate, change the smallest relevant part, inspect the named element, and return it.

## Why one chat and one spawn

Invoking a skill loads its instructions into the current session - it is not a new LLM session. So critique and the checker loop are cheap: same model, same context, different instruction files. A subagent (the `Agent`/`Task` tool) is a genuinely separate session with a cold start. The old default looped an independent `dataviz-eval` subagent on every iteration, which is what made iterations slow. The current flow spawns exactly once, on the converged candidate, to recover a real blind read at bounded cost.

A same-session checker catches mechanical regressions well but conceptual blind spots poorly, because the checker is the same context that built the chart. The single independent eval is what closes that gap.

## Rendering and inspection

`render_and_inspect_chart` is the preferred mechanical path when available. If the MCP tool fails, fall back to a direct local renderer and visual inspection, and state that deterministic inspection was unavailable. Do not fabricate metadata or describe incomplete checks as complete. Typography is judged by hierarchy at delivery size, not only minimum legibility, and duplicate identification or scale scaffolding should be removed.

## Case logging

The detailed case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default repair path and never suppresses a valid artifact.

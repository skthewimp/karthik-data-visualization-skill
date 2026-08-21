# dataviz-fix

Use this skill when the task is not merely to critique a chart, but to repair it and return a real artifact.

The default path is **forward design, not critique-plus-patch**: extract the intent (`dataviz-brief`) and the data (`dataviz-extract`) from the source, choose a form cold (`dataviz-selector`, source form gets no vote), build the chart(s), run an in-context critique-checker loop capped at two passes, then spawn exactly one blind `dataviz-eval` reviewer, apply at most one final revision, and deliver. User feedback drives later revisions.

## Design principles

- **Forward design, not critique-first.** Repair does not begin by critiquing the source chart - that anchors on the existing image and makes "re-render the source form, tidied" the default. Intent and data come first; the form is chosen cold with the source form removed from the room. Preserving a message is not preserving a form.
- **Redesign against the image, stay faithful to the prompt.** The input image is not sacred and the source form gets no vote; any instruction that arrives with it (chart type, annotations, what to fix, wording, style) is authoritative throughout.
- **One chat, one spawn.** The brief, extract, selection, build, and checker loop run in the current session (cheap). Independent evaluation is the single subagent spawn - a real blind read, run once, never looped.

## What it does

- Extracts the repair's intent with `dataviz-brief`: key messages and required content, explicit drops, audience, story, authoritative constraints, thin keep-notes, and the edit-vs-redesign mode. A `bounded-edit` stays anchored to the source form; a `redesign` (the default when unsure) reopens it.
- Extracts the full period-by-category data table from the image with `dataviz-extract` (every category/series/period), not just totals, so any chosen form can be built.
- Chooses the form cold with `dataviz-selector` on the intent and data - the source chart's form is not an input and gets no vote; there is no "unless the form is clearly correct" escape hatch in the redesign path.
- Rebuilds as a real PNG, SVG, or PDF with `karthik-data-visualization`, carrying every key message with its required content (which may take more than one chart, whole plus parts). Invokes `chart-annotations` whenever the chart may have a point worth marking and lets that skill judge whether any mark clears the bar.
- Composes the headline and subhead in the build step: title claim from `chart-annotations`, style from `karthik-data-visualization`, voice from the installed writing skill when available. There is no separate headline skill.
- Runs `dataviz-critique` as a downstream checker on the export, capped at two passes, exiting on no fatal or major defect. It verifies the candidate against the brief; it does not re-derive the messages or reopen the form.
- Spawns one blind `dataviz-eval` reviewer on the converged candidate; skips it for a purely literal or cosmetic edit.
- Applies at most one final revision from eval findings, with no re-spawn.
- Falls back to direct rendering and visual inspection when MCP inspection is unavailable.
- Iterates from short user feedback without restarting the chart each time.
- Records a reusable skill lesson after acceptance only when the miss reveals a general rule or tool defect.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/scripts/case_manager.py`](codex/scripts/case_manager.py) and [`claude/scripts/case_manager.py`](claude/scripts/case_manager.py) - deterministic case logger.
- [`tests/test_case_manager.py`](tests/test_case_manager.py) - state, budget, context, and termination regression tests.

## Relationship to other skills

`dataviz-fix` is the repair umbrella. It opens with `dataviz-brief` (intent) and `dataviz-extract` (data), then uses `dataviz-selector` (form, chosen cold), `karthik-data-visualization`, and `chart-annotations` to build, and `dataviz-critique` as the downstream checker - plus the installed writing or brand-style skill when one is available. `dataviz-eval` is the single independent reviewer spawned once per flow; the case manager is an optional audited path, not a default release gate.

## Edit rule

Mirror behavioural and script changes across the Codex and Claude surfaces.

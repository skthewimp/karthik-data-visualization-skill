# dataviz-fix

Use this skill when the task is not merely to critique a chart, but to repair it and return a real artifact.

The default path: run one single-pass `dataviz-critique` on the source, reconstruct the chart (biased toward redesign, faithful to the prompt), run an in-context critique-checker loop capped at two passes, then spawn exactly one blind `dataviz-eval` reviewer, apply at most one final revision, and deliver. User feedback drives later revisions.

## Design principles

- **Redesign against the image, stay faithful to the prompt.** The input image is not sacred; any instruction that arrives with it (chart type, annotations, what to fix, wording, style) is authoritative throughout.
- **One chat, one spawn.** Critique and the checker loop run in the current session (cheap). Independent evaluation is the single subagent spawn in the flow - a real blind read, run once, never looped. This is the deliberate fix for slow, unbounded maker-checker loops.

## What it does

- Rebuilds an uploaded or pasted visualization as a real PNG, SVG, or PDF.
- Runs the source critique once (JSON is fine) with no maker-checker on the critique itself.
- Invokes `dataviz-selector` (default-on unless the form is clearly correct) and `chart-annotations` (default-on for redesigns) during reconstruction.
- Runs an in-context checker loop on the export, capped at two passes, exiting on no fatal or major defect.
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

`dataviz-fix` is the repair umbrella. It uses `dataviz-critique`, `dataviz-selector`, `chart-annotations`, and `karthik-data-visualization`, plus the installed writing or brand-style skill when one is available. `dataviz-eval` is the single independent reviewer spawned once per flow; the case manager is an optional audited path, not a default release gate.

## Edit rule

Mirror behavioural and script changes across the Codex and Claude surfaces.

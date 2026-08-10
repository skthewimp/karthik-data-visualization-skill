# dataviz-eval

Use this skill when a rendered chart, dashboard, or draft already exists and the question is: *is this ready to send, or does it need another render cycle?*

This is the inspection gate between chart creation and delivery. It looks at the actual artifact, not the code, and is tuned for clipping, overlap, label crowding, header collisions, export-vs-viewport mismatches, and chat/slide legibility.

## What it does

- Scores readability, integrity, hierarchy, and delivery readiness.
- Gives a clear `Send / Revise / Redesign` verdict.
- Checks geometry, direct labels, title/source/unit fit, and compression survival.
- Tells you whether to fix spacing and labels first, or hand the work back to critique/fix.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude/Hermes-compatible version.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `dataviz-critique` when the chart form itself seems wrong. Use `dataviz-selector` before charting. Use `karthik-data-visualization` for implementation and render iteration. Use `dataviz-fix` when revising a chart through feedback.

## Edit rule

If evaluation behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep the docs, the skill files, and the evaluation rubric aligned.

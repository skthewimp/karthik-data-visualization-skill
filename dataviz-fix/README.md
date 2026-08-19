# dataviz-fix

Use this skill when the task is not merely to critique a chart, but to repair it and return a real artifact.

The default path builds one candidate, inspects it once, and delivers it. It makes one more candidate only when a major visible defect remains. User feedback drives later revisions.

## What it does

- Rebuilds an uploaded or pasted visualization as a real PNG, SVG, or PDF.
- Iterates from short user feedback without restarting the chart each time.
- Inspects the exact export once for obvious mechanical defects.
- Delivers the best valid artifact within two candidates or ten elapsed minutes.
- Falls back to direct rendering and visual inspection when MCP inspection is unavailable.
- Uses independent evaluation and detailed case logging only for explicit audited, high-risk, or benchmark work.
- Records a reusable skill lesson after acceptance only when the miss reveals a general rule or tool defect.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/scripts/case_manager.py`](codex/scripts/case_manager.py) and [`claude/scripts/case_manager.py`](claude/scripts/case_manager.py) - deterministic case logger.
- [`tests/test_case_manager.py`](tests/test_case_manager.py) - state, budget, context, and termination regression tests.

## Relationship to other skills

`dataviz-fix` is the repair umbrella. It uses `dataviz-critique` and `karthik-data-visualization`, and calls other skills only when their failure mode is relevant. `dataviz-eval` and the case manager are optional audited paths, not default release gates.

## Edit rule

Mirror behavioural and script changes across the Codex and Claude surfaces.

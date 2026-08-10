# dataviz-fix

Use this skill when the task is not merely to critique a chart, but to repair it through a real feedback loop and improve the skill stack from the accepted result.

The skill keeps the original chart, each rendered revision, the user's corrections, the accepted chart, and a compact diagnosis of why the first output missed. It then routes any reusable lesson to the one skill that owns it.

## What it does

- Rebuilds an uploaded or pasted visualization as a real PNG, SVG, or PDF.
- Iterates from short user feedback without restarting the chart each time.
- Sends every render to a fresh independent `dataviz-eval` reviewer, saves the pre-intent blind read separately, and stores the scoped gate results, five release checks, failure codes, and minimum pass set.
- Stores a case packet with original, revisions, independent review reports, feedback, and skill-version hashes.
- Separates execution misses from missing, ambiguous, or conflicting skill rules.
- Makes only reusable skill changes; it avoids overfitting one chart's values or layout.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude/Hermes-compatible version.
- [`codex/scripts/case_manager.py`](codex/scripts/case_manager.py) and [`claude/scripts/case_manager.py`](claude/scripts/case_manager.py) - deterministic case logger.

## Relationship to other skills

`dataviz-fix` is the repair-loop umbrella. `dataviz-eval` is its required rendered-artifact gate. It calls `dataviz-critique`, `dataviz-selector`, `karthik-data-visualization`, `chart-annotations`, and the analytical skills when their failure mode is relevant.

## Edit rule

Mirror behavioural and script changes across the Codex and Claude surfaces. The Claude surface is also the Hermes install source.

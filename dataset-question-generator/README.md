# dataset-question-generator

Dataset-question skill: use this when the question is **what should we ask of this raw dataset?**

It profiles the dataset first, rejects obvious or stale prompts, and returns fresh visualisable questions in Karthik's analysis style.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version of the skill, with Claude-safe metadata.

## Edit rule

If you change skill behavior, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific.

## Relationship to other skills

Use this before `karthik-analysis-planner`, `dataviz-selector`, and `karthik-data-visualization`. This skill finds the candidate questions; the planner makes one question operational; the selector picks the visual; the visualization skill styles the output.

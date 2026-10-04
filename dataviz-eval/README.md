# dataviz-eval

`dataviz-eval` measures whether a rendered visualization does its job for a particular question, evidence base, audience, and delivery medium.

It has two modes:

- **Artifact gate:** inspect one delivered chart and return `Send`, `Revise`, `Redesign`, or `Not evaluable`.
- **Creator-system benchmark:** compare chart-producing agents, prompts, renderers, or skill versions across a representative golden set.

The live evaluation uses separate expert and audience blind reads before revealing the intended question and insight. It then checks evidence, question recovery, insight recovery, visual reasoning, information fit, and the actual export at its intended size. Fatal failures are gates; they are not averaged into a cosmetic score.

## Why it is optional

This is a formal audit, not a default `dataviz-fix` stage. Its blind review and strict gates can block `Send`, add model calls, and create repeated revisions. That is appropriate when the user requests an independent verdict, a consequential claim needs scrutiny, or a creator system is being benchmarked. It is unnecessary for an ordinary repair that can be built, inspected, delivered, and improved from user feedback.

Do not auto-load `dataviz-eval` during normal repair. When it is used, its verdict may guide the next revision, but it must not suppress the strongest valid artifact already produced.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/references/evaluation-framework.md`](codex/references/evaluation-framework.md) and [`claude/references/evaluation-framework.md`](claude/references/evaluation-framework.md) - gate anchors, failure codes, benchmark method, and calibration cases.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

- Use `dataviz-selector` to choose a visual form before plotting.
- Use `karthik-data-visualization` to create and style the chart.
- Use `dataviz-critique` for open-ended diagnosis and alternatives.
- Use `dataviz-eval` only when a formal independent pass line is needed.
- Use `dataviz-fix` to execute revisions and preserve the feedback trail.

## Edit rule

Keep both surfaces aligned. If the protocol, gate anchors, or failure codes change, update both `SKILL.md` files, both reference files, and the human documentation in the same change.

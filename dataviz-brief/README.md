# dataviz-brief

Use this skill at the **start** of a chart repair, before any chart is chosen or built. It extracts the intent - what the replacement must say and carry - from the source image and any prompt, so the rest of the repair is designed forward from that intent rather than patched onto the old chart.

This is the fix for a class of repair failures where starting with a critique of the source chart anchored everything on the existing image, and the path of least resistance became "re-render the same form, tidied". The brief reads the source but never defends it: it decides *what the chart must say*, not *how it should look*. The form question belongs to `dataviz-selector`, run afterwards and cold.

## What it produces

- **Key messages** and the **required content** for each - read partly out of the source's own encoding (a stacked chart's categories are a key message), never shrunk because the source is hard to read.
- **Explicit drops** - anything judged not key, named with a reason in message terms. No silent losses.
- **Audience, medium, and story** - who reads it, at what size, and the one-sentence point if the evidence implies one.
- **Authoritative constraints** from the prompt - chart type, annotations, wording, brand or style.
- **Edit-vs-redesign mode** - `bounded-edit` (stay anchored to the source form, skip form selection) vs `redesign` (reopen the form, select cold). Default to `redesign` when unsure.
- **Keep-notes** - a thin list of genuinely reusable source ideas (a smart annotation, a top-N-plus-"other" grouping). Not a fault-list.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

`dataviz-brief` is step 1 of `dataviz-fix`. It runs in parallel with `dataviz-extract` (which recovers the data table), then feeds `dataviz-selector` (which chooses the form cold from the brief and data). `dataviz-critique` is the downstream checker that verifies a built candidate against this brief.

## Edit rule

Update both `codex/SKILL.md` and `claude/SKILL.md` together; keep them byte-identical. Keep `docs/skills/dataviz-brief.md` aligned with the public behaviour.

# Dataviz Brief

Use `dataviz-brief` at the start of a chart repair, before any chart is chosen or built. It extracts the **intent** - what the replacement must say and carry - from the source image and any prompt, so the repair is designed *forward* from that intent instead of patched onto the old chart.

## Why it exists

Repairs used to begin by critiquing the source chart. Critiquing the source anchors everything on the existing image, and the path of least resistance becomes "re-render the same form, tidied". That reliably fails a whole class of charts - most visibly a many-series stacked bar whose message is per-series comparison, which no amount of tidying makes legible. Extracting the brief first, and choosing the form cold from the brief, takes the source form out of the room.

The governing principle: **preserving a message is not preserving a form.** The data and messages must survive; the encoding must not, and usually should not when the source form was the weakness.

## What it produces

- **Key messages** and the **required content** for each. The source's own encoding is read as intent - a stacked or multi-series chart's categories are a key message - but difficulty of reading the source is never allowed to shrink the intent.
- **Explicit drops.** Anything judged not key is named with a reason in message terms. Silence is not a decision; silent drops are the bug this guards against.
- **Audience, medium, and story.** Who reads it, at what size, and the one-sentence point if the evidence implies one.
- **Authoritative constraints** from the prompt - chart type, annotations, wording, brand or style - which must survive the whole repair.
- **Edit-vs-redesign mode.** `bounded-edit` (a literal change that leaves the source form intact - stay anchored, skip form selection) versus `redesign` (reopen the form, select cold). The default when unsure is `redesign`.
- **Keep-notes.** A thin list of genuinely reusable source ideas - a smart annotation, a sensible top-N-plus-"other" grouping. This is *not* a fault-list of the source and *not* a defence of its form.

## What it does not do

- It does not choose a chart form - that is `dataviz-selector`, run afterwards and cold on this brief.
- It does not extract the full data table - that is `dataviz-extract`, run in parallel.
- It does not critique the source's execution. Forward design needs the intent the chart should have served, not a diagnosis of how the old chart failed.

## Relationship to other skills

Step 1 of `dataviz-fix`. Runs in parallel with `dataviz-extract`; feeds `dataviz-selector` and the build step. `dataviz-critique` later verifies the built candidate against this brief.

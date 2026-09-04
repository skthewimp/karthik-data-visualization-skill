---
name: dataviz-brief
description: Extract the design brief for a chart repair - key messages, required content, audience, constraints, and an edit-vs-redesign decision - from an image and any prompt.
---

# Dataviz Brief

Use at the **start** of a chart repair, before any chart is chosen or built. Its job is to state what the replacement must accomplish - the intent - so everything downstream is designed *forward* from that intent, not patched onto the source.

This skill reads the source but doesn't defend it: no fault-list of the old chart, and the old form never decides the new one (form is `dataviz-selector`'s, run afterwards and cold). Here you decide only *what the chart must say and carry*, not *how it should look*.

## Why this runs first

A repair that begins by critiquing the source anchors on the existing image, and the path of least resistance becomes "re-render the same form, tidied" - which fails a whole class of charts, most visibly a many-series stacked bar whose message is per-series comparison. Extracting the brief first and selecting the form cold from it removes the source form from the room. **Preserving a message is not preserving a form:** the data and messages must survive; the encoding usually should not when the source form was the weakness.

## Inputs

- The source image or artifact.
- The prompt, if any: requested change, chart-type requests, annotations, wording, brand/style preferences, audience notes. Treat everything stated here as a requirement, not a suggestion.

## What to produce

A short brief with these parts (prose or JSON, concise):

### 1. Key messages

State the one or few messages the chart exists to carry - e.g. "total usage is growing" *and* "the mix is shifting away from a dominant incumbent". More than one is legitimate.

- **The source's form declares its messages.** Whatever the source encodes as its primary structure (whatever colour, stack, or facet carries) is presumptively a key message - a stacked/multi-series/faceted chart exists to show that composition or comparison. Read it as key unless the prompt redirects to a different question. This is how you read intent *out of* the source; it's not a reason to keep the source's form.
- **Difficulty of recovery is never grounds to drop a message** - neither uncertain values ("approximate", "too many categories to read exactly") nor uncertain identity ("the legend names fewer categories than encoded", "can't map every colour to a label"). Both are facts about the source form's weakness and argue for a better form downstream (small multiples, direct-labelled lines, top-N plus explicit "other", share-of-total), never for deleting the message. When some labels can't be recovered, keep the categories: name the ones the source identifies and mark the rest generically.

### 2. Required content per message

For each key message, name the data and encoding the rebuild must show - the specific series, periods, breakdowns, comparisons, or annotations without which it collapses. A per-category breakdown is required for "the mix is shifting", not for "the total is growing".

### 3. Explicit drops

Name anything *not* key, and why, in message terms. A drop is legitimate only when the information serves no key message - not when it's inconvenient to recover or render. Silence is not a decision: a multi-category chart that comes back as a bare total has failed if no one decided to lose the breakdown.

### 4. Audience, story, and constraints

- **Audience and medium:** who reads this, expected literacy, viewing size (slide, chat, thumbnail, print).
- **Story:** the one-sentence point the chart should leave, if the prompt or evidence implies one. Don't manufacture a claim when the evidence is exploratory.
- **Constraints from the prompt:** requested chart type, annotations, wording, brand/style, what to fix - authoritative, and they must survive the whole repair. When a downstream redesign impulse conflicts with a stated constraint, the constraint wins.

### 5. Edit-vs-redesign mode

Emit the mode explicitly - it decides whether the form is reopened:

- **`bounded-edit`:** a literal, self-contained change leaving the form intact and correct ("fix the axis labels", "change the title", "recolour series 3", "remove the gridlines"). Skip form selection and full data extraction; apply the edit and re-render. Choose only when the existing form genuinely serves the messages and the prompt doesn't question it.
- **`redesign`:** everything else - a new question, a weak or misleading form, a per-series message trapped in a stack, "make this clearer", or no prompt. The source form gets no vote; form selection runs cold.

When in doubt, choose `redesign` - a bounded-edit that needs a form change can be widened; a redesign wrongly narrowed to an edit reproduces the source's weakness.

### 6. Keep-notes (thin)

Optional: is anything in the source worth carrying forward as an idea - a smart annotation, a sensible top-N-plus-"other" grouping, a good baseline or period window? List only real, reusable ideas. Not a fault-list, not a defence of the form. If nothing stands out, say so.

## Output shape

```markdown
Key messages:
  - <message> - required content: <series/periods/breakdowns/comparisons>
  - ...
Dropped as not key (with reason): <item - why, in message terms | none>
Audience / medium: <who, literacy, viewing size>
Story: <one-sentence point | exploratory, no single claim>
Constraints (authoritative): <chart type, annotations, wording, style, what to fix | none>
Mode: bounded-edit | redesign
Keep-notes: <reusable source ideas | none>
```

## Boundaries

- Don't choose a chart form here - that's `dataviz-selector`, run afterwards and cold on this brief.
- Don't extract the full data table beyond what you need to name the messages; period-by-category extraction is `dataviz-extract`, run in parallel.
- Don't critique the source's execution - a forward-design repair needs only the intent the old chart should have served.

---
name: dataviz-brief
description: Extract the design brief for a chart repair - key messages, required content, audience, constraints, and an edit-vs-redesign decision - from an image and any prompt.
---

# Dataviz Brief

Use this at the **start** of a chart repair, before any chart is chosen or built. Its job is to state what the replacement must accomplish - the intent - so that everything downstream is designed *forward* from that intent, not patched onto the source chart.

This skill reads the source, but it does not defend the source. It never produces a fault-list of the old chart, and it never lets the old chart's form decide the new one. The form question belongs to `dataviz-selector`, run afterwards and cold. Here you decide only *what the chart must say and carry*, not *how it should look*.

## Why this runs first

A repair that begins by critiquing the source chart anchors on the existing image, and the path of least resistance becomes "re-render the same form, tidied". That fails a whole class of charts - most visibly a many-series stacked bar whose message is per-series comparison, which no amount of tidying makes legible. Extracting the brief first, and selecting the form cold from the brief, removes the source form from the room. **Preserving a message is not preserving a form.** The data and the messages must survive; the encoding must not, and usually should not when the source form was the weakness.

## Inputs

- The source image or artifact.
- The prompt, if any: the requested change, chart-type requests, annotations, wording, brand or style preferences, audience notes. Treat everything the user states here as a requirement, not a suggestion.

## What to produce

A short brief with these parts. Prose or JSON both fine; keep it concise.

### 1. Key messages

From the source and any prompt, state the one or few messages the chart exists to carry - for example "total usage is growing" *and* "the mix is shifting away from a dominant incumbent". A chart may legitimately carry more than one.

- **The source's form declares its messages.** Whatever the source encodes as its primary structure is presumptively a key message. A stacked, multi-series, or faceted chart exists to show composition or comparison across those categories - that comparison *is* a message, not optional detail. Read the primary encoded dimension (whatever colour, stack, or facet carries) as key unless the prompt explicitly redirects to a different question. This is how you read intent *out of* the source; it is not a reason to keep the source's form.
- **Difficulty of recovery is never grounds to drop a message.** "Values are approximate", "read from a screenshot", "too many categories to read exactly", "crowded legend", "would invent unreadable precision" - none of these shrink the intent. They are facts about the source form's weakness, and they argue for a better form downstream (small multiples, direct-labelled lines, top-N plus an explicit "other", a share-of-total view), never for deleting the message here. Approximate category values, labelled approximate, still carry the message; exact precision was never the point.

### 2. Required content per message

For each key message, name the data and encoding the rebuild must show to support it - the specific series, periods, breakdowns, comparisons, or annotations without which the message collapses. A per-category breakdown is required content for a "the mix is shifting" message; it is not for a "the total is growing" message.

### 3. Explicit drops

Name anything you judge *not* key, and why, in message terms. A drop is legitimate only when the information serves no key message - not when it is merely inconvenient to recover or render. Silence is not a decision: a ten-category stacked chart that comes back as a bare total failed because no one decided to lose the model mix. If you drop, say so out loud with a reason.

### 4. Audience, story, and constraints

- **Audience and medium**: who reads this, expected data literacy, viewing size (slide, chat, thumbnail, print). This shapes the form later.
- **Story**: the one-sentence point the chart should leave the reader with, if the prompt or evidence implies one. Do not manufacture a claim when the evidence is exploratory.
- **Constraints from the prompt**: requested chart type, annotations, wording, brand or style preferences, what to fix. These are authoritative and must survive the whole repair. When a downstream redesign impulse conflicts with a stated constraint, the constraint wins.

### 5. Edit-vs-redesign mode

Classify the request and emit the mode explicitly - this decides whether the form is reopened downstream:

- **`bounded-edit`**: a literal, self-contained change to the existing chart that leaves its form intact and correct - "fix the axis labels", "change the title", "recolour series 3", "remove the gridlines". Stay anchored to the source form; skip form selection and full data extraction; apply the named edit and re-render. Choose this only when the existing form genuinely serves the messages and the prompt does not question it.
- **`redesign`**: everything else - a new question, a weak or misleading form, a per-series message trapped in a stack, "make this clearer", or no prompt at all. The form is reopened. Downstream, `dataviz-selector` runs cold on the messages and data; the source form gets no vote.

When in doubt, choose `redesign`. A bounded-edit that turns out to need a form change can always be widened; a redesign wrongly narrowed to an edit reproduces the source's weakness.

### 6. Keep-notes (thin)

A short, optional pass: is anything in the source genuinely worth carrying forward as an idea - a smart annotation, a sensible top-N-plus-"other" grouping, a good baseline or reference line, a well-chosen period window? List only real, reusable ideas. This is *not* a fault-list of the source and *not* a defence of its form. If nothing stands out, say so and move on.

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

- Do not choose a chart form here. That is `dataviz-selector`, run afterwards and cold on this brief.
- Do not extract the full data table here beyond what you need to name the messages. Detailed period-by-category extraction is `dataviz-extract`, run in parallel.
- Do not critique the source chart's execution. Diagnosis of what is wrong with the old chart is not needed for a forward-design repair; you need only the intent it should have served.

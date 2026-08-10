---
name: dataviz-eval
description: Evaluate an existing chart, dashboard, or draft for readability, integrity, hierarchy, and delivery readiness. Use when deciding whether a rendered visualization is ready to send or needs another inspect→revise cycle; especially for clipping, overlap, whitespace, export-vs-viewport mismatches, and chat/slide legibility.
metadata:
  short-description: Evaluate chart readiness
  claude-description: Evaluate a rendered chart or chart draft for legibility, correctness, and delivery readiness.
---

# Dataviz Eval

Use this when a chart, dashboard, infographic, or rendered draft already exists and you need to decide whether it is ready to send, needs revision, or should be redesigned.

This skill is about *evaluation*, not chart choice and not implementation. If the chart form itself is wrong, hand off to `dataviz-critique` or `dataviz-selector`. If the chart is mostly right but needs repair, hand off to `dataviz-fix` and `karthik-data-visualization`.

## When to use

- The user asks “is this readable?”, “does this look right?”, “should I send it?”, or “what’s still wrong?”
- You have a rendered PNG/SVG/PDF and need a pass/fail judgment.
- You need to inspect clipping, overlap, label crowding, header collisions, or whitespace before delivery.
- You need to verify that the export itself is correct, not just the browser preview or code.
- You want a compact evaluation rubric before a second render cycle.

## Evaluation protocol

### 1) Identify the delivery target

Ask:
- What size will the viewer actually see?
- Is this for chat, slide, web, or print?
- Is the exported artifact the real deliverable, or just a preview?

### 2) Inspect the rendered artifact, not the code

Check the actual output image/PDF/SVG at the intended display size if possible.

Look for:
- clipped text or marks
- overlapping labels
- illegible small text
- title/subtitle/header collisions
- wasted whitespace or a crushed plotting area
- mismatched orientations or aspect ratio surprises
- axes, legends, or annotations that compete with the data
- low contrast after compression or screenshotting

### 3) Score the chart on four questions

Use this rubric:

- **Readability** — Can a viewer understand it quickly?
- **Integrity** — Are scales, labels, units, and encodings truthful and consistent?
- **Hierarchy** — Does the chart guide attention to the main comparison first?
- **Delivery readiness** — Will it survive the intended medium without breaking?

### 4) Decide the verdict

Use one of:
- **Send** — no major issue remains.
- **Revise** — the chart is close, but one or more fixes are needed.
- **Redesign** — the current form is the wrong solution.

## What to check

### Legibility
- Title, subtitle, axis labels, and source note are readable.
- Numbers and category labels are large enough for the target medium.
- Labels do not overlap or clip.
- Endpoint labels, callouts, and annotations are placed with enough clearance.

### Geometry
- The chart uses the canvas intentionally.
- Margins are wide enough for labels and headers.
- Portrait vs landscape matches the content.
- The artboard is shaped for the row count / series count.
- Direct labels have room to breathe.

### Truthfulness
- Bars start at zero when they should.
- Units are present and consistent.
- Denominators and transformations are explicit.
- Legends and colours map to the right categories.
- No redundant or misleading encodings remain.

### Story fit
- The chart answers one main question.
- The chart form matches the comparison.
- The main comparison is visible in seconds.
- Uncertainty, caveats, or sources are shown if needed to prevent overclaiming.

### Medium fit
- Chat delivery: readable after compression.
- Slide delivery: strong hierarchy from a distance.
- Web delivery: labels and hover-free content still work.
- Print delivery: source and small labels remain legible.

## Common failure patterns

- Browser preview looks fine, but the saved export is clipped or wider than intended.
- Direct labels are added, but the chart still has axes/legend clutter competing with them.
- Text is shrunk instead of fixing geometry.
- The chart is legible in full size but fails at thumbnail size.
- The form is technically valid but still makes the wrong thing hard to see.
- Small palette differences disappear after chat compression.

## Output format

Use this structure:

```markdown
## Verdict
Send / Revise / Redesign

## Why
- Readability: ...
- Integrity: ...
- Hierarchy: ...
- Delivery readiness: ...

## Issues
1. ...
2. ...
3. ...

## Next action
- If revise: what to change next
- If redesign: the better chart form
```

## Good practice

- Evaluate the exported artifact at the intended size before approving it.
- Prefer fixing geometry and label placement before shrinking type.
- Escalate to critique if the chart is conceptually wrong.
- Escalate to fix/implementation if the chart is conceptually right but visually broken.

## Pitfalls

1. **Confusing evaluation with critique.** Evaluation asks “is this acceptable?”; critique asks “what should it become?”
2. **Checking only the code.** The rendered artifact is the source of truth.
3. **Ignoring delivery context.** A chart that works on a desktop preview may fail in Telegram, slides, or print.
4. **Forcing a send when the chart still needs geometry fixes.** If labels collide or the artboard is wrong, revise first.
5. **Overfitting to cosmetics.** If the chart form is wrong, no amount of label tweaking will save it.

## Verification checklist

- [ ] I inspected the actual rendered artifact
- [ ] I checked readability at the intended size
- [ ] I checked overlap, clipping, and whitespace
- [ ] I verified title/units/source/legend fit the chart
- [ ] I confirmed the chart form matches the question
- [ ] I gave a clear Send / Revise / Redesign verdict

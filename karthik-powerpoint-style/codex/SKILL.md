---
name: karthik-powerpoint-style
description: "Create, revise, or critique PowerPoint, teaching, and workshop slides in Karthik's style: plain titles (claims, labels, or questions, not crafted aphorisms), sparse chart-first layouts, direct labels, clean typography, minimal decoration, source notes, verbatim reuse of Karthik's own decks and blogs, facilitator cue-card patterns, and management-ready slide patterns for charts, scorecards, recommendations, and deck outlines."
metadata:
  short-description: Karthik PowerPoint style
  claude-description: "Create or critique analytical and teaching slides in Karthik's style: plain titles, sparse layouts, direct labels, minimal decoration, and facilitator cue-card workshop decks."
---

# Karthik PowerPoint Style

Use this skill when creating, revising, or critiquing presentation slides, especially analytical decks with charts, metrics, product narratives, consulting recommendations, or management updates.

Core job: make slides feel like interpreted analysis, not decorated reporting.

## Start from Karthik's own material

Before writing new slides on a topic, check whether Karthik's own decks, blogs, or notes already cover it.

- If they do, pull the actual slides or text **verbatim**. Do not paraphrase his material into fresh prose - the paraphrase reads as generic AI copy and throws away his examples, phrasing, and jokes.
- Reuse the **real images** from his decks, not text stand-ins for them. Extract embedded media from a `.pptx` (unzip it, look in `ppt/media/`) or the original file rather than describing or re-creating the picture.
- Keep his concrete cases intact - specific names, odd numbers, wry asides.

## Workflow

1. Write the one-sentence claim for each slide before designing it.
2. Choose the simplest evidence structure for that claim: chart, scorecard, table, timeline, comparison, or short argument.
3. Title the slide plainly (see Slide titles): state the finding in plain words, or use a plain concept label or a direct question - never a crafted aphorism.
4. Put the main evidence large and central; remove anything that does not support the claim.
5. Add only necessary context: timeframe, comparator, source, caveat, annotation, or next action.
6. Use direct labels and annotations so the slide can be understood without presenter narration.
7. Split crowded slides. Prefer two clear slides over one dense slide.

## Slide titles

Titles are plain. Use whichever fits:

- a plain concept label - "Normalisation", "Confirmation bias", "Agenda", "Keep open"
- a plain statement of the point - "Correlation does not imply causation"
- a direct question - "What is average?", "Compared to what?", "What should the chart do?"

A claim-first title states the finding in **plain words**. It is never a crafted one-liner. Do not write:

- clever aphorisms or maxims - "Analysis is never a straight line"
- "X, not Y" reveals - "What you take home isn't the chart"
- parallel or antithetical one-liners - "The machine does the work. You make the calls."
- rule-of-three headlines

Test: if the title could be a LinkedIn caption or a conference-talk tagline, it is wrong. When unsure, use the plainest label or question that names what the slide is about.

## Slide bodies

- Bodies are bullets or a single short line - never prose paragraphs, and never a "bold lead + explanation sentence" block.
- Trim to 3-5 points. Cut the sixth.
- No numbered academic procedures ("1. Name the source rows. 2. Write the formula...") - they read like a manual, not like Karthik talking.
- Use contractions, straight quotes, and hyphens (never em dashes).
- Some slides are deliberately blank and filled live from the room - leave them blank.

## Visual style

- Use white backgrounds by default.
- Use clean, sparse layouts with high data-ink ratio.
- Avoid decoration, gradients, shadows, stock art, icons, ornamental dividers, and busy borders.
- Use generous whitespace; do not fill the slide just because space exists.
- Use a quiet visual hierarchy: title, subtitle/kicker, main evidence, annotation, source.
- Use light grey for structure and context; use one accent colour for the story.
- Prefer direct labels over legends.
- Keep footers small and muted.

## Typography

- Prefer Aptos, Arial, Helvetica, or another clean sans-serif.
- Titles: 26-34 pt, bold.
- Subtitle/kicker: 11-16 pt, muted.
- Chart labels/body: 10-16 pt.
- Footnotes/sources: 7-9 pt, muted grey.
- Avoid all-caps except very short labels.
- Do not use more than two font weights on a slide.

## Colour palette

Use these defaults unless the project has a stronger domain palette:

- Text: `#111111`
- Body text: `#222222`
- Muted text: `#666666`
- Gridlines/rules: `#D9D9D9`
- Pale chart panel if needed: `#F7F7F4`
- Main accent blue: `#2F6BFF`
- Negative/red: `#C73E3A`
- Positive/green: `#2E8B57`
- Warning/amber: `#D99A2B`

## Slide patterns

### Chart slide

- Title: claim the chart proves.
- Kicker: timeframe, sample, or comparator.
- Main chart: large, with minimal gridlines.
- Annotation: label the key gap, inflection, outlier, threshold, or event.
- Footer: source and transformation notes.

Use `dataviz-selector` before choosing the chart form. Use `karthik-data-visualization` for chart styling.

### Recommendation slide

- Title: recommendation or decision.
- Left side: evidence or reason.
- Right side: implication, action, owner, or trade-off.
- Keep prose short; use bullets only when they are parallel and necessary.

### Scorecard slide

- Use when the viewer must scan several metrics.
- Prefer compact tables with sparklines or status markers over dashboard tiles.
- Include targets or previous-period values; never show numbers without comparators.

### Narrative section slide

- Use a short sentence that tees up the next section.
- Avoid decorative interstitials.
- If the section needs a visual, use a simple timeline, flow, or one-line argument.

### Workshop / facilitator cue-card slide

A teaching or workshop deck is a spine, not a script. During a hands-on exercise nothing is projected - the slide is the facilitator's cue card.

- The face carries only a plain title and a `time · artifact` anchor ("8 minutes · one paper sketch").
- Put all how-to detail, participant instructions, and things-to-watch-for in facilitator notes, not on the slide face.
- Do not write out step-by-step instructions the room never sees.

## Chart guardrails inside slides

- Never use pie charts, donut charts, 3D charts, gauges, radar/spider charts, or decorative infographic forms.
- Avoid dashboards as a substitute for interpretation.
- Bars start at zero.
- Maps are only for spatial stories.
- Do not use dual axes unless there is no defensible alternative; if used, label the caveat clearly.
- Do not rely on colour alone to explain meaning.

## Output expectations

When giving slide guidance, use this structure:

```markdown
Slide title: <claim>
Purpose: <what the viewer should conclude>
Layout: <chart/table/text arrangement>
Main evidence: <data or argument to show>
Annotation: <what to call out directly>
Style notes: <specific typography/colour/spacing guidance>
Avoid: <likely bad slide choices>
```

When creating a deck outline, list slides as claims, not topics.

---
name: dataviz-fix
description: Iteratively repair an uploaded or pasted data visualization, revise from feedback, then improve the owning dataviz skill from the accepted result.
---

# Dataviz Fix

Own the repair-and-learning loop:

```text
uploaded chart + optional context
→ diagnose
→ rebuild a real chart
→ inspect the export, revise or redesign
→ user feedback
→ revise until accepted
→ identify why the first result missed
→ make the narrowest reusable skill change
```

The user-facing loop matters more than a long critique. Return a chart early, then improve it from concrete feedback.

## Companion skills

Use the smallest relevant subset:

- `dataviz-critique`: diagnose question/data/visual failures and rank them by severity.
- `dataviz-selector`: keep or change the chart form.
- `karthik-data-visualization`: implement and inspect the visual.
- `chart-annotations`: decide what to mark and how to label it.
- The applicable installed writing or brand style skill: govern every title, subtitle, annotation, caption, and note. Do not treat prose inside a chart as exempt from the user's writing rules.
- `dataviz-eval`: only when the user asks for a formal audit or release verdict.
- `dataviz-orchestrator`: when source data or analysis must be rebuilt.
- `karthik-analysis-planner` and `karthik-data-cleaning`: only when definitions, grain, denominators, or data quality affect the repair.

For an open-ended repair or redesign, always load `dataviz-critique` and `dataviz-selector`; the source chart's title and form are hypotheses to test, not intent to preserve. For a narrow literal edit, use only the companion skills the named change needs.

## Repair loop

### 1. Read the input

- Inspect the actual image, not only OCR or an image description.
- Infer the intended comparison, audience, and medium when visible. Keep what the user said separate from what you inferred.
- Use source data/code when supplied. If it is absent, recover only legible values and mark them approximate.
- Preserve exact wording, units, order, and semantic mappings unless the redesign deliberately changes them.
- When the user says "only change X" or names things to keep, treat that as the edit boundary.

### 2. Diagnose and choose the intervention

Before choosing anything, decide what the chart must say and carry:

- The primary encoded dimension (what the stack, colour, or facets carry) is presumptively a key message. Collapsing a breakdown into a total drops it.
- Preserving the message is not preserving the form. When the source form is what makes a message hard to read, changing the form is the repair.
- Keep the source form when it is already a defensible answer. Replace it only when the new form is clearly more legible, never as a lateral swap between roughly equivalent forms.
- Hard to recover is not grounds to drop. Unreadable labels, approximate values, or too many categories call for a better form, not deleted data. Name anything you do drop and why.
- Interface chrome in a screenshot (tooltips, hover cards, crosshair readouts) is not part of the chart. Do not reproduce it.

Name internally:

- the apparent claim;
- the top three fatal/major issues, including any semantic ambiguity in measure, time context, universe or denominator, claim strength, or units;
- whether the right intervention is minimal repair, analytical redesign, or a different story lens;
- which companion skills are needed.

Do not give the full diagnosis unless asked. Use it to make the chart.

### 3. Rebuild a real artifact

- Produce a real PNG/SVG/PDF with reproducible R, Python, JavaScript, or editable vector code. Never return ASCII art, a text mockup, or advice instead of the repaired chart.
- Continue from the latest candidate and its code. Preserve every element that already works and change only what needs changing. Restart from the source only for a redesign.
- Make the literal requested change first. Do not retain or restore an element the user asked to remove. Touch an out-of-scope element only when the requested change forces it.
- If one fix applies to several panels, facets, rows, or series, apply it to every instance, not just the easiest one.
- Use exact data when available; never present estimated screenshot values as exact.

### 4. Inspect before sending

Render, then look at the exact exported file at delivery size. Check:

- the claim reads first, and nothing invites a materially different reading;
- every category stays identifiable and correctly bound to its marks;
- no clipping, collisions, or orphaned labels, including in the densest region, not just the overview;
- the closest pair of encoded colours stays distinct at delivery size and in grayscale;
- every title, label, and note follows the applicable writing or brand style skill.

Fix what fails and re-render. Prefer a local repair of a mechanical defect over reopening the design; return to `dataviz-critique` or `dataviz-selector` only when the form itself is wrong. Stop when the chart does its job; do not keep revising for taste.

### 5. Continue from feedback

Treat each user correction as evidence. Before editing, translate it into one observable change: the target, its current state, its required state. If the user corrects an earlier principle, drop the earlier instruction rather than accumulating a contradiction. Change the smallest relevant part of the latest candidate, render, and inspect the named element directly. Do not defend the earlier choice or repeat already accepted decisions.

Do not send progress-only replies. Every chart or revision response includes the image, plus no more than three short lines: what changed, and whether values are exact or approximate.

## Acceptance and skill learning

Treat clear phrases such as "this is right", "done", "final", or "accept" as acceptance. Do not edit any skill while the repair is still in progress; user feedback is evidence for the later diagnosis, not permission to patch skills mid-loop.

1. Compare the original, every output, the accepted output, and every user correction. One case may expose several distinct misses.
2. Classify the first-output miss:
   - `execution-miss`: an existing rule was clear but not followed;
   - `missing-rule`: no reusable rule covered the correction;
   - `ambiguous-rule`: wording allowed the wrong choice;
   - `conflicting-rule`: two skills pushed in different directions;
   - `tooling`: image handling, rendering, or delivery failed;
   - `input-data`: the needed evidence was absent.
3. Choose one owner per miss. Patch this skill only when sequencing or revision continuity caused it; patch the chart skill when the design principle itself was missing, ambiguous, or conflicting.
4. **Do not overfit.** Abstract the feedback one level above its example: describe the reader's mistaken mental model and the violated relationship between evidence, encoding, context, and claim. Do not turn nouns, numbers, chart types, or wording from one chart into a standing rule. Before committing a lesson, test it against at least two unrelated chart situations and remove any clause that only handles the originating example. Keep one-off chart preferences out of the skills. An execution miss that repeats despite a clear rule does not need another prose rule. An input-data miss needs no rule at all.
5. Make the smallest source change that would have produced the accepted result on the first attempt. Update both `codex/SKILL.md` and `claude/SKILL.md`.
6. Run `./sync.sh --no-pull --validate-only` in the source repo.

## Final accepted response

Return the accepted chart path, the miss classification and owning skill, and the exact skill files changed, or "no skill change" with the reason. Keep it under five lines unless the user asks for the diagnosis.

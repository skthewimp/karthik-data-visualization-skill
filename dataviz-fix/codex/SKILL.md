---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

Return an improved chart. The workflow exists to help produce an artifact, not to prevent one from reaching the user.

## Non-negotiable rule

**A valid rendered candidate must be delivered.** Missing review infrastructure, incomplete metadata, an unavailable independent reviewer, or an imperfect quality score must not suppress the best available output.

Label limitations honestly. Do not relabel an unreviewed candidate as approved, but do send it.

## Default workflow

### 1. Read the source

- Inspect the actual image or artifact.
- Identify the user’s requested change, visible data, units, labels, and obvious evidence limits.
- For a literal edit, preserve everything outside that edit unless a dependent adjustment is necessary.
- For an open-ended repair, make a short internal diagnosis and choose the smallest useful redesign.

Load `dataviz-critique`, `karthik-data-visualization`, and the applicable writing or brand skill. Load `dataviz-selector` only when the chart form is genuinely in question. Do not load `dataviz-eval` by default.

Do not create a structured critique, design contract, semantic preflight, plan audit, case record, or review packet unless the user explicitly asks for an audited workflow or the task is unusually high risk.

### 2. Build one real artifact

- Produce a PNG, SVG, or PDF with reproducible R, Python, JavaScript, or editable vector code.
- Use exact values when supplied. Mark screenshot-derived values as approximate unless they are clearly printed source labels.
- Keep source wording, units, periods, categories, and mappings unless the repair deliberately changes them.
- Apply the user’s writing or brand style to chart copy.

Use the project’s existing renderer when one exists. For a new static chart, prefer ggplot2 when available, but do not delay the output to satisfy a renderer preference.

### 3. Inspect once before delivery

Inspect the exact exported artifact at its delivery size. Check:

- clipping and collisions;
- text legibility;
- label-to-mark association;
- missing categories, periods, or units;
- obvious colour or contrast failures.

Use `render_and_inspect_chart` when available. If the MCP tool fails, use the local renderer directly and visually inspect the result. State that deterministic inspection was unavailable. Never invent layout metadata or claim that incomplete checks are complete.

Fix obvious mechanical defects before sending. This inspection is a practical self-check, not a release bureaucracy.

### 4. Deliver the best candidate

Send the artifact after the first sound build. Do not wait for an independent review.

If one major visible defect remains, make one more build. The default autonomous limit is:

- two rendered candidates; or
- ten elapsed minutes;

whichever comes first.

At the limit, send the strongest valid candidate and name the unresolved issue in one sentence. A partially improved chart is more useful than no chart.

### 5. Continue from user feedback

Treat user feedback as the main release signal. Change the smallest relevant part of the latest candidate, render again, inspect the named element, and return the changed artifact.

Do not restart from the source unless the user asks for a redesign or the current form cannot support the requested change.

## When independent evaluation is worth the time

Use a fresh `dataviz-eval` reviewer only when:

- the user requests independent evaluation;
- a materially misleading claim may survive visual polish;
- the repair is a major redesign with consequential evidence decisions; or
- the task is a benchmark of the chart-producing system.

The review informs the next revision. It does not block delivery of the current valid artifact.

## Optional case logging

Use `case_manager.py` only when the user wants an audit trail, comparison history, bounded benchmark, or reusable learning record. The case state never overrides the output-first rule: if a valid artifact exists, deliver it with its actual status.

When case logging is used, keep it minimal:

1. Start the case.
2. Record each rendered artifact.
3. Attach real inspection evidence when available.
4. Record user feedback and acceptance.

Do not require the user-facing repair to wait for contracts, blind-response freezes, or every optional gate.

## Failure handling

- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic inspection.
- **Reviewer failure:** deliver the inspected candidate as unreviewed.
- **Budget reached:** deliver the best candidate with one unresolved-issue line.
- **Renderer failure with no artifact:** report the concrete error and return any earlier valid candidate.
- **Missing evidence:** preserve visible source values, avoid invented claims, and label the limitation.

## Response format

Attach the exact artifact and use no more than three short lines:

1. What changed.
2. Whether values are exact, transcribed, or approximate.
3. Whether deterministic inspection completed; if not, say what fallback check was used.

## Learning after acceptance

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule or tool defect. Do not add another gate for a one-off mistake. Prefer simplifying or repairing the failing step over adding prose, schemas, or tests.

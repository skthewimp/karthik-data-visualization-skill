---
name: dataviz-fix
description: Iteratively repair an uploaded or pasted data visualization, keep every revision and user correction, and use the accepted result to diagnose and fix the owning dataviz skill.
---

# Dataviz Fix

Own the complete repair-and-learning loop:

```text
uploaded chart + optional context
→ diagnose
→ rebuild a real chart
→ inspect
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
- `dataviz-eval`: decide whether the rendered chart is ready, needs revision, or needs redesign.
- `karthik-data-visualization`: implement and inspect the visual.
- `chart-annotations`: decide what to mark and how to label it.
- `dataviz-orchestrator`: use when source data or analysis must be rebuilt.
- `karthik-analysis-planner` and `karthik-data-cleaning`: use only when definitions, grain, denominators, or data quality affect the repair.

Do not load every companion skill automatically. Choose by failure mode.

## Case log

Persist each example so the accepted result can teach the skills. Use:

```bash
python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py <command> ...
```

Set `DATAVIZ_FIX_ROOT` to override the default case directory. Pass a stable session id with `--session` when available.

### Start a case

On the first chart in a repair conversation:

```bash
python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py start \
  --session "<session-id>" \
  --image "/absolute/path/to/input.png" \
  --request "<user request>" \
  --skills-root "/path/to/karthik-data-visualization-skill"
```

Do this before editing. The command copies the original and snapshots skill hashes.

After every rendered revision:

```bash
python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py iterate \
  --session "<session-id>" \
  --output "/absolute/path/to/revision.png" \
  --summary "<what changed>"
```

Before acting on user feedback:

```bash
python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py feedback \
  --session "<session-id>" \
  --text "<user feedback verbatim>"
```

## Repair loop

### 1. Read the input

- Inspect the actual image, not only OCR or an image description.
- Infer the intended comparison, audience, and medium when visible.
- Use source data/code when supplied. If it is absent, recover only legible values and mark them approximate.
- Preserve exact wording, units, order, and semantic mappings unless the redesign deliberately changes them.

### 2. Diagnose and choose the intervention

Name internally:

- the apparent claim;
- the top three fatal/major issues;
- whether the right intervention is minimal repair, analytical redesign, or a different story lens;
- which companion skills are needed.

Do not give the full diagnosis unless asked. Use it to make the chart.

### 3. Rebuild a real artifact

- Produce a real PNG/SVG/PDF with reproducible R, Python, JavaScript, or editable vector code.
- Never return ASCII art, a text-only mockup, or advice instead of the repaired chart.
- Prefer editing the same chart code across revisions instead of restarting.
- Use exact data when available; never present estimated screenshot values as exact.
- Save code and outputs inside the active case directory when feasible.

### 4. Inspect before sending

This is an inspect → revise → render loop: inspect the rendered artifact, fix the issue, re-render, and inspect again before sending. Stop only when the output is acceptable or you have hit the cycle limit.

Inspect the rendered artifact. Check:

- the main comparison is visible within five seconds;
- title, units, dates, source, and caveats are legible;
- labels do not overlap or clip;
- ordering, baselines, scales, and direct labels are correct;
- colours remain distinct after chat compression;
- the output works at the intended display size.

Revise before sending if a fatal or major issue remains. Limit autonomous build-inspect cycles to three; user feedback starts a new cycle.

### 5. Continue from feedback

Treat each user correction as evidence. Log it verbatim, change the smallest relevant part, render, inspect, and record the new output. Do not defend the earlier choice or repeat already accepted decisions.

Send the image plus no more than three short lines: what changed, whether values are exact or approximate, and the artifact path/media tag required by the interface.

## Acceptance and skill learning

Treat clear phrases such as “this is right”, “done”, “final”, “happy with this”, or “accept” as acceptance. Then:

1. Record acceptance:

   ```bash
   python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py accept \
     --session "<session-id>"
   ```

2. Compare the original, first output, accepted output, and every user correction.
3. Classify the first-output miss:
   - `execution-miss`: an existing rule was clear but not followed;
   - `missing-rule`: no reusable rule covered the correction;
   - `ambiguous-rule`: wording allowed the wrong choice;
   - `conflicting-rule`: two skills pushed in different directions;
   - `tooling`: image handling, rendering, inspection, or delivery failed;
   - `input-data`: the needed evidence was absent.
4. Choose one owning skill. Patch the umbrella `dataviz-fix` skill only when sequencing, logging, revision, or acceptance caused the miss.
5. Change a skill only when the correction is reusable across future charts. Do not encode one chart's wording, colours, values, or layout as a general rule.
6. Make the smallest source change that would have produced the accepted result on the first attempt. Update both `codex/SKILL.md` and `claude/SKILL.md`; update a shared reference only when detailed guidance belongs there.
7. Validate the repo. Do not commit or push unless the user explicitly asks.
8. Record the diagnosis:

   ```bash
   python3 ~/.codex/skills/dataviz-fix/scripts/case_manager.py diagnose \
     --session "<session-id>" \
     --classification "<classification>" \
     --owner "<skill-name or none>" \
     --lesson "<reusable lesson>" \
     --changed-files "<comma-separated paths or none>"
   ```

If the miss is `execution-miss` or `input-data`, usually do not change a skill. Record why. More rules do not fix non-compliance or missing evidence.

## Final accepted response

Return:

- accepted chart path;
- case/review-packet path;
- miss classification and owning skill;
- exact skill files changed, or “no skill change” with the reason.

Keep this under six lines unless the user asks for the diagnosis.

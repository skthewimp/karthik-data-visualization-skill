---
name: dataviz-fix
description: Iteratively repair an uploaded or pasted data visualization, preserve revisions and feedback, then improve the owning dataviz skill from the accepted result.
---

# Dataviz Fix

Own the complete repair-and-learning loop:

```text
uploaded chart + optional context
→ diagnose
→ rebuild a real chart
→ run the `dataviz-eval` artifact gate
→ revise or redesign until the gate says `Send`
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
- `dataviz-eval`: run the required artifact gate after every render and return the minimum pass set.
- `karthik-data-visualization`: implement and inspect the visual.
- `chart-annotations`: decide what to mark and how to label it.
- `dataviz-orchestrator`: use when source data or analysis must be rebuilt.
- `karthik-analysis-planner` and `karthik-data-cleaning`: use only when definitions, grain, denominators, or data quality affect the repair.

Always load `dataviz-eval` for the rendered-artifact gate. Choose the other companion skills by failure mode.

## Case log

Persist each example so the accepted result can teach the skills. Hermes expands `${HERMES_SKILL_DIR}` to this installed skill directory. Use:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" <command> ...
```

Set `DATAVIZ_FIX_ROOT` to override the default case directory. Always pass `${HERMES_SESSION_ID}` as the session id.

### Start a case

On the first chart in a repair conversation:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" start \
  --session "${HERMES_SESSION_ID}" \
  --image "/absolute/path/to/input.png" \
  --request "<user request>" \
  --audience "<intended audience or inferred audience>" \
  --medium "<delivery medium and viewing condition>" \
  --creator "main:${HERMES_SESSION_ID}" \
  --skills-root "/home/karthik/.hermes/skills/data-science"
```

Do this before editing. The command copies the original and snapshots the installed skills actually used by Hermes.

After every rendered revision:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" iterate \
  --session "${HERMES_SESSION_ID}" \
  --output "/absolute/path/to/revision.png" \
  --summary "<what changed>"
```

The creator must not grade its own export. After `iterate`, use a fresh leaf reviewer through Hermes `delegate_task` with `file`, `terminal`, and `vision` tools. Give it only:

- the recorded artifact and original/source paths;
- the user request, audience, medium, and active acceptance checks;
- the installed `dataviz-eval` skill path;
- a destination for its JSON report.

Do not pass the creator's diagnosis, intended verdict, claimed fixes, or rendering code. Generate the bounded review packet and response template:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" review-request \
  --session "${HERMES_SESSION_ID}"
```

Pass only the returned blind-request path to the reviewer. It must inspect the exact artifact with `vision_analyze`, save its blind reads, then run the packet's `blind_submit_command`. That command freezes the blind response and creates the intent reveal; the reveal does not exist beforehand. The same reviewer then opens it and completes the response template. The creator may verify and record the report, but may not author or amend it. Use the delegate task's real identifier as `reviewer`; the case manager rejects the creator identity and any blind response changed after reveal.

Persist that independent report before sending:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" evaluate \
  --session "${HERMES_SESSION_ID}" \
  --report "/absolute/path/to/independent-review.json"
```

The report must identify the reviewer and exact artifact hash; include expert and audience blind reads; mark which gates are required by the declared scope; give evidence for all six gates and five general release checks; and state verdict, failure codes, and required actions. The case manager rejects `Send` unless every required gate and release check passes. A non-required gate stays `Unknown`; it is never converted to a fake pass. If independent review is unavailable, the artifact is `Not evaluable`, not self-approved.

Before acting on user feedback:

```bash
python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" feedback \
  --session "${HERMES_SESSION_ID}" \
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
- Treat HTML as rendering source only. Export and record the exact PNG, JPEG, SVG, or PDF that the interface will attach.
- Never return ASCII art, a text-only mockup, or advice instead of the repaired chart.
- Prefer editing the same chart code across revisions instead of restarting.
- Use exact data when available; never present estimated screenshot values as exact.
- Save code and outputs inside the active case directory when feasible.

### 4. Inspect before sending

This is a render → independent evaluate → revise loop. Use the full `dataviz-eval` artifact-gate protocol on the actual recorded export, including its expert read, audience read, evidence scope, six gates, five release checks, verdict, failure codes, and minimum pass set. Keep the long evaluation internal unless the user asks for it.

The release checks are generic, not chart-specific:

- **Visual integrity:** no collision, clipping, truncation, occlusion, or broken geometry.
- **Relationship traceability:** the identification system fits the chart's density and geometry; each label, value, mark, legend entry, and annotation pairs with what it describes without guesswork. The intended label-mark bond must be perceptually stronger than competing nearby relationships; shared-row alignment alone does not bridge blank space. Direct labels are preferred only when they stay legible and close to their targets; otherwise use an axis, legend, grouping, small multiples, or another structure.
- **Spatial economy:** whitespace and aspect ratio support grouping and hierarchy rather than separating related elements or wasting the delivery surface.
- **Encoding semantics:** every salient colour, size, shape, order, and highlight has a recoverable data or narrative role.
- **Delivery robustness:** the exact export survives the intended display size and compression.

Do not replace these principles with chart names, preferred palettes, fixed pixel limits, or thresholds learned from one failed example. Use the failed examples as regression tests only.

This gate covers static rendered deliverables. Keep editable code, slides, or HTML when useful, but record and review the exported PNG, JPEG, SVG, or PDF the user will actually receive.

Follow the verdict:

- `Send`: persist the evaluation, then show the candidate to the user.
- `Revise`: apply only the minimum pass set, record a new iteration, and evaluate again.
- `Redesign`: return to `dataviz-critique` or `dataviz-selector`, rebuild, then evaluate again.
- `Not evaluable`: obtain the missing artifact, evidence, or delivery condition when required; never present the candidate as approved.

Limit autonomous render-evaluate cycles to three; user feedback starts a new cycle. After the third non-`Send` result, show the best candidate with the unresolved gate stated plainly instead of looping silently.

### 5. Continue from feedback

Treat each user correction as evidence. Before editing, translate it into one observable check: target, current state, required state. Log it verbatim, change the smallest relevant part, render, record the media iteration, and run `dataviz-eval` with that check in the evaluation packet. Inspect the named element directly; do not infer success from a generic chart summary. Do not defend the earlier choice or repeat already accepted decisions.

Do not send progress-only replies such as “I’ll fix it” or “now checking”. Use tools silently until a candidate is ready. Every chart or revision response must include the media attachment in the same response, plus no more than three short lines: what changed, whether values are exact or approximate, and `MEDIA:/absolute/path/to/output.png`. If the user asks where the graph is, return the media line immediately.

## Acceptance and skill learning

Treat clear phrases such as “this is right”, “done”, “final”, “happy with this”, or “accept” as acceptance. Then:

Do not edit any skill while the case is active. Finish the chart and obtain acceptance first. User feedback is evidence for the later diagnosis, not permission to patch source files mid-loop.

1. Record acceptance. If the independent verdict is not `Send`, use `--override-reason` only when the user has explicitly accepted that exact artifact; the case remains visibly `accepted_with_override`.

   ```bash
   python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" accept \
     --session "${HERMES_SESSION_ID}"
   ```

2. Compare the original, first output, accepted output, and every user correction.
   Include the recorded verdicts, failed gates, failure codes, and required actions. User acceptance remains authoritative even when the evaluator recorded a concern.
3. Classify the first-output miss:
   - `execution-miss`: an existing rule was clear but not followed;
   - `missing-rule`: no reusable rule covered the correction;
   - `ambiguous-rule`: wording allowed the wrong choice;
   - `conflicting-rule`: two skills pushed in different directions;
   - `tooling`: image handling, rendering, inspection, or delivery failed;
   - `input-data`: the needed evidence was absent.
4. Choose one owning skill. Patch the umbrella `dataviz-fix` skill only when sequencing, logging, revision, or acceptance caused the miss.
   Put chart-design rules in the owning chart skill, not in this umbrella checklist.
5. Change a skill only when the correction is reusable across future charts. Do not encode one chart's wording, colours, values, or layout as a general rule.
6. Make the smallest source change that would have produced the accepted result on the first attempt. Update both `codex/SKILL.md` and `claude/SKILL.md`; update a shared reference only when detailed guidance belongs there.
7. Run `./sync.sh --no-pull --validate-only` in the source repo. Do not commit or push unless the user explicitly asks.
8. Record the diagnosis:

   ```bash
   python3 "${HERMES_SKILL_DIR}/scripts/case_manager.py" diagnose \
     --session "${HERMES_SESSION_ID}" \
     --classification "<classification>" \
     --owner "<skill-name or none>" \
     --lesson "<reusable lesson>" \
     --changed-files "<comma-separated paths or none>"
   ```

If the miss is `execution-miss` or `input-data`, usually do not change a skill. Record why. More rules do not fix non-compliance or missing evidence.

## Final accepted response

Return:

- `MEDIA:` for the accepted media artifact;
- accepted chart path;
- case/review-packet path;
- miss classification and owning skill;
- exact skill files changed, or “no skill change” with the reason.

Keep this under six lines unless the user asks for the diagnosis.

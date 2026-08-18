---
name: dataviz-fix
description: Iteratively repair an uploaded or pasted data visualization, preserve revisions and feedback, then improve the owning dataviz skill from the accepted result.
---

# Dataviz Fix

Own the complete repair-and-learning loop:

```text
source chart
→ `dataviz-critique` on the original artifact
→ attach the structured critique and implementation contract
→ build
→ render and deterministic inspection
→ independent `dataviz-eval`
→ `Revise` from the latest candidate or `Redesign` from the underlying evidence
→ render, inspect, and independently evaluate again
→ repeat until `Send`
→ user review
→ re-enter implementation for every rejected or corrected result
→ accepted
→ record reusable lessons for later repository maintenance
```

Do not skip, merge, or reorder these handoffs. `Send` ends the autonomous evaluation loop; only explicit user acceptance completes the case.

## Companion skills

Use the smallest relevant subset:

- `dataviz-critique`: diagnose question/data/visual failures and rank them by severity.
- `dataviz-selector`: keep or change the chart form.
- `dataviz-eval`: run the required artifact gate after every render and return the minimum pass set.
- `karthik-data-visualization`: implement and inspect the visual.
- The applicable installed writing or brand style skill: govern every title, subtitle, annotation, caption, and note. In Karthik's environment, this is `karthik-writing-style`.
- `chart-annotations`: decide what to mark and how to label it.
- `dataviz-orchestrator`: use when source data or analysis must be rebuilt.
- `karthik-analysis-planner` and `karthik-data-cleaning`: use only when definitions, grain, denominators, or data quality affect the repair.

Always load `dataviz-critique`, `karthik-data-visualization`, and `dataviz-eval`, including for an apparently narrow literal edit. The initial critique is a required implementation contract, not optional advice. Load `dataviz-selector` whenever that critique questions the form and after every `Redesign` verdict. Always load an applicable installed writing or brand style skill before drafting reader-facing chart copy. Do not treat prose inside a chart as exempt from the user's writing rules.

## Case log

Persist each example so the accepted result can teach the skills. Resolve these placeholders once and substitute their literal values in every command:

- `CASE_MANAGER`: `"${CODEX_HOME:-$HOME/.codex}/skills/dataviz-fix/scripts/case_manager.py"` in Codex; `"$HOME/.claude/skills/dataviz-fix/scripts/case_manager.py"` in Claude Code; `"${HERMES_SKILL_DIR}/scripts/case_manager.py"` in Hermes.
- `SKILLS_ROOT`: the matching `skills` directory, or the parent of `${HERMES_SKILL_DIR}`.
- `CASE_SESSION`: the runtime session id when one exists; otherwise generate one stable UUID for this conversation.

Set `DATAVIZ_FIX_ROOT` to override the default case directory. After `start`, retain the returned `case_id` as `CASE_ID` and use `--case "${CASE_ID}"` for every later command. Do not rely on shell variables surviving across tool calls.

### Start a case

On the first chart in a repair conversation:

```bash
python3 "${CASE_MANAGER}" start \
  --session "${CASE_SESSION}" \
  --image "/absolute/path/to/input.png" \
  --request "<user request>" \
  --audience "<user-supplied audience, or omit>" \
  --purpose "<decision or purpose, or omit>" \
  --question "<analytical question, or omit>" \
  --hypothesis "<hypothesis, or omit>" \
  --message "<intended message, or omit>" \
  --medium "<delivery medium, or omit>" \
  --creator "main:${CASE_SESSION}" \
  --context-source user \
  --skills-root "${SKILLS_ROOT}"
```

Pass `--context-source user` only when every structured intake field in that command was explicitly supplied by the user. The default is `inferred`. Do not upgrade a paraphrase of the source title or the creator's proposed story to user intent.

Do this before editing. The command copies the original, snapshots the installed skills, records context version 1, and creates a bounded loop. It defaults to three autonomous iterations. Use `--max-elapsed-minutes`, `--max-tokens`, or `--max-cost-usd` when another hard budget matters.

Turn the request into a change contract before the first build. Record each concrete requested change as an intake check:

```bash
python3 "${CASE_MANAGER}" check \
  --case "${CASE_ID}" \
  --kind change \
  --text "<user request verbatim>" \
  --target "<element or relationship>" \
  --current "<observable source state>" \
  --required "<observable delivered state>" \
  --why "<reader consequence>"
```

When the user says “only change X”, “keep the rest”, or names elements to preserve, pass that wording through `--preserve` at `start`. The case manager converts it into a required preservation check. Do not leave a literal edit instruction only inside the free-text request: the reviewer cannot enforce prose that was never made a check.

Expand the check across repeated structures before rendering. If one legend, axis, annotation rule, or encoding applies to several panels, facets, rows, or series, name the expected instance count and location in `--required`. Do not treat a successful edit in one panel as completion for the whole chart.

Do not put inferred context into user-supplied fields. Record it separately:

```bash
python3 "${CASE_MANAGER}" context \
  --case "${CASE_ID}" \
  --source inferred \
  --audience "<inferred audience>" \
  --purpose "<inferred purpose>" \
  --reason "Inferred from the supplied chart and conversation"
```

Use `context` whenever the user adds or changes the audience, purpose, question, hypothesis, message, medium, dimensions, source notes, preservation requirements, accessibility, brand, tooling, or output constraints. `--text` accepts an ordinary free-text prompt. Each material change creates a new context version, cancels an in-flight stale review, and supersedes an old verdict. An identical update creates no new version.

Before any implementation, run `dataviz-critique` on the original artifact and save its structured repair brief. It must state the apparent question and claim, evidence limitations, fatal/major/minor findings, exactly three highest-consequence finding ids, misleading and defensible interpretations, repair/redesign decision, observable delivered outcomes, preservation requirements, and whether the form is questioned. Attach it:

```bash
python3 "${CASE_MANAGER}" critique \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/critique.json"
```

Create the first implementation contract with `karthik-data-visualization`. Map every fatal and major finding id to a planned change, affected zones, and observable outcome. Also record measure/evidence scope, chart form, primary identification route, title/subtitle/legend/plot/annotation/footer zones, colour role, delivery dimensions/aspect ratio, and exact/approximate value status. If the critique questions the form or chooses redesign, include the `dataviz-selector` decision. Attach it:

```bash
python3 "${CASE_MANAGER}" design-contract \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/design-contract.json"
```

Probe renderers before building. An explicit user renderer wins; otherwise choose ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available and the adapter supports the requested static output. Record the complete probe, whether ggplot2 supports this source/output, the selected renderer, and any fallback reason:

```bash
python3 "${CASE_MANAGER}" renderer-selection \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/renderer-selection.json"
```

An unexplained Matplotlib selection is invalid when an `auto` probe reports usable ggplot2 support.

Before the first render under each context version, save a five-part semantic preflight as JSON:

```json
{
  "context_version": 1,
  "dimensions": {
    "measure": {"result": "clear|repair|unknown", "observed": "...", "risk": "...", "required": "..."},
    "time_context": {"result": "clear|repair|unknown", "observed": "...", "risk": "...", "required": "..."},
    "universe_denominator": {"result": "clear|repair|unknown", "observed": "...", "risk": "...", "required": "..."},
    "claim_strength": {"result": "clear|repair|unknown", "observed": "...", "risk": "...", "required": "..."},
    "audience_units": {"result": "clear|repair|unknown", "observed": "...", "risk": "...", "required": "..."}
  }
}
```

Each `required` value must describe an observable delivered state, not a preferred chart type or wording. `clear` still needs observed evidence and a concrete no-regression state. Record it, then run the build check:

```bash
python3 "${CASE_MANAGER}" semantic-preflight \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/semantic-preflight.json"

python3 "${CASE_MANAGER}" build-check \
  --case "${CASE_ID}"
```

**Repair preflight:** carry every fatal and major critique finding into the design contract; translate every named user correction into an observable acceptance check. Use `dataviz-eval` for release criteria; this skill owns recording and sequencing, not redefining them.

Do not start the build if this preflight stops the case. Record the completed artifact with `iterate` after rendering even if that call crossed a budget; the budget controls the next build, not preservation or independent review of work already done.

For static repairs, call the backend-neutral `render_and_inspect_chart(source_path, output_dir, renderer="auto", delivery_profile, dimensions)` capability when available. It chooses ggplot2 first, renders through `ragg`, and emits the artifact, chart specification, layout metadata, inspection, review views, and manifest. Use Matplotlib only for an explicit requirement or a recorded unavailable/unsupported ggplot2 condition.

After every rendered revision, record the exact artifact and matching bundle:

```bash
python3 "${CASE_MANAGER}" iterate \
  --case "${CASE_ID}" \
  --output "/absolute/path/to/revision.png" \
  --summary "<what changed>"
```

When the renderer emits a matching bundle, add `--bundle-manifest "/absolute/path/to/manifest.json"`. Then run the available deterministic inspection capability on the recorded artifact and attach its report before `review-request`:

```bash
python3 "${CASE_MANAGER}" inspect \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/inspection.json"
```

Inspection is mandatory, not best effort. The case manager rejects review without an artifact-hash-matched inspection and automatically compares it with the preceding inspected iteration, preserving introduced, persistent, and resolved defects.

The creator must not grade its own export. After `iterate`, use a fresh leaf reviewer through Hermes `delegate_task` with `file`, `terminal`, and `vision` tools. Give it only:

- the recorded artifact and original/source paths;
- the installed `dataviz-eval` skill path;
- the blind-request path returned by `review-request`.

Do not pass the creator's diagnosis, intended verdict, claimed fixes, or rendering code. Generate the bounded review packet and response template:

```bash
python3 "${CASE_MANAGER}" review-request \
  --case "${CASE_ID}"
```

Pass only the returned blind-request path to the reviewer. It must inspect the exact artifact with `vision_analyze`, save its narrative blind reads plus the five structured semantic readings, then run the packet's `blind_submit_command`. That command freezes the blind response and creates the intent reveal; the reveal does not exist beforehand. The same reviewer then opens it and completes the response template without rewriting those frozen fields. The creator may verify and record the report, but may not author or amend it. Use the delegate task's real identifier as `reviewer`; the case manager rejects the creator identity and any blind response changed after reveal.

Persist that independent report before sending:

```bash
python3 "${CASE_MANAGER}" evaluate \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/independent-review.json"
```

The report must identify the reviewer and exact artifact hash; include expert and audience blind reads; independently recheck all five semantic dimensions; mark which gates are required by the declared scope; give evidence for all six gates and five general release checks; and state verdict, failure codes, and required actions. The creator's semantic preflight is a hypothesis, not evidence. The case manager rejects `Send` unless every semantic check, required gate, and release check passes. A non-required gate stays `Unknown`; it is never converted to a fake pass. If independent review is unavailable, the artifact is `Not evaluable`, not self-approved.

Record provider usage after creator and reviewer calls when the API or runtime exposes it:

```bash
python3 "${CASE_MANAGER}" usage \
  --case "${CASE_ID}" \
  --stage creator \
  --iteration 1 \
  --input-tokens 10000 \
  --output-tokens 2000 \
  --cached-input-tokens 50000 \
  --cost-usd 0.12 \
  --latency-seconds 45
```

The case records calls, tokens, cost, and latency. Before another build, it enforces the configured iteration, time, token, and cost limits. `limits` with no values only reports the current budget; tightening a limit needs no authorization. Increasing any existing limit requires a single-use, case-bound authorization grant recorded by the runtime from an explicit user turn. A reason string, inferred consent, or a creator-authored note is not authorization. Use the exact grant id and approved values supplied by the runtime, then resume separately:

```bash
python3 "${CASE_MANAGER}" limits \
  --case "${CASE_ID}" \
  --max-iterations 4 \
  --authorization "<case-bound grant id>"

python3 "${CASE_MANAGER}" resume \
  --case "${CASE_ID}" \
  --reason "User explicitly approved the recorded bounded increase"
```

The grant does not resume the case, cannot be reused, and must exactly match every increased limit. Each approved increase remains in `limit_changes` and links back to its user-turn authorization. Never ask for or manufacture a grant merely to finish a run.

Before acting on user feedback:

```bash
python3 "${CASE_MANAGER}" feedback \
  --case "${CASE_ID}" \
  --text "<user feedback verbatim>" \
  --target "<element or relationship>" \
  --current "<observable current state>" \
  --required "<observable required state>" \
  --why "<reader consequence>"
```

If later feedback clarifies or reverses an earlier check, add `--supersedes "<feedback number>"`. If it overrides a carried evaluator action, add `--supersedes-actions "<action id>"` using the open ids shown by `status`. User corrections outrank reviewer preferences. Do not leave contradictory gates active or silently rewrite history.

Before every `Revise` build, attach a revision contract whose `changes` map every open evaluator action id and every new user-check id to a planned change, affected zones, and observable outcome:

```bash
python3 "${CASE_MANAGER}" revision-contract \
  --case "${CASE_ID}" \
  --report "/absolute/path/to/revision-contract.json"
```

Apply the evaluator's complete minimum pass set to the latest candidate and its generating code. Do not reopen passing decisions or rebuild from the source during `Revise`. After `Redesign`, rerun `dataviz-critique`, run `dataviz-selector` when the form is implicated, create a new design contract, and rebuild from the underlying evidence rather than the failed candidate.

## Repair loop

### 1. Read the input

- Inspect the actual image, not only OCR or an image description.
- Infer the intended comparison, audience, and medium when visible.
- Use source data/code when supplied. If it is absent, recover only legible values and mark them approximate.
- Preserve exact wording, units, order, and semantic mappings unless the redesign deliberately changes them.

### 2. Diagnose and choose the intervention

Use the attached critique brief as the first implementation contract. The first implementation must address every fatal and major finding, not only the easiest three. Do not substitute a fresh informal diagnosis after the contract has been recorded.

### 3. Rebuild a real artifact

- Produce a real PNG/SVG/PDF with reproducible R, Python, JavaScript, or editable vector code.
- Treat HTML as rendering source only. Export and record the exact PNG, JPEG, SVG, or PDF that the interface will attach.
- Never return ASCII art, a text-only mockup, or advice instead of the repaired chart.
- Continue from the latest candidate and its generating code. Preserve every element that already passes and change only the current minimum pass set. Restart from the source only after a `Redesign` verdict; a routine `Revise` is not permission to discard prior work.
- Treat the active change and preservation checks as the edit boundary. Make the literal requested change first. Do not retain, restore, or substitute an element the user explicitly asked to remove. Adjust an out-of-scope element only when the requested change makes that dependent adjustment unavoidable; record the reason.
- An unchanged or perceptually unchanged artifact cannot satisfy an active correction. Reusing an artifact is valid only when no active user check or unresolved evaluator action requires a change.
- Use exact data when available; never present estimated screenshot values as exact.
- Save code and outputs inside the active case directory when feasible.
- Apply the installed writing or brand style skill to every reader-facing phrase. Factual accuracy does not excuse generic AI copy or a voice mismatch.

### 4. Inspect before sending

This is a render → independent evaluate → revise loop. Invoke `dataviz-eval` on the actual recorded export for expert/audience reads, evidence scope, gates, release checks, presentation checks, verdict, and minimum pass set. Keep the long evaluation internal unless the user asks for it.

Two presentation checks are mandatory for every new iteration:

- **Colour distinction:** inspect the closest pair of competing encoded colours at delivery size, in grayscale, and under common colour-vision deficiencies. A named palette, brand match, or claim that colours “look distinct” is not evidence. A chart with no competing encoded colours may pass only with that fact recorded.
- **Copy style:** inspect titles, subtitles, annotations, captions, and notes against the applicable installed writing or brand style skill. If none applies, use plain, specific, evidence-bounded prose. Accurate but generic AI phrasing does not pass.

The independent reviewer records both checks with a result, direct evidence, and a stress test. `Send` requires both to pass.

Before requesting the independent review, use any available deterministic artifact-inspection capability on the exact recorded export and preserve its artifact-bound report with the iteration. Pass known mechanical defects into the review and minimum pass set. On `Revise`, repair them before reopening higher-level design choices and keep unrelated passing regions unchanged; do not treat a collision or clipping report as permission to redesign the chart. If inspection coverage is incomplete, record the missing geometry evidence instead of converting it into a pass.

Every unresolved required action from one evaluation remains active in the next revealed review. Every active, non-superseded user acceptance check is also a first-class release gate with its own id, result, and direct evidence. A later overall gate cannot silently erase either. `Send` is invalid until every carried action and user check explicitly passes.

For a narrow repair, the gate is scope-aware. Judge the requested and changed regions against the full quality standard. In untouched regions, test preservation and regression against the source or latest accepted candidate. Record an unchanged pre-existing defect outside the authorized scope as a baseline concern; do not turn it into a required action unless it blocks the requested correction or leaves the delivered chart materially misleading. A reviewer action may not conflict with an active user check.

Review the exact export in at least three ways when available: the full artifact, a representative delivery-size preview, and deterministic overlapping detail views. A clean overview cannot overrule a collision, weak association, or mapping error in a dense local region.

The independent evaluator owns the release checks and their evidence. The repair case must carry every unresolved action forward, verify that every active user check is explicitly reported, and reject self-approval; it must not copy the evaluator's detailed criteria into this workflow.

Do not replace these principles with chart names, preferred palettes, fixed pixel limits, or thresholds learned from one failed example. Use the failed examples as regression tests only.

This gate covers static rendered deliverables. Keep editable code, slides, or HTML when useful, but record and review the exported PNG, JPEG, SVG, or PDF the user will actually receive.

Follow the verdict:

- `Send`: persist the evaluation, then show the candidate to the user.
- `Revise`: apply the evaluator's complete minimum pass set to the latest candidate, record a new iteration, and evaluate again.
- `Redesign`: rerun `dataviz-critique` and, when form is implicated, `dataviz-selector`; attach a new design contract, rebuild from underlying evidence, inspect, and evaluate again.
- `Not evaluable`: obtain the missing artifact, evidence, or delivery condition when required; never present the candidate as approved.

Obey the recorded state. `Revise` and `Redesign` permit another bounded build. `Send` moves to `user_review`; it is not final until the user accepts it. `Not evaluable` becomes `blocked`. Reworded but semantically equivalent evaluator actions retain one action id, and recurring equivalent failure codes/gate outcomes advance the stall counter until the case blocks for `no_progress`; genuinely distinct actions remain separate. Exhausted iteration, time, token, or cost budgets become `stopped`. In either paused state, preserve and report the best candidate plus every unresolved critique finding, user check, evaluator action, semantic check, and mechanical defect.

Use `stop --kind ... --reason ...` for an explicit user stop, missing context or evidence, or renderer failure. `evaluate` records the final verdict and moves an exhausted run to `stopped` in the same command; use `status` or the stored evaluation to report it without resuming. Use `resume --reason ...` only after the blocker changed. A budget stop requires a user-authorized limit increase recorded after that stop, followed by an explicit resume. A stopped run retains every artifact, transition, feedback item, evaluation, and best candidate.

### 5. Continue from feedback

Treat each user correction as evidence. Before editing, translate it into one observable check: target, current state, required state. Log it with `feedback`. If the user corrects the principle itself, supersede the earlier check rather than accumulating a contradiction. Record changes to audience, purpose, question, hypothesis, message, medium, or constraints with `context`; when one message contains both, call both commands. Change the smallest relevant part of the latest candidate, render, record the media iteration, and run `dataviz-eval` with that check in the evaluation packet. Inspect the named element directly; do not infer success from a generic chart summary. Do not defend the earlier choice or repeat already accepted decisions.

Do not send progress-only replies such as “I’ll fix it” or “now checking”. Use tools silently until a candidate is ready. Every approved chart or revision delivery must include the media attachment in the same response, plus no more than three short lines: what changed, whether values are exact or approximate, and `MEDIA:/absolute/path/to/output.png`. A stopped or blocked diagnostic is not a chart delivery: explain the stop, best candidate, and unresolved findings without `MEDIA:`. It may include a plain absolute artifact path for diagnosis; Hermes will not treat that plain path as a release. If the user asks where an approved graph is, return the media line immediately.

## Acceptance and skill learning

Treat clear phrases such as “this is right”, “done”, “final”, “happy with this”, or “accept” as acceptance. Then:

Do not edit any skill while the case is active. Finish the chart and obtain acceptance first. User feedback is evidence for the later diagnosis, not permission to patch source files mid-loop. Exception: when the case is `stopped` or `blocked` and the user explicitly rejects the workflow result and asks for a system fix, record a paused-case diagnosis without marking the chart accepted. Do not resume or rewrite that chart unless requested.

1. Record acceptance. If the independent verdict is not `Send`, use `--override-reason` only when the user has explicitly accepted that exact artifact; the case remains visibly `accepted_with_override`.

   ```bash
   python3 "${CASE_MANAGER}" accept \
     --case "${CASE_ID}"
   ```

2. Compare the original, every output, the accepted or best stopped output, and every user correction. Split a long case into distinct failure episodes; one case may expose separate creator, evaluator, and tooling misses.
   Include the recorded verdicts, failed gates, failure codes, and required actions. User acceptance remains authoritative even when the evaluator recorded a concern.
3. Classify the first-output miss:
   - `execution-miss`: an existing rule was clear but not followed;
   - `missing-rule`: no reusable rule covered the correction;
   - `ambiguous-rule`: wording allowed the wrong choice;
   - `conflicting-rule`: two skills pushed in different directions;
   - `tooling`: image handling, rendering, inspection, or delivery failed;
   - `input-data`: the needed evidence was absent.
4. Choose one owner for each distinct failure episode. Patch the umbrella `dataviz-fix` skill only when sequencing, logging, revision continuity, or acceptance caused that miss. Patch `dataviz-eval` when the reviewer failed to test or enforce an observable condition. Patch the chart skill when the design principle itself was missing, ambiguous, or conflicting.
5. Change a skill or runner only when evidence points to a reusable rule, missing tool, or ambiguous instruction. Abstract user feedback one level above its examples: describe the reader's mistaken mental model and the violated relationship between evidence, encoding, context, and claim. Do not turn nouns from one chart, domain, event, unit system, or wording into a standing checklist. Before committing a lesson, test it against at least two unrelated chart situations and remove any clause that only handles the originating example. Keep one-off chart preferences in the case record. An execution miss that repeats despite a clear rule is an enforcement or observability problem: add a structured gate, deterministic view, or regression test instead of another prose rule.
6. Make the smallest source change that would have produced the accepted result on the first attempt. Update both `codex/SKILL.md` and `claude/SKILL.md`; update a shared reference only when detailed guidance belongs there.
7. Run `./sync.sh --no-pull --validate-only` in the source repo. Do not commit or push unless the user explicitly asks.
8. Record the diagnosis:

   ```bash
   python3 "${CASE_MANAGER}" diagnose \
     --case "${CASE_ID}" \
     --classification "<classification>" \
     --owner "<skill-name or none>" \
     --lesson "<reusable lesson>" \
     --enforcement "<structured control; required for execution-miss>" \
     --regression-test "<test name; required for execution-miss>" \
     --changed-files "<comma-separated paths or none>"
   ```

If the miss is `execution-miss`, the case manager rejects a diagnosis without both an enforcement mechanism and regression test. Usually do not add another prose rule. If the miss is `input-data`, record why; more rules do not create missing evidence.

## Final accepted response

Return:

- `MEDIA:` for the accepted media artifact;
- accepted chart path;
- case/review-packet path;
- miss classification and owning skill;
- exact skill files changed, or “no skill change” with the reason.

Keep this under six lines unless the user asks for the diagnosis.

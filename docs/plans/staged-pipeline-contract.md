# Staged pipeline contract

## Problem

Skills were delivered as one mega-prompt. The public repair runtime discovered every
`<skill>/codex/SKILL.md` and appended all of them into a single creator adapter, so a build
call carried brief, extract, critique, selector, table-style, powerpoint, cleaning,
analysis-planner and eval at once. Long single-context runs rot: the model loses the thread
of which guidance applies to the step in front of it.

## Approach

Run each pipeline as an ordered sequence of **stages**, one model call per stage. Each stage
carries only the skills it needs plus a compact structured artifact handed forward from the
previous stage.

The skills repo owns:

- the generic stage definitions (diagnose, select, build, refine; and the story-side
  discover, contract, clean, facts, select, build, refine),
- a focused adapter and a content checklist (`output_schema`) for each stage,
- the rule for which builder skill applies (chart vs table),
- a provider-neutral contract another application can reuse.

## What was built

- `dataviz_mcp/stage_contracts.py` - the authoritative provider-neutral contract.
  `REPAIR_PIPELINE` and `STORY_PIPELINE` as ordered `Stage` objects; `stage_skill_bundle`
  reads only a stage's own skills (the context-rot fix); `build_stage_adapter` prepends the
  shared guardrails and the stage's focused instructions. The old
  `dataviz_mcp/public_repair_contract.py` (whole-repository bundle) was deleted.
- `dataviz-fix` repurposed into the staged **repair** orchestrator (diagnose+extract ->
  select -> build -> refine), keeping `case_manager.py` for loop state and telemetry.
- `dataviz-orchestrator` refactored into the staged **dataset-to-story** orchestrator
  (discover -> contract -> clean -> facts -> select -> build -> refine).
- Both skills reference the contract module for the exact skill subset and per-stage content
  rather than duplicating them.
- `dataviz_mcp/tests/test_stage_contracts.py` - the regression guard is that each stage
  bundles only its named skills, and the build stage swaps chart vs table builder from the
  select artifact's `builder` field.

## Handoff format: structured text, not strict JSON

The handoff between stages started as strict, deeply-nested JSON. That serialization broke
cheaper / open-weight models, which are unreliable at valid JSON, so the pipeline could only
run on a strong model. Almost every field in a stage artifact is reasoning content whose only
consumer is the *next LLM stage* - which reads markdown perfectly well. The only thing code
must parse reliably is a handful of routing scalars.

So each stage now emits **markdown sections** (one per content field, read by the next stage)
plus, at the two `select` stages, a small **`routing` block** of `key: value` lines the driver
parses: `builder` (`chart`/`table`) and the `needs_annotations` / `needs_explainer` /
`needs_color_plan` / `needs_precision_plan` flags that gate the conditional build skills.
`dataviz_mcp/handoff.py` parses the routing block leniently and, for backward compatibility,
also accepts a plain JSON object - so strong-model output still works. `case_manager.py`'s
report validators likewise parse tolerantly (code fences and trailing commas are stripped)
while keeping their semantic requirements. The per-stage `output_schema` in `stage_contracts`
is retained as the machine-readable *content checklist*, not a JSON wire format.

## Consumer wired up

`tester/local_runner.py` drives the repair pipeline as separate scoped codex calls -
diagnose -> select -> build - each opening only its stage's skills via `stage_contracts`,
with the diagnose and select artifacts (structured text) passed forward. The blind reviewer
stays a separate call. There is no longer a single creator pass holding every skill. The
build call's builder skill (chart vs table) and its conditional skills (annotations,
explainer, colour, precision) are read from the select artifact's routing block at runtime
via `dataviz_mcp.handoff.parse_routing`.

## Remaining

- `facts` is a named placeholder stage in the story pipeline until `karthik-evidence-builder`
  exists (see `agentic-dataviz-skill-build-plan.md`).
- The story pipeline has no live driver yet; only the repair pipeline is wired into the
  tester. A story driver would follow the same shape (one scoped call per stage).
- End-to-end validation of the staged runner needs a live codex run
  (`DATAVIZ_ENABLE_LOCAL_RUNNER=1`); the unit tests cover the wiring and per-stage scoping.

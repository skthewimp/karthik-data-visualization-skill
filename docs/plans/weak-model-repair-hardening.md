# Making the repair pipeline work on weaker models

Status: planning (opened 2026-08-27). This is a direction, not a committed schedule.

## The problem

The staged repair pipeline was tuned on a strong model. When a cheaper or open-weight
model drives it, a cluster of failures shows up that a strong model never hits: the form
stage collapses (it re-renders the source stack instead of choosing cold), stages get
silently skipped, and when no renderer is wired up the model hand-rolls an SVG/JS path that
emits a dark, monospace, library-default chart. We patched each of these in prose (see the
2026-08-27 CHANGELOG entry: mandatory stages, house visual defaults, renderer ladder,
`form_built` + flow check). Prose patches work on a strong model and leak on a weak one,
because they ask the model's compliance to do a job that code should do.

## The governing principle

"MCP vs text skill" is the wrong axis. Cut the system three ways:

- **Judgment** - which form fits, which messages matter, whether an annotation earns its
  place, what the title claims. No tool can do this. It stays in text the model reads.
- **Mechanism** - rendering pixels, contrast ratios, significant digits, overflow and
  label-collision checks, palette distinctness. Pure determinism. Belongs in code (the MCP
  server).
- **Orchestration** - run the stages in order, don't skip `select`, don't advance on an
  empty form decision, don't improvise a renderer. This is "verify the model did X." Belongs
  in the driver/harness and in runtime validators.

Every weak-model failure we chased was mechanism or orchestration being enforced by prose.
The fix is to move those two categories out of prose and into the deterministic spine, and
to shrink the surviving text down to judgment alone. Short text is exactly what a weak model
follows reliably.

**The trap:** do not MCP-ify judgment. A `recommend_chart_form` tool would be either a worse
model behind an API or a brittle enumerated ruleset - the hardcoded-trigger anti-pattern this
repo already rejects. The precision and colour tools mark the right line: they compute the
mechanical part and *recommend* an assignment, but the skill still owns the call. Hold that
line everywhere.

## Workstreams

Ordered by leverage against weak-model failure. Each names the concrete change and the files
it touches.

### W1. Make `stage_contracts` a runtime validator, not a content checklist (highest leverage)

Today `dataviz_mcp/stage_contracts.py` describes the shape and the skill prose asks the model
to honour it. A weak model can hand back a build that never recorded a form decision and the
prose won't stop it.

- Add a between-stage validator the driver runs on each handoff before advancing.
- Reject a BUILD handoff whose `form_built` is empty, or equals the source form on a
  `redesign` (as opposed to a `bounded-edit`, where retaining the source form is the point).
- Reject a SELECT handoff with no recorded cold form decision.
- Parse leniently (the handoff is structured text, not strict JSON) but *gate* strictly:
  a missing required field is a stop, not a warning.
- Files: `dataviz_mcp/stage_contracts.py`, `dataviz_mcp/handoff.py`, the driver.

This retires most of the C1/C5 prose - the model can't skip a stage that code won't let it
leave.

### W2. Make the deterministic renderer the only sanctioned pixel path (retires the ladder)

The improvised dark/monospace renderer happened because hand-rolling pixels was *available*.
The strongest guardrail removes the capability rather than warning against it.

- Require a valid BUILD to carry a `render_and_inspect_chart`-produced artifact plus its
  metadata (dimensions, backend, hash). No tool artifact, no valid build.
- With that gate in place, the C3 renderer-ladder prose becomes unnecessary - the bottom
  rung (hand-rolled path) is no longer reachable, so it needs no warning.
- Harness precondition: treat a missing/unreachable MCP renderer as a setup failure, not a
  situation the model routes around. If the renderer isn't present, the run fails loudly
  rather than degrading into improvisation.
- Files: the MCP server surface, the build-stage contract, driver preconditions; then trim
  the renderer-ladder paragraphs in `dataviz-fix` and `karthik-data-visualization` once the
  gate is proven.

### W3. Move the mechanical half of the critique loop into tool calls

A weak model eyeballing "is the contrast okay?" is a coin flip. The same model reading
`3.9:1, below 4.5` is reliable.

- Have the checker call `inspect_rendered_chart`, `validate_palette`, and
  `recommend_precision`-as-a-check, and read numbers rather than judge vibes.
- Keep the *semantic* half of `dataviz-critique` in prose - message carriage, form fit - that
  is judgment and stays with the model.
- Files: `dataviz-critique` (both copies), possibly a thin check-mode wrapper in the MCP
  server so the tools return pass/fail verdicts, not just measurements.

### W4. Compress the judgment skills to one decision per turn

`dataviz-selector`, `dataviz-brief`, `chart-annotations` are irreducibly model reasoning and
stay as text. The weak-model lever here is not relocation, it's shape:

- Shorter, example-led, single-decision-per-call.
- Each output captured in the compact structured handoff that W1's validator then checks.
- Resist adding rules; every extra paragraph is one more thing a weak model drops. Prefer one
  worked example over three abstract clauses.
- Files: the three skills' `{claude,codex}` copies, kept identical.

## Sequencing

W1 and W2 first - they convert the two worst failure classes from "hope the model complies"
to "code enforces it," and each one lets us delete prose rather than add it. W3 next, since it
makes the checker trustworthy on a weak model. W4 is ongoing hygiene, done opportunistically
as each judgment skill is next touched.

## Deliberately not doing

- No `recommend_chart_form` / `recommend_annotation` tool. Judgment stays in text (see the
  trap above).
- No new strict-JSON wire contracts between stages. Handoffs stay lenient structured text;
  only the *validation* gets strict, and it runs in code, not in the model.
- No rewrite of `dataviz-eval` here - that is a separate first-principles pass.

## Open questions

- Where exactly does the driver live for the harness that runs weaker models, and how much of
  W1's gating can live in this repo's MCP/contract layer versus the external harness? The
  harness itself is out of this repo's scope; the validators it calls should be in-repo so any
  driver can reuse them.
- Should the between-stage validator hard-fail (stop the run) or bounce one retry back to the
  same stage with the specific violation named? A single named-violation retry may recover a
  weak model cheaply; needs a test.
- Can W2's "tool artifact required" be enforced without breaking the documented local-renderer
  fallback for when the MCP tool is genuinely unavailable? Likely yes: require the tool when
  present, and record "deterministic inspection unavailable" as an explicit, gated state rather
  than a silent improvisation.

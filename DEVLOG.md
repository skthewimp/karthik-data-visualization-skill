# Devlog

## 2026-09-04 - redundant value axis persisted when most (not all) values were labelled

### Context

Karthik: "even when a lot of values are directly labelled, we still get a Y-axis. why is this
happening?" Traced it to detection, not skill wording. `REDUNDANT_VALUE_AXIS` has two paths, both
demanding completeness: the contract path fires on the declared key set but needs the builder to
pass `inspection_contract.direct_labels` (the pipeline usually didn't), and the geometry fallback
required a value label on *every* mark of *every* panel. A chart labelling a lot but not all of its
marks, with no declared contract, tripped neither path and kept its axis, ticks, and gridlines.

The earlier decision (2026-09-01) deliberately kept the geometry fallback strict "because with no
contract it can't tell a key mark from a filler one." Karthik chose to override that here - do both.

### What I changed

- **Geometry fallback: every-mark -> coverage ratio.** Replaced `value_labels >= count` with
  `value_labels >= count * _REDUNDANT_AXIS_MIN_COVERAGE` (0.8), per mark-bearing panel. As a ratio
  it scales with panel size without enumerating regimes: a 3-mark panel still needs all three, a
  10-mark panel tolerates two unlabelled, a focal 1-of-5 stays silent (axis still reads the four).
  The message reports the observed min coverage. `dataviz_mcp/inspection.py`.
- **Skills declare the contract.** `dataviz-execution` (both): the flag entry now tells the builder
  to pass `inspection_contract.direct_labels` at render time so the check fires on the editorial key
  set (endpoints/exceptions), not only on near-complete geometry. `karthik-data-visualization`
  (both): the identification-route rule points at the contract declaration. `docs/mcp.md` updated.
- **Tests.** `bars_mostly_labelled` (4/5 = 0.8) now flags; `bars_few_labelled` (1/5 = 0.2) stays
  silent. Existing every-mark and per-panel tests still pass. `dataviz_mcp/tests/`.

### Decisions

- Line series are unaffected: line points live in `series`, not `marks`, so the geometry fallback
  never fired for pure line charts and still doesn't - sparse endpoint labels on a line keep their
  axis. The relaxation targets discrete marks (bars/scatter) where each value is read individually.
- Kept it a non-blocking-in-spirit suggestion at `medium`; the contract path stays the exact,
  primary route and the geometry share is the conservative no-contract floor.

## 2026-09-04 - the reflexive 0-100 axis: undo the nudge, don't build a tool

Karthik flagged a fresh run: a Bollywood age-mix line chart, values 1-44%, drawn on a 0-100
y-axis - top half of the plot empty. His read was sharp and correct: "R defaults would not draw
to 100. The default is being set somewhere, and it became a bug after we put in the new layout
MCP."

Investigation, not a literal default: I traced every scale-touching tool (`recommend_layout`,
`reserve_frame`, `place_on_marks`, `rendering.py`) - all only *read* the scale from the ggplot
the builder writes; none sets `limits`. So the `c(0,100)` came from the build model *overriding*
the renderer's default. Git archaeology found the decisive fact: `9636814` had already caught
this exact bug (a repaired integer-percent line chart at 0-100) and "fixed" it docs-only. It
recurred. And `e48ec0d` (with the layout-MCP coordinate-separation work) had added "data scales
represent the intended data domain" to the build/tester prose - which for a percentage reads as
its natural domain, 0-100. That is the push.

First I over-corrected: built a `recommend_axis_range` planning tool (select decides zero_based/
hard bounds, tool fits min/max/breaks, build applies), wired as a `needs_axis_range_plan` /
`value_axis_plan` select decision, committed and pushed (`1f7dae5`). Karthik pushed back twice -
first "is this too prescriptive? what about small multiples, dual axes?", then "do we need this
tool at all?" He was right both times. The renderer *already* fits a value axis to the data with
nice breaks (ggplot's Wilkinson, Matplotlib's) for zero model effort - a 1-44 line gets ~0-44,
10/20/30/40 ticks, never 100, never a forced zero. A Python tool would re-implement that wheel,
mishandle log/date/categorical axes, and worst of all re-invite the explicit-`limits` override
that *is* the bug. The path of least resistance (write no `limits`) already gives the right
answer; the fix is to stop pushing the model off it.

So I ripped the tool back out (deleted `axis.py`/`test_axis.py`, reverted server/docs/README/
construct to `9166903`) and kept only the real fix: undo the "intended data domain" phrasing ->
"the data's plotted extent ... not 0-100 unless the data reaches it" (build contract + tester),
and one plain build-guidance line in `karthik-data-visualization` and the construct build stage -
let the renderer's fitted range and nice breaks stand, override only for a deliberate zero
baseline or a genuine full-range case. No new tool, schema, or routing flag. Lesson: a recurring
visual defect is not automatically a missing-tool problem; when the default already does the
right thing, the fix is to stop overriding it, not to add machinery that overrides it "correctly".

## 2026-09-04 - `refit_chart`: close the render -> inspect -> resize loop in code

Built the `refit_chart` MCP tool. The three pre/post-render geometry tools (`reserve_frame`,
`place_on_marks`, `suggest_dims_for_overflow`) already hand *fix vectors* back to the model when
a first render clips or squashes - and the model then spends a full turn editing dims and
re-rendering. That is pure arithmetic dressed up as a model call. `refit_chart` runs the loop
in code: render -> inspect -> while clipping/overflow/squash remains, grow the canvas by the
exact measured overflow (`suggest_dims_for_overflow`) and re-render, up to `max_iterations`,
honouring the delivery ceiling (warned, never squashed) and stopping when a grow stops reducing
the residual.

Design fork I put to Karthik before coding: the scope line named "underfilled canvas", but
underfill has no exact read-back resize vector (the report gives only a ratio, and the fix is a
*shrink* that is predict-and-check, not exact arithmetic - which collides with the repo's
read-back-not-predict rule). Asked; he chose **only grow, report underfill**. So refit grows
deterministically for clip/overflow/squash and surfaces underfill as a residual (`underfilled` +
a warning) for the model to handle as a design call (denser layout / bigger marks / table).

TDD throughout: 16 tests (pure helpers, a fake-renderer loop harness for every exit path -
resolved / ceiling / no-improvement / max-iterations / underfill - plus two *live* renders).
Proven live on both backends: a clipped matplotlib title 396px over the edge clears to 0 in one
grow; squashed ggplot facet panels grow 9.7px -> 136px monotonically (asymptotic under the
shared single-deficit squash math, so multi-row facets ride the budget and report an honest
residual rather than resolving fully - a property of the existing shared math, not a refit bug).

Wired it into the server (14 -> 15 tools), the `dataviz-construct` build/execution stage
contracts (execution runs refit deterministically FIRST, then escalates only non-resize
residuals; build no longer hand-edits dims for clipping), both SKILL.md copies, `docs/mcp.md`,
the READMEs, and CHANGELOG. Full suite 195 -> 212 green.

## 2026-09-02 - Canonical-examples audit: two more shipped failures

Walked the five canonical example outputs. Cases 01 and 05 were the two already fixed earlier
today (Bollywood axis/precision/labels; mixed-unit small multiples). Two new ones stood out:

- Case 02 (token vs cost share): paired share bars carried negative percentages (cacheWrite
  -4.2%, output -0.5%, input -0.8%) under a subtitle asserting "each measure totals 100%". A
  share of a whole cannot be negative - the model relabelled a net/delta as a share and the
  honesty gate let it through. Added a part-to-whole reconciliation check to idea-critique's DATA
  question: components must be non-negative and sum to the stated total.
- Case 04 (seven dietary series): the model stamped a value on every point of all seven lines,
  and the four small series converging near the baseline produced 60 measured label collisions.
  Existing rules already forbid stamping every point, but there was no stated stop-point for the
  convergent-cluster case. Added one to the shared-scale bullet in karthik-data-visualization:
  when small series converge, labelling cannot fix it - change the form (own panel/inset or
  table).

Case 03 (total line + per-model facets) embeds the aggregate "Total" as cell 1 of the component
grid at a 10x scale. The total+breakdown pairing is licensed, so I first only flagged it - then
Karthik asked to add the rule. Added to dataviz-selector: when the pairing uses a small-multiples
breakdown, the total gets its own set-apart panel and scale, never a cell in the component grid,
because a total mixed among components at a different scale is the same false-comparability read
as heterogeneous units.

While adding the convergent-cluster stop-point I noticed the earlier axis-range edit had
overwritten the shared-scale resolution bullet rather than adding beside it; restored it in the
same change.

## 2026-09-02 - Four failures on one integer-percent line chart

Karthik flagged a repaired Bollywood-age line chart with four problems: (1) a 0-100 y-axis when
the data maxes at 44, wasting half the panel; (2) fabricated decimals - `43.0%`, `1.0%` on
integer source data, and ragged (`36%` beside `43.0%`); (3) endpoint value labels clashing with
series-name labels at the right edge; (4) the recent "data labels can't be moved" rule visibly
causing that clash.

Root causes and fixes (no example-specific triggers, all general):

- Precision: the spread rule sets how *few* digits distinguish values but had no ceiling on the
  source's own precision. Added a hard cap - spread can lower digits, never raise above source;
  integers stay integers; one uniform place per column. (`dataviz-precision`)
- Labels: the on-mark `data_label` "never moved" rule (added to stop bar-segment values being
  shoved off-canvas by obstacle-avoidance) was being read as "an overlap involving a data label
  is acceptable." Clarified: the label stays anchored, but a collision is still a defect resolved
  by moving the *other* label - at a line end, the series name is the movable one. (`dataviz-execution`)
- Axis: nothing stopped padding a percentage axis to its unit ceiling. Added: fit the axis to the
  data range, a percentage does not force 0-100, upper bound just above the max, zero baseline only
  where the encoding needs it. (`karthik-data-visualization`)

## 2026-09-02 - Small multiples with mixed units keeps slipping through

Karthik flagged a published repair that turned a mixed-unit comparison table into a five-panel
small-multiples grid (lines written, $/line, mean prompt chars, API calls, $/burst - five
different units), and defended it as "panels preserve the distinct units." We already had a
"panels must share the same unit" rule, so this was an enforcement failure, not a missing rule.

Root cause: the rule was buried as the final clause of the ~400-word multi-series bullet in
`dataviz-selector`, after layout, ordering, and shared-vs-free-scale prose. A weak model reading
that wall never acts on the last sentence. And no gate re-checked it before render - the execution
gate passed the grid geometrically ("0 measured defects").

Two changes, no new machine schema (unit metadata isn't reliably available, and a hardcoded
check would overfit):

- pulled the same-unit requirement out into its own standalone `dataviz-selector` bullet, led
  imperatively as a hard gate, with the "preserve the distinct units" rationalisation named as an
  argument against the grid;
- added the heterogeneous-unit-facet check to the EXPRESSION question in `dataviz-idea-critique`
  so the pre-render gate catches it and routes back to `select`.

Kept general: the test is per-panel unit commensurability, not the example's five panels or its
specific units.

## 2026-09-02 - Separate data coordinates from layout coordinates

A repair run compressed a time series after the builder reserved label space twice: once by
extending the year domain far beyond the data and again with a huge physical margin. The same run
left known direct labels unwrapped because an optional placement plan contradicted the selected
design.

The first draft added a mandatory direct-label schema. Karthik correctly flagged that as
overfitting. The final fix removes that extra structure and repairs the general mechanisms:

- reader-facing text blocks whose words and anchors already exist trigger text placement directly;
- quantitative domains carry data, while non-data content and whitespace use screen/layout
  coordinates;
- the same whitespace cannot be reserved in both systems.

No chart type, date range, label count, or right-side-band special case was encoded. The observed
failure remains only as regression motivation.

### Follow-up: labels need a reading-length budget

Placement already wrapped text, but movable labels inherited the annotation width ceiling: 32% of
the canvas. On a wide canvas that legitimised very long one-line series names. An intermediate fix
replaced that with universal 24-character / three-line defaults; Karthik caught the same category
error again—readable measure is a design judgment, not a constant. For every series/category,
on-mark data, and axis label, build now passes `max_width_px` and `max_lines` from the delivery
condition, density, and available region. The tool enforces those limits. Curtailment is explicit
and retains `full_text`; otherwise an over-budget label stays intact and is reported for revision.
Free annotations keep their separate canvas-relative allowance.

## 2026-09-01 - Selector: crowding-gated facets + separate smoothing rule

### Context

Feedback: the selector over-uses small multiples - it faceted ~4 lines that a single
direct-labelled panel would carry fine. Separately, the selector had no notion of drawing a
smoothed line (loess/regression) along a noisy series, or of points-as-scatter + smoothed trend
instead of connect-the-dots.

### Key correction from Karthik

These are **two unrelated rules**, not one ladder. My first pass conflated them (crossing signal ->
smooth *or* facet); Karthik rejected that. Facets are a crowding/overplot decision only. Smoothing
is a point-density decision within a single series (none of the current corpus cases even have
dense-enough series), and he draws at most 1-2 smooth lines per graph.

### Decisions

- **Rule A (facets):** default one panel, direct-labelled lines; escalate to small multiples only on
  too-many-to-label or spaghetti overplot. Lines crossing / noisy shape is explicitly *not* a facet
  trigger. Rewrote the "many comparable series" bullet; existing layout guidance now gated on "once
  faceting is warranted".
- **Rule B (smoothing):** new standalone bullet, point-density trigger, decoupled from series count
  and faceting. Overlay-on-faint-raw or scatter-plus-trend; cap 1-2 smooths; show uncertainty, keep
  turning points, mark extrapolation.
- No enumerated counts anywhere (no-hardcoded-cases). KDV line 116 already gates facets on "crowded",
  so no contradiction - left untouched.
- Both claude+codex copies edited; `./sync.sh --no-pull` to install.

### Follow-up: panel/bar ordering (Quartz liquor small-multiples as the good example)

Reviewed a food-share small-multiples output vs the Quartz "shots per week" chart. Verdict: the food
chart's family (facets) was right and slopegraph was wrong (non-monotonic trajectories - peaks/dips -
that a slopegraph would flatten to endpoint change). The one reusable lesson Karthik wanted encoded
was **ordering**, not the free-scale critique.

- Small-multiple panels: order by decreasing peak value or decreasing story importance, top-left to
  bottom-right; if the key story isn't the biggest panel, thicken its line instead of reordering.
  `dataviz-selector` + `karthik-data-visualization`, both copies.
- Horizontal ranking bars: longest at top, descending - ordering is load-bearing. Vertical bars: less
  order-sensitive but still order meaningfully. `dataviz-selector`, both copies.

## 2026-09-01 - New dataviz-aesthetic composition gate

### Context

Feedback: pipeline charts don't look "premium enough". Beyond the label overload fix, we wanted a
reusable *aesthetic review* run once a chart is produced - the five questions: what is seen first,
is anything competing with it, does every box/rule/colour/bold phrase earn its place, is
whitespace grouping or filling, does it look composed rather than styled ggplot output. Open
question was whether it should also seed the planning/build phase.

### What I found

Mapped the existing post-render skills: `dataviz-execution` = element-level defects, `dataviz-eval`
= send/revise/redesign + semantic meaning + benchmark, `dataviz-critique` = broad diagnosis +
alternatives. None owned composition / first-read / "premium feel" - a real gap, so a dedicated
skill is not a thin wrapper.

### Decisions

- **New standalone skill `dataviz-aesthetic`** (both forks confirmed with Karthik: new skill, and
  seed build too). Standalone so both execution and the build phase point at one source instead of
  duplicating the principles.
- **Distinct lens, hard delineation.** Execution hunts defects element by element; aesthetic steps
  back and reads the whole image, and explicitly never re-checks geometry/precision/CVD. Kept it
  from collapsing into a second eraser-test section.
- **Three wiring points.** (1) `dataviz-execution` runs the pass as its final step once defects are
  clean; (2) construct `execution` stage bundles both skills in `stage_contracts.py` + instructions
  mention it; (3) build intent seeded in `karthik-data-visualization` (decide the one focal element
  before drawing) and a one-liner in `dataviz-selector` (form choice = what is seen first).
- **No new folder README.** The sibling gates (execution, idea-critique, construct) have none;
  matched them. Install-path lists in root README are already a stale partial subset that omits the
  newer gates - left them rather than half-fix.
- **No code logic change.** Only `stage_contracts.py` gained the skill in the execution bundle +
  instruction text; `sync-skills.py` auto-discovers skill dirs, so no manifest edit. Full pytest
  suite green (163).

## 2026-09-01 - Label ownership in the core skill; axis drops on the key labels

### Context

Feedback: pipeline charts don't look "premium enough" - one cause is too many labels. The clean
split (from the review comment): Select/Build decides *what deserves a label and why*;
`recommend_labels` picks feasible indices within that scope; `recommend_text_placement` only
places; execution confirms attachment and that unnecessary labels were removed. The placement
tool must never independently add, delete, or rewrite labels. The editorial principle belongs in
the core visualization skill. Related: we don't need *all* points labelled to drop an axis - key
points labelled is enough.

### What I changed (scope trimmed to fixes 1-3 on Karthik's call)

- Core `karthik-data-visualization`: added the editorial-scope rule ("a direct label earns its
  place; decide scope first") naming the five things that earn a label, and stating the tools pick
  within scope and never widen/add/rewrite it. Relaxed the quantitative drop-unless test so the
  axis goes once the reading-carrying marks are labelled, not once every point is.
- `dataviz-execution`: reworded `REDUNDANT_VALUE_AXIS` to make the contract path (key set) the
  primary trigger and the every-mark geometry path the conservative no-contract floor; extended the
  eraser test to labels themselves.

### Decisions

- Scope owner = core skill only (not a new skill, not widening `chart-annotations` which stays
  callout-only). Matches the comment: principle in core, enforced downstream.
- Kept `recommend_labels` budget at 4/series - no hardcoded count change; the upstream editorial
  gate does the trimming.
- No `inspection.py` change: the contract path of `REDUNDANT_VALUE_AXIS` already fires on the
  declared key set, so relaxing "every mark" was a wording fix, not code. The geometry fallback
  stays strict because with no contract it can't tell a key mark from a filler one.
- Deferred (Karthik: less important): tightening `recommend_labels`/`recommend_text_placement`
  docstrings, and a mechanical over-label flag.

## 2026-09-01 - Mechanical restatement check in the label-positioning tool

### Context

Prompt (paraphrased): the benign-annotation catch should not be in execution - it belongs in the
label-positioning tool. When a data label already exists and an annotation just restates it,
recommend removing the annotation.

### What I changed

`recommend_text_placement` (`text_fit.py`) already receives both the annotations and the on-mark
`data_label`s with their anchors, so it is the natural enforcement point. Added a post-placement
pass: parse numeric tokens from each block; a free annotation carrying exactly one data value
(years/coordinates excluded via a 1500-2200 integer test) whose value a `data_label` within ~20%
of the canvas diagonal already prints is recommended for removal. Returns a top-level
`redundant_annotations` (`{id, restated_value, data_label_id}`) plus a per-block warning.

The single-value constraint is what keeps it honest: a comparison naming two values
("from 51% to 26%") or a delta whose number is on no label ("up 9 points") is never flagged - those
add what the labels do not. Server docstring, `docs/mcp.md`, and the `chart-annotations` value-add
gate now point at it. Three regression tests (flag the restatement, spare the comparison, spare the
delta).

## 2026-09-01 - An operational gate for benign annotations

### Context

Prompt (paraphrased): the fix workflow keeps producing benign annotations ("Up 9.0 points",
"highest output: 340 lines", "Peak: 42% in 2000"). I only want annotations that add value. How?

### Diagnosis

The rule existed but did not bind. `karthik-evidence-builder` (origination) said in one soft
sentence that a mark "that restates the obvious, or that the axis already shows, is clutter" - too
weak for a weak build model to operationalize. And `chart-annotations` (the ranking/keep gate) had
no restatement reject at all: it ranked by "reader payoff" but never dropped a candidate that
merely restated a visible label. So benign candidates slipped origination and were then ranked and
kept.

### What I changed

- **Operational test, both skills.** An annotation adds value only when its content cannot be
  recovered from the marks the reader already sees - direct labels, axes, title. Named three
  general benign classes (restate a labelled value; name a rank the geometry shows; restate a
  change two labelled endpoints show) against what earns a mark (a computed comparison, a
  cause/consequence, a threshold's meaning, outside context, attention to an easy-to-miss feature).
- **evidence-builder:** expanded the candidate-annotation rule into that test. Both copies + mirror.
- **chart-annotations:** new "value-add gate" in Step 3 - reject restatements before ranking;
  updated numbered Step 4 and added a pitfalls row. Both copies + mirror.
- General principle keyed on "recoverable from the marks", no enumerated chart or phrase.

## 2026-09-01 - Years are labels; redundant-axis flag reaches into facets

### Context

Prompt (paraphrased): a faceted shares-over-time fix-workflow chart had three problems - shared Y
axes flattened the small categories (or it should have been a slopegraph), the annotations were
benign and over-precise, and every panel showed both direct labels and a value axis. What went
wrong, and is it the selector?

### Diagnosis

Three defects, three owners. (1) Shared-vs-free scale: the free-scale rule already exists in the
selector (line 46) - a compliance miss, not a gap. (2) `2,000` for the year 2000 and `40.0%` /
`9.0 points`: precision. The year is a real gap - the skill had no notion that a temporal/ordinal
coordinate is a label, not a measured quantity; the `.0` is a build bypass of `recommend_precision`
(the spread rule gives 0 decimals for shares spanning 1-42). (3) Direct labels + value axis:
`REDUNDANT_VALUE_AXIS` exists but only fired from a caller-declared direct-label contract, which a
faceted build did not supply.

Karthik chose to fix the precision label rule and the faceted redundant-axis detection.

### What I changed

- **Precision.** New "labels are not measurements" section: years, quarters, ranks, stages, IDs
  used as coordinates take no thousands separator, no spread rounding, no forced decimals -
  outside the spread rule, distinct from the exact-lookup override. Both copies + docs mirror.
- **Redundant-axis in facets.** `inspect_rendered_chart` gains a geometry fallback: when no
  direct-label contract is declared, it groups marks and numeric value labels by axes (reliable
  where tick `axes_id` is not) and fires once every mark-bearing panel labels each of its marks.
  Contract path untouched; fallback runs only when the contract found nothing. New fixture
  `faceted_bars_all_labelled` + regression test. `dataviz_mcp/inspection.py`.
- Left for later (compliance, not gaps): benign annotations, the `.0` build bypass, and the
  shared-vs-free scale application.

## 2026-09-01 - Selector: ordered/time axes keep their direction, magnitude gets bars

### Context

Prompt (paraphrased): a fix-workflow chart put Q1–Q4 (a time series) down the y-axis reading Q4
at top to Q1 at bottom, and drew each value as a dot on a line. Inverting a time axis is wrong,
and a bar beats the dot-with-line. What in the selector led to this?

### Diagnosis

Two selector gaps. The "Ranking: sorted horizontal bars" bullet had no guard excluding ordered
axes, so a time series got read as a ranking - categories flipped onto y, sequence direction
lost. And nothing steered a single-value-per-category magnitude toward bars, so a lollipop
(dot + hairline stem) slipped through even after dot plots were dropped from magnitude guidance.

### What I changed

- **Ordered-axis rule.** An intrinsically ordered category axis (time, stages, sizes, ranked
  bins) keeps its order and natural direction - left-to-right, or top-to-bottom if vertical -
  never magnitude-sorted or inverted so time climbs upward. Magnitude-sorting and the
  horizontal-bar layout are nominal-only. Holds per panel in small multiples.
- **Bar-vs-lollipop rule.** A single value per category read as magnitude is a bar (filled length
  is the cue, zero anchors it); a lollipop/dot-with-stem is reserved for many dense categories
  where the endpoint matters more than the filled length.
- Both in `dataviz-selector` (claude + codex), mirrored in `docs/skills/dataviz-selector.md`.
  General principles, no enumerated dataset or chart type.

## 2026-09-01 - On-mark labels stop getting shoved off their marks

### Context

Prompt (paraphrased): a stacked bar wanted its segment values ON the boxes, but
`recommend_text_placement` pushed every label out and the graph became malformed. Full tool logs
plus the rendered result attached. How to fix?

### Diagnosis

Misuse, not a tool bug. All 16 segment values (`44%`, `39%`, …) were passed as `role: "label"`
= movable, with the bar segments passed as `obstacles`. A movable block's contract is "move it
out of any obstacle to the nearest clear spot + leader line" - so the tool shoved every value off
its bar, drew leaders, and by retry 4 clipped them off-canvas at x~2200. The two *free* callouts
on the same chart placed cleanly every call - proof it was the routing, not the geometry. A value
the plotting layer already centred inside a segment is position-fixed by the data, like a title,
not a free annotation to de-collide.

### What I changed

- **New `data_label` role.** `ON_MARK_ROLES = {"data_label"}` joins the pinned set - wrapped,
  never moved, no leader line, and never de-collided against obstacles - but wraps to the narrow
  annotation band, not the full canvas width, so a short segment value never wraps like a title.
  Only free callouts (annotation/label) still get obstacle de-collision. `dataviz_mcp/text_fit.py`,
  `dataviz_mcp/server.py`.
- **Guidance.** `dataviz-execution` (both copies), `docs/mcp.md`, and the tool docstrings now say:
  tag on-mark values `data_label` and never list their own bar in `obstacles`. General principle
  keyed on "plotting-layer-centred label", no enumerated chart type.
- **Regression test.** `test_on_mark_data_label_stays_on_its_mark` - a `data_label` whose anchor
  is covered by an obstacle stays put, no `suggested_anchor`, no `leader_line`, no warnings.

## 2026-08-31 - Leader lines for displaced labels, and the selector stops endorsing dot plots

### Context

Prompt (paraphrased): reviewed a fresh canonical-examples run. Mostly happy, geometry now fixed.
Remaining gripes - some data labels sit away from their points; dot plots read poorly for
categorical-vs-numerical comparisons (want bars, or a slopegraph); small multiples on a shared
scale hide the shape of the small curves. Which skills/MCPs fix this?

The scope tightened over a few turns: label fix goes in the text-placement MCP as a leader line
(not the selector); the selector should drop dot-plot endorsements while keeping dumbbells and
scatter; slopegraphs are not two-period-only and must label both ends and show every value; add
the small-multiples shared-vs-free scale rule. No new invented guardrails.

### What I changed

- **Leader line.** De-collision already moves a colliding label to the nearest clear spot, but a
  moved label then floats unpaired. `recommend_text_placement` now returns `leader_line`
  (`{from,to}`, box perimeter to the original anchor) for any movable block that ends up off its
  anchor, plus a warning. The builder draws the thin connector - ggrepel's segment.
  `dataviz_mcp/text_fit.py`, `dataviz_mcp/server.py`.
- **Selector.** Removed dot plots from the two-point, composition, and magnitude-channel
  guidance; kept dumbbells, paired bars, and scatter. Generalised slopegraphs past two periods
  (label both ends, show every value). Added the shared-vs-free scale decision to the
  small-multiples bullet. `dataviz-selector` (both copies).

### Notes

Half the friction was mine - jumped toward running tests before the edit set was complete and
before reading `AGENTS.md`. Publish (tests/sync/commit) is the final step, run once when the
change is done, not mid-way.

## 2026-08-31 - Placement gains font-shrink and a portrait-flip recommendation

### Context

Prompt (paraphrased): in the piece that looks at labels and suggests repositioning - does it
also resize labels? And it should recommend flipping the canvas to portrait when that makes
things easier. Both belong in `recommend_text_placement` (the build-phase MCP that takes all the
text), not in `recommend_layout`: layout's dims are disregarded downstream and other harnesses
already own orientation, whereas the flip can be applied later, in the build phase where wrapping
is decided.

### What I changed

- **Resize.** The collision ladder was move -> tighten-wrap -> hand-review; font size was read
  once and never reduced. Added a shrink step between move and tighten: step the font down
  (largest that fits) toward `min_font_pt` (default 8pt, the inspector's legibility floor, never
  below) and re-search for a clear spot; return `suggested_font_pt`. Only movable roles shrink.
- **Portrait.** After the loop, if any block stayed unresolvable on a landscape canvas, return a
  canvas-level `suggested_orientation: "portrait"` and swapped `suggested_canvas`. Honest about
  its limits: the tool can't move the data marks, so it recommends the flip rather than verifying
  it - a later build stage re-renders portrait and re-runs placement against the new geometry.

### Notes

- 156/156 MCP tests pass; new fixtures cover a window only a shrunk box fits, the floor never
  being breached, an unresolvable landscape recommending portrait, and a clean chart recommending
  no flip.

## 2026-08-31 - Enforce three style bans the canonical run exposed

### Context

Prompt (paraphrased): the canonical-examples gallery still shows model output with tiny
bordered facets, misplaced labels, wasted grey bands, slanted axis labels, an external legend,
and needless colour on a single-series-per-facet chart - do any skills need fixing? The ugly
charts are the graded subject (a weak model's `exact published PNG`), not the skills rendering;
the harness already flags the geometry ones. But three style bans lived only in prose: slanted
ticks, external legends, and redundant colour.

### What I changed

- **A - slanted labels.** `recommend_layout` was *recommending* the banned thing: it set
  `rotate_x_labels = True` on overflow. Now it stays `False` and the overflow warning points at
  horizontal remedies (abbreviate / thin to every-Nth / widen). Test rewritten to lock in "never
  rotate".
- **B - external legend + redundant colour.** Two new low, non-blocking inspection flags built
  on the same principle, generalised past the immediate case: a legend is redundant when the
  series are already named on the plot (direct labels - however many lines - facet titles, or
  category ticks); colour is redundant when it is 1:1 with a channel already encoding the
  grouping (facet, category axis, direct labels). The precise trigger, not the severity, keeps
  legit charts silent - many crossing unlabelled lines keep their legend, a focal-plus-grey bar
  highlight keeps its colour (fewer fills than bars). Line series now export their `colour` so
  the check compares by value.

### Notes

- A separate finding (text placement not applied to Case 5) traced to the website repo
  (`public_site/runner.py` drops role `label` before calling the placement MCP; the R-emit step
  ignores `suggested_anchor`). The placement MCP is correct - `label` is already a movable role -
  so nothing changed here. Left for the website repo.
- 152/152 MCP tests pass, including new fixtures for both flags and their silent cases.

## 2026-08-31 - Forward geometry tools: size and place before the render clips

### Context

Prompt (paraphrased): a weak-model run still produces charts that clip the title/footer,
squash many facets into a shallow canvas, and collide annotations - and with a small revision
budget the model can't guess its way back. The fix belongs at the skill/tool level, not in
harness gates. Two ideas emerged: a tool that sizes the canvas from the data/shape before the
render, and - once dimensions, title, subtitle, caption and annotation anchors are known - a
tool that recommends efficient text wrapping and moves annotations that would collide,
including against the data.

### What I found

`inspect_rendered_chart` already *detects* every one of these (clip, collision, utilization),
but only after render - so the model burned iterations guessing new dims. The gap was a
*forward* tool (the missing sibling to `recommend_precision` / `recommend_colours`) and,
inside inspection, a fix vector telling the model *how much* to change, not just what's wrong.

Mining ~416 ggplot files corrected the sizing model twice: it is regime-*driven* input but not
regime-*named* output (an early `_classify` with `n_x >= 40` thresholds was the enumerated-case
anti-pattern and got cut), and Karthik never hand-sets margins - so the tool returns
`width x height x dpi` + facet grid, not a margins dict. `coord_flip` (80 uses) showed the real
principle: orientation decides which axis absorbs a count, so sizing is one rule -
`slots x per_slot_floor` per axis, `y_slots` grows height (labels stack), `x_slots` grows width
then rotates (labels crowd) - with two documented legibility floors (filled vs point marks),
no regimes, no thresholds.

### What I built

`dataviz_mcp/layout.py` (`recommend_layout` + shared geometry primitives + a backward
`suggest_dims_for_overflow`), `dataviz_mcp/text_fit.py` (`recommend_text_placement`: greedy wrap
+ ring-search de-collision against text, edges, and data marks - marks always passed as
obstacles), and `inspection.py` widened to schema v3 with per-edge `overflow_px` /
`grow_margin_px`, `separation_needed_px`, `panel_heights_px`, and a `geometry_summary` whose
`suggested_dims` reuses the layout math. Both tools registered in `server.py`; the two
resolution points documented in `dataviz-construct` and the fix vectors in `dataviz-execution`
(both `{claude,codex}` copies). 20 new tests; full suite 131 green.

Follow-up the same day: a `REDUNDANT_VALUE_AXIS` inspection check (backward only, since it needs
the render metadata). When direct-label coverage is complete yet numeric axis ticks still
render, they are duplicate ink - the eraser test made mechanical. The `tick_label` role does not
carry x/y, so the clean discriminator is the tick *text*: numeric ticks are the value axis
(flag), category ticks name marks (keep). Low severity so it never blocks - a zero baseline can
still earn the axis. 2 tests + a fixture; suite 133 green. Facet-scale-for-insight parked for a
later pass.

## 2026-08-28 - Coalesce creation and repair into one construct process

### Context

Prompt (paraphrased, PII stripped): the dataviz-fix and dataviz-create workflows should
coalesce into one workflow after the front half figures out what to do / change - the graph
construction part is shared. And in that shared workflow, run two rounds of iteration: first
whether the graph is appropriate / conveys the right message / has the right data, then a
second round for semantics, overlaps, execution - in that order. A follow-up reframed it: one
shared process (`dataviz-construct`), with separate skills for the *ideas* (is the data right,
the expression right) and the *execution*; ideas can run before the chart is constructed;
whether it loops 0/2 times is the harness's call, not ours - our job is to define the skills
and process. Two more constraints: do not touch `dataviz-critique` (still needed standalone
and at the repair diagnose step); and the headline/annotation insight generation had to become
an explicit pre-build step (build `karthik-evidence-builder`, the long-standing facts gap).

### What I found

Exploration confirmed both pipelines already converged on `select -> build -> refine`
(`dataviz_mcp/stage_contracts.py`), duplicated as prose in `dataviz-fix` and
`dataviz-orchestrator`. The single `refine` stage mixed substance (question-data-visual,
message) with craft (overlap, ink) and hardcoded a two-pass cap. Insight for headlines lived
in a skill-less `facts` stage (create) or was recovered, not computed (repair); the headline
claim and annotations were decided late, at build, by `chart-annotations`, with nothing
validating pre-render that the claimed insight was supported.

### What I did

- **`dataviz_mcp/stage_contracts.py`:** replaced the two `... -> select -> build -> refine`
  tails with one shared construct tail `insight -> select -> idea -> build -> execution`.
  `select`/`idea`/`build`/`execution` are single shared `Stage` objects spliced into both
  pipelines via `_construct_tail(...)`; only `insight` is parameterised by its input schema
  (`DIAGNOSE_SCHEMA` for repair, `CLEAN_SCHEMA` for story). Added `INSIGHT_SCHEMA` (facts +
  `headline_claim` + `candidate_annotations`, supersedes `FACTS_SCHEMA`), `IDEA_CRITIQUE_SCHEMA`
  (verdict + four judgements + issues with `route_back`), and `EXECUTION_SCHEMA` (renamed from
  `REFINE_SCHEMA`). Removed the two-pass cap from the adapter text and stated the budget is the
  driver's.
- **Four new skills** (each `claude`/`codex` byte-identical + folder README): `dataviz-construct`
  (shared process doc), `karthik-evidence-builder` (insight stage), `dataviz-idea-critique`
  (pre-render gate), `dataviz-execution` (post-render gate).
- **Edited skills:** `dataviz-fix` and `dataviz-orchestrator` reduced to their front halves,
  handing into `dataviz-construct`; the 2-pass cap removed. `chart-annotations` now receives
  the headline claim and candidate marks from the insight stage (body edit applied to both
  variants, preserving each frontmatter). `dataviz-critique` untouched, as instructed.
- **Tests:** updated `dataviz_mcp/tests/test_stage_contracts.py` for the new stage ids and
  schemas; added `test_both_front_halves_share_one_construct_tail`,
  `test_insight_stage_has_a_real_skill`, `test_insight_names_the_headline_claim_before_build`,
  and `test_no_construct_stage_hardcodes_an_iteration_cap`. Full suite: 107 passed.
- **Docs:** root `README.md` (18 -> 22 skills, front-half framing, tree), `dataviz_mcp/README.md`,
  `docs/mcp.md` generation sequence, `docs/skills/{dataviz-fix,dataviz-orchestrator}.md`, the
  docs indexes, four new `docs/skills/*.md` pages, and this plan in `docs/plans/`. Historical
  CHANGELOG/DEVLOG/plan/design entries were left as the record they are.

### Design decisions

- **Ideas before execution, as separate skills.** The idea gate is judged from the plan and
  the data (no render needed), so it runs first and cheapest; the execution gate needs pixels,
  so it runs after build. Splitting them into two skills keeps each context lean and matches the
  per-stage-call model.
- **Insight is an explicit pre-build stage.** For the idea gate to check "is this the right
  insight" before rendering, the headline claim and candidate annotations must exist before
  build - so `karthik-evidence-builder` produces them, and `chart-annotations` words/places what
  it named rather than originating the claim.
- **No hardcoded pass count.** Each gate is a `find -> fix -> redo` unit; the harness owns how
  many times it runs.

## 2026-08-27 - Make the house rules bind when a weaker model runs the repair loop

### Context

A benchmark run of the `dataviz-fix` repair loop on a weaker / open-weight creator model
regressed against an earlier run that was good: the weaker model loaded
`karthik-data-visualization` and violated its rules anyway. Two failure clusters, both
structural rather than "a missing rule":

1. **Form-intelligence collapse.** The model went diagnose -> build, skipping the cold
   form-selection stage, so it re-rendered the source form more tidily instead of choosing
   the form that makes the message easiest to read.
2. **Improvised renderer.** With the deterministic renderer absent, the model hand-rolled an
   SVG/JS/Ghostscript path that emitted a dark background and a monospace/terminal typeface -
   the library-default look the skills already forbid.

The rules were already in the skills and were good; they stopped *binding* under a weaker
model. So the work was to close the routes by which a stage or a house default silently
drops out. Change surface: everything in this repo (skills + MCP); the private benchmark
harness is out of scope and fixed separately. Everything had to stay generic so the repo
keeps working standalone for other people's harnesses - no hardcoded cases, no private model
names, the house typeface reaching the skill via brand config rather than a literal.

The fixes were walked one at a time (labelled C1-C6 in a private working doc), discussing
each before editing and editing both `codex`/`claude` copies together.

### What was done

- **C1 - stages mandatory.** `dataviz-fix` reframed so the ordered stages run whether or not
  a driver splits the calls; single-turn runs must still walk every stage. `select` hard-gated
  as mandatory for every redesign; only a literal `bounded-edit` skips it. Conditional build
  loads (`karthik-table-style`, `dataviz-precision`) stated as mandatory-when-triggered.
- **C2 - House visual defaults.** `karthik-data-visualization` gained a "House visual defaults"
  block (light background, proportional sans, direct labels, claim-first title) that binds the
  export regardless of renderer and is checked at the render-and-inspect step. Default-background
  rule tightened to match.
- **C3 - renderer fallback ladder.** Explicit renderer order in both `dataviz-fix` and
  `karthik-data-visualization`, a forbidden-move rule (no improvised dark/monospace/Ghostscript
  path), and an escape hatch (no compliant renderer -> report failure, do not ship a violating
  chart). Escape hatch kept in the build stage only.
- **C4 - canvas/aspect ratio: SKIPPED.** Scoped and discussed (inherit the delivery *frame*,
  not the source's mis-shapen canvas; source aspect ratio is defeasible evidence, overridden by
  judgement for implausible shapes like one-column small multiples; the prompt always wins) but
  deferred this pass as cosmetic relative to the dark/monospace and form-collapse failures. Not
  rejected - deferred.
- **C5 - form-decision field + flow check.** Verified `recommend_precision` is sound (money/ratio
  columns produce no excess digits; the earlier symptom was the stage being skipped, i.e. a C1
  problem) - no code change. Added a required `form_built` string to `BUILD_SCHEMA` and a refine-
  stage flow check that reads it: a build with no recorded cold form decision is a fatal flow
  violation.
- **C6 - retune `dataviz-eval`: NOT done as a patch.** On inspection, `dataviz-eval` is an
  optional, out-of-loop blind reviewer (Stage 4's default reviewer is `dataviz-critique`;
  eval is spawned only for an explicit audit / high-risk decision). It was pulled into the
  path because the builder was failing - the wrong layer, since C1-C3 prevent those failures
  upstream while a reviewer only detects them late, and eval's own "taste is not fatal"
  carve-out was letting the exact house-defaults violation through. Decision: rebuild
  `dataviz-eval` from first principles in a separate pass rather than patch it. The seed for
  that rebuild lives in the private working folder.

### Housekeeping

Moved the private benchmark artifacts (model-comparison decks, the full creator/reviewer
transcript, and the codename-bearing diagnosis + first-principles docs) out of the repo into a
private sibling folder, and added `.gitignore` patterns so they cannot be re-committed. Those
carry private model codenames and raw benchmark data and must not reach the public repo.

### Verification

`./sync.sh --no-pull --validate-only` green across all 18 skills;
`pytest test_stage_contracts.py test_precision.py` → 38 passed. Both `codex`/`claude` copies of
each edited skill confirmed identical.

## 2026-08-26 - Decouple standalone skills from the repair/story harness

### Prompt

> forget the downstream harness that i'm building. how does this repo currently stand as a set
> of standalone skills and MCPs for building and repairing dataviz, and analysing data? anything
> is off or overfit or hardcoded?

Then, across follow-ups: undo the machine-specific overfit; reframe the pipeline coupling by
*precondition* rather than "demote" it to a footer; check once more for dangling references, dead
blocks, and unnecessary JSON; do all four remaining; commit and push with documentation.

### Context

An audit of the 18 skills + MCP as standalone units. The MCP (10 deterministic render/inspect/
colour/precision tools) and the single-purpose skills were clean; `color_math` / `precision` are
principled (real WCAG sRGB constants, spread-keyed significant digits), not tuned. Two problems:
(1) one personal skill hardcoded machine-local notebook paths; (2) ~6 skills wove the staged-
pipeline wiring into their prose - harness component names and schema field names - so they read
as stage configs, not standalone skills, and `dataviz-critique` still carried a JSON "structured
repair brief" that the staged refactor had already replaced with `DIAGNOSE_SCHEMA`.

### What changed

- Reframed harness coupling by precondition in `dataviz-precision`, `dataviz-brief`,
  `dataviz-critique`, `dataviz-color`, `dataviz-selector`: "if an upstream decision already exists,
  obey it and carry its reason; otherwise decide here" - no harness component or field names. The
  wire-format field names stay in `stage_contracts.py`, where code actually reads them.
- Removed dead blocks: `dataviz-critique`'s `public_repair_contract`-era JSON contract and its
  orphaned field notes; `karthik-data-visualization`'s deprecated "design contract" (rewritten as a
  standalone "audited repair plan" checklist); the stale "design contract" input in `dataviz-eval`.
- Deleted the machine-local exemplar-path block from `karthik-r-analysis-style` (kept the
  domain-name lists and comment-voice examples, which are portable).
- Left `dataviz-fix` and `dataviz-orchestrator` as-is - they own the pipeline and correctly name
  `stage_contracts.py`, `stage_skill_bundle`, and the routing block. Sibling "see also →
  `dataviz-fix`" pointers kept.

### Decision / scoping note

The rule: **frame the coupling by precondition, not by naming the harness component and its wire
fields.** That keeps each skill true standalone and still correct inside the pipeline. Rejected the
alternative of quarantining the pipeline prose in a trailer ("demote"), which would have left the
harness field names sitting in the skill body.

### Validation

`./sync.sh --no-pull --validate-only` validates all 18 skills; `git diff --check` clean. Prose-only
change, no code or tests touched. 16 files (8 skills × `codex`/`claude` surfaces).

## 2026-08-26 - Structured-text handoffs so the staged pipelines run on cheaper models

### Prompt

> recently we moved the dataviz-fix and orchestrator workflows from a monolith to a series of
> LLM calls with only the right contexts loaded in. however the issue with this is that it now
> overly depends upon json output because of which i'm unable to use this with cheaper / open
> weight models which inevitably break on json output. is there a way around this? investigate
> first.

Chosen after investigation: **format-robust handoffs**, full maintainer scope (both pipelines,
both `codex`/`claude` surfaces, `case_manager`, docs, tests, sync).

### Context

The staged refactor (see the 2026-08-... entries) passes each stage's artifact to the next as
strict, nested JSON. Cheaper / open-weight models are unreliable at valid JSON, so the pipeline
effectively required a strong model. The investigation found the JSON is load-bearing in two
layers: the inter-stage handoff artifacts (`stage_contracts.py` schemas + the `diagnose`/`select`
files the runner passes forward) and `case_manager.py`'s nine `validate_*` report validators,
which hard-fail with `SystemExit` on any shape deviation. The key realisation: almost all of that
JSON is reasoning content whose only consumer is the next LLM stage - which reads markdown fine.
Only a handful of routing scalars (`builder`, the `needs_*` flags) actually need machine parsing.

### What changed

- **New `dataviz_mcp/handoff.py`** - the dependency-free tolerant layer. Stages emit markdown
  sections plus a small `routing` block; `parse_routing` reads it leniently and falls back to a
  lenient JSON parse (fence-strip, trailing-comma tolerance, outermost-object extraction) so
  strong-model JSON still works. `expected_sections` / `render_handoff_spec` derive the prompt's
  section list from each stage's `output_schema` (kept as a content checklist, not a wire format).
- **`stage_contracts.py`** - `Stage.routing_fields` + `Stage.handoff_spec()`, a
  `HANDOFF_FORMAT_PREAMBLE`, dropped every "return … against the required schema" closer, and
  `build_stage_adapter` now appends the handoff format + spec.
- **`tester/local_runner.py`** - routing parsed via `handoff`, and the color/precision conditional
  skills are now actually wired (a pre-existing dead path: only annotations/explainer were). Handoff
  files moved `.json` -> `.md`; diagnose/select prompts request the structured-text handoff.
- **`case_manager.py`** (both surfaces, byte-identical) - a tolerant `read_report` and coercing
  `nonempty_text` / `text_list`; `case.json` still read strictly. This relaxes the shape rigidity
  while keeping the cross-referential semantic checks.

### Decision / scoping note

The complex `case_manager` contracts (design-contract maps every finding, etc.) stay JSON but
parse tolerantly, rather than moving to markdown - forcing those cross-referential reports into
prose would be a fragile rewrite for little gain. The markdown handoff is for the LLM-to-LLM stage
artifacts, where the consumer is another model; the machine-validated reports keep JSON with a
lenient parser. Boundary: LLM-to-LLM handoffs = markdown + routing; machine-validated contracts =
tolerant JSON.

### Validation

`pytest -q` (101) and `pytest -q tester/tests` (23) green, plus the new `test_handoff.py`.
`./sync.sh --no-pull` installs both surfaces.

## 2026-08-25 - Drop redundant quantitative axes; match small-multiple grids to the frame

### Context

Two chart failures pointed at the same kind of gap - a rule that existed but was written so it never
fired. A skill-made small-multiples chart kept full quantitative Y axes plus a dense gridline ladder
even though every point was already value-labelled; and a separate repair (the a16z OpenRouter
stacked bar) exposed a layout fumble when it was rebuilt as small multiples.

### Diagnosis

- **Quantitative axis never dropped.** The core rule said, for identity: "remove that redundant axis
  or legend" (active imperative), but for quantitative: "keep quantitative scales ... only when they
  add information the direct labels do not" (passive, default-keep). Three failures compounded: the
  framing asymmetry (drop-unless vs keep-unless), a scope trap (the rule lived inside "identification
  route" language, which reads as identity/naming, so value axes fell outside it), and an escape hatch
  so wide that a scale could always be argued to "add" something. So the intent was there; the wording
  guaranteed it wouldn't act.
- **Grid orientation.** The selector required a grid "sized to the delivery medium" but never said the
  grid's aspect should track the frame's aspect, nor to cap panels for legibility. A tall 3x4 grid in a
  wide 16:9 chat frame passed the letter of the rule while producing cramped panels whose end-labels
  clipped.

### Decisions

- Generalized the redundant-scaffolding test to every channel (axis, scale, gridline, tick, label,
  legend) and flipped the quantitative default to drop-unless, naming the concrete reading tasks that
  earn a scale its place. Encoded as one general principle - no counts, thresholds, or the immediate
  example.
- Added to the small-multiples rule (selector + core viz skill): grid proportions track the delivery
  frame's aspect ratio, and panel count must keep panels legible or the number/medium changes before
  panels shrink.

### Build notes

- Edited both surfaces of `karthik-data-visualization` and `dataviz-selector`; `dataviz-eval:135`
  already carried the general redundancy audit, so it was left as the backstop. Verified codex/claude
  bodies stay byte-identical, ran `./sync.sh --no-pull --validate-only`, then `./sync.sh --no-pull`.
- Test case: repaired `~/Downloads/openrouter.png` (11-series stacked bar) into small multiples with
  direct end-value labels; the new rule dropped every per-panel quantitative axis and gridline while
  the end-labels carried magnitude. Values were reconstructed/illustrative and labelled as such,
  since exact per-model series are not recoverable from the source stack.

## 2026-08-24 - R analysis style: no SQL, right-assign long chains, run-not-knit

### Context

Karthik gave three corrections to his R exploration style, all reflecting how he actually works at the console.

### Decisions

- No raw SQL. Data access uses dplyr backends (`dbplyr`, `duckplyr`/DuckDB, `arrow`); logic goes through dplyr verbs and the backend translates. SQL strings survive only for an unavoidable one-off DDL/config statement with no dplyr equivalent - previously the skill said "raw SQL is fine for setup, views, S3 config, or awkward operations", which was too permissive.
- Right assignment (`->`) is the default for new long chains. Reason he gave: it lets a pipe be run partially, line by line, while exploring. Old notebooks' style stays untouched, so this is a new-code default, not a global rewrite rule.
- Notebooks are for running chunk by chunk, never knitting. Added an explicit rule to drop anything that only serves knitted output (`knitr::opts_chunk$set`, figure sizing/captions, cross-references, knit-ready structure).

### Build notes

- Edited `karthik-r-analysis-style/claude/SKILL.md`, rebuilt the codex copy from the shared body (only the frontmatter differs between the two surfaces), updated `docs/skills/karthik-r-analysis-style.md` and CHANGELOG, and ran `./sync.sh --no-pull`.
- Encoded as generalized rules, not example-specific behaviour.

## 2026-08-24 - Colour selection and significant digits as skills plus MCP tools

### Context

The suite could render, inspect, select, critique and repair, but two everyday decisions had no home beyond scattered prose: which colours a specific graph should use, and how many significant digits its numbers should show. Karthik wanted both as first-class, reusable capabilities - deterministic where the maths is deterministic, judgement where it isn't.

### Decisions (settled with Karthik before building)

- Two new skills (`dataviz-color`, `dataviz-precision`), each backed by MCP tools rather than prose alone.
- Brand is optional and usually arrives as an installed skill: the colour skill scans the session's available-skills list for a `brand`/`style`/`theme`/`palette` name and honours it first, then in-context style, then our accessibility defaults. But even with a brand or recommended set in hand, a specific graph still needs a which-and-how-assigned decision - so `recommend_colours` is a recommender, not just a validator.
- Precision is driven by the spread, not by individual values: derive the uniform rounding place from the column's range (max - min) via a formula, and round every value to that one place. No fabricated precision, no rounding toward rounder-sounding numbers.
- In a repair, the source chart's colours are a *prior*, not a rule: `extract_palette_from_image` samples them (pixel extraction) to seed the palette, then brand and accessibility may override while the semantic mapping is kept.
- Reuse the WCAG contrast code already in `inspection.py` rather than rewriting it; keep the new skills the authority and leave the old craft skills pointing to them (no duplicated rulesets, no thin wrappers).

### Build notes

- Extracted `_relative_luminance` / `_contrast_ratio` into `dataviz_mcp/color_math.py` (names unchanged) and added hue/lightness, Machado CVD matrices, and grayscale helpers. `inspection.py` now imports the shared pair.
- `palette.py` separation metric is lightness-weighted on purpose: hue collapses under CVD and grayscale, lightness survives both, so `separation = Δlightness + 0.4·(Δhue/180)`. Greedy max-min selection with a pinned focal.
- Verified against the plan's examples: `recommend_precision([12483, 9210, 15040])` rounds to hundreds (`12,500 / 9,200 / 15,000`); `validate_palette` on two near-identical blues soft-fails on distinctness + CVD + grayscale; `extract_palette_from_image` on the sector fixture returns the chart's magenta hues. Two naive test expectations were corrected once the validator (correctly) flagged that many light Okabe-Ito colours miss 3:1 on white and some dark pairs collide in grayscale - accessibility on a white ground is genuinely hard, and the tool says so.

## 2026-08-22 - Staging the pipelines so the context stops rotting

### Context

Delivered through a web app, the skills went out as one mega-prompt. `dataviz_mcp/public_repair_contract.py` discovered every `<skill>/codex/SKILL.md` and appended all sixteen into a single creator adapter, so a build call carried brief, extract, critique, selector, table-style, powerpoint, cleaning, analysis-planner and eval at once. The build step has no use for the discovery or evaluation skills; a long single context loses the thread. Karthik wanted each pipeline run as a sequence of separate API calls, each carrying only the skills relevant to that step plus a compact artifact handed forward.

### Decisions (settled with Karthik before building)

- Two staged orchestrators, not one. `dataviz-orchestrator` keeps its name and owns the dataset-to-story flow; the repair flow needed its own. `dataviz-fix` already *was* the repair pipeline (intent -> data -> select -> build -> critique -> eval), written for one context and with no other job, so we **repurposed** it in place rather than renaming or adding a sibling.
- The provider-neutral contract is the authoritative machine layer (a Python module with per-stage skill subsets + JSON schemas); the prose skills carry the reasoning and reference it for the shape.
- No thin wrappers or back-compat shims. The old module was deleted outright and its test rewritten, not aliased.

### Build

- `dataviz_mcp/stage_contracts.py` (new): `REPAIR_PIPELINE` (diagnose+extract -> select -> build -> refine) and `STORY_PIPELINE` (discover -> contract -> clean -> facts -> select -> build -> refine) as ordered `Stage` objects. `stage_skill_bundle` reads only a stage's own skills - the context-rot fix - and `build_stage_adapter` prepends shared guardrails (untrusted image text, frameworks-not-tools, approximate-not-exact, harvested from the old adapter) plus the stage's focused instructions. The build stage swaps `karthik-data-visualization` / `karthik-table-style` from the previous stage's `builder` enum; `chart-annotations` / `chart-explainer` load only when the select artifact asks. Reused `REPAIR_PLAN_SCHEMA`'s blocks, split into a diagnose brief schema and a select design/layout/acceptance schema.
- Deleted `dataviz_mcp/public_repair_contract.py` and its test; wrote `dataviz_mcp/tests/test_stage_contracts.py` whose load-bearing assertion is that each stage bundles only its named skills and none of the others.
- Repurposed `dataviz-fix` and refactored `dataviz-orchestrator` (both surfaces, byte-identical) into staged orchestrators, each written as separate per-stage calls pointing at the contract module. `dataviz-fix` keeps `case_manager.py`. `facts` is a named placeholder until `karthik-evidence-builder` exists.
- Docs: new `docs/plans/staged-pipeline-contract.md`, updated `dataviz_mcp/README.md`, both `docs/skills/*` pages, both skill READMEs, `docs/README.md`, `docs/plans/README.md`, root README, and CHANGELOG.

### Then: no monoliths, everything consistent across codex and claude

Karthik's follow-up was two words of principle - "everything needs to be consistent across codex and claude" and "no monoliths". The skill copies were already byte-identical where it mattered (the diffs are only the deliberate long-vs-short frontmatter `description`; bodies match). The monolith was the tester: `tester/local_runner.py` ran one codex `exec` that opened dataviz-fix + critique + selector + visual + writing at once and did the whole build in a single context - the practical rot the contract was meant to end.

Split it. The creator pass is now three scoped codex calls driven off `stage_contracts`: diagnose (brief+extract+critique) writes `diagnose-NN.json`; select (selector, no image) reads it and writes `select-NN.json` with the `builder` choice; build opens only the chosen builder skill (chart or table) plus the installed writing skill, reads both artifacts, runs the case-manager workflow, and renders the candidate. The blind reviewer was already a separate call. Usage for all three creator sub-calls is recorded under the case-manager's existing `creator` stage enum, so no state-machine change was needed. New runner tests assert the anti-monolith property directly: the build call carries the builder skill but not the diagnosis or selection skills, and diagnose carries neither.

### Verification

48 tests pass (`pytest -q`) and the tester suite is 20 (`pytest -q tester/tests`), including the new per-stage scoping guards. `./sync.sh --no-pull` validated and installed all sixteen skills. End-to-end validation of the staged runner needs a live codex run (`DATAVIZ_ENABLE_LOCAL_RUNNER=1`); the unit tests cover the wiring and scoping.

### End-to-end run (Claude-driven) and a real inspector bug

Rather than the Codex tester, drove the provider-neutral pipeline as Claude on a real sample (the NIFTY 50 vs NIFTY NEXT 50 sector-weight mirror chart), one stage at a time, loading only each stage's skills: diagnose (brief+extract+critique) -> select (selector, chose a dumbbell) -> build (data-visualization+annotations+writing, ggplot2 via the MCP render/inspect) -> refine. The staging held and the artifacts chained. The refine loop earned its keep twice: it caught direct labels clipping into the subtitle (moved them to the Financials row) and then a genuine `LOW_TEXT_CONTRAST` on the orange label (darkened the label text; dots keep Okabe-Ito).

The run also surfaced a real bug in the geometry gate the whole loop depends on. `passes_geometry_checks` was false on a visibly clean chart, and the only failing signal was two `legend_collisions` whose "legend" bbox equalled the plot panel. Traced it to the ggplot layout adapter emitting the empty `guide-box-inside` cell (panel-sized `zeroGrob`, present whenever `guide="none"`) as a legend, so any in-panel direct label false-collided. Fixed in `rendering.py` by skipping empty `guide-box*` cells in the top-level loop; added `test_guide_none_does_not_emit_phantom_panel_legend`. After the fix the same chart passes with `legends: []` and `defects: []`. 49 tests pass.

## 2026-08-21 - "Can't name it" is not "not key": sealing the identity crack

### Context

A hosted repair (dataviz.karthiks.co) again collapsed the many-series stacked chart to a single total column - but through a door the previous guardrails did not name. All prior anti-drop rules blocked reasons about *value* recovery: "values approximate", "read from a screenshot", "unreadable precision", "crowded legend". This run's stated WHY was about *identity*: "the stack contains more distinct colours than the visible legend identifies, preventing reliable category-to-colour recovery", so "model-level trajectories were not reconstructed because the legend does not identify all plotted colours". The model converted "I can't reliably name every category" into "the categories aren't key" and dropped the mix - the whole point of the chart.

Two layers were in play. The output shape (assess source -> recommend -> build -> limitations, under `mode: automatic_critique` with a repair_brief that says "run a complete expert dataviz critique of the source") is the old critique-first flow, not the repo's forward-design flow - that orchestration lives in the hosted app, not this repo, and needs a redeploy/app-side change to pick up the brief-first flow. Independent of that, the skills themselves had one unsealed crack.

### Fix

Generalised the "difficulty of recovery is never grounds to drop a message" rule in `dataviz-brief` and `dataviz-critique` (both surfaces) so it explicitly covers a category's *identity*, not only its *value*: an unmappable colour or a legend that names fewer categories than the chart encodes is a form weakness, not a licence to delete the dimension. Remedy stated inline: keep the categories, name the ones the source identifies, mark the rest generically - imperfect labels still carry a composition/comparison message. `dataviz-extract` now asks for one member per visually distinct series, naming what it can and labelling the rest generically, and forbids shrinking the category count to only the named series. Kept general (no "models"/a16z wording) so it does not overfit the triggering case.

## 2026-08-21 - A well-formatted table is a visualization too

### Context

The suite could only ever answer with a chart. Given a badly formatted table it produced a chart; given data that would read better as a table it produced a tidier chart, because no skill treated a table as an option and none owned table craft. Karthik's own table principles - emphasis, decimal alignment, precision keyed to variance, column widths, minimal rules, tabular figures, deliberately-scoped conditional formatting - lived nowhere in the repo.

### Decision

Four forks were settled with Karthik before building: a new standalone skill (`karthik-table-style`) rather than bloating the chart-style skill; full render + inspect rather than code-only tables; and, after the render stack turned out to have no headless/screenshot path to reuse (only `ragg` for ggplot and matplotlib Agg), tables render as `grid`/`tableGrob` objects through the existing `ragg` path - zero new dependencies, no headless Chrome - instead of adding `webshot2`/chromote. `gt` stays the recommended idiom for delivered HTML tables; the gated raster uses grid.

### Build (five phases, one commit each)

1. `karthik-table-style` skill - both surfaces byte-identical, folder + surface READMEs, generalised heuristics (no example-specific rules).
2. `dataviz-selector` - an explicit "Table or chart?" section and a table verdict routing to the new skill; a table named a legitimate cold verdict in a repair.
3. `dataviz-fix` - a `form = table` exit that builds via the table skill and gates via the grid/ragg raster.
4. MCP - `render_and_inspect_chart` gains `content="table"`. The key realisation: `ggplotGrob()` already produces a gtable, and a `tableGrob` *is* a gtable with the same `$layout/$grobs/$widths/$heights`, so the existing layout-extraction machinery works on a table almost unchanged. The R runner now accepts a gtable return and, for table content, captures each cell's text, font size, and background fill at its exact track bbox. One real bug surfaced and was fixed: `resolve_tracks` created a zero-length unit vector when no track was a `null` unit (tables have all-fixed widths), so it now guards that subset. Added a `table_fixture.R`, three tests, and a `table_rendering` probe capability. Full suite: 34 passed.
5. Docs/plumbing - root README (15→16, layout, per-skill section, install lists, renderer-policy note), `docs/skills/` index + new page, orchestrator routing, CHANGELOG, this entry.

The honesty boundary is explicit in the coverage report: cell bounding boxes, text, and fills are exact from the gtable tracks, but decimal-point alignment and in-cell overflow are not automatically verified and must be read from the rendered raster.

## 2026-08-21 - Stop the whack-a-mole: repair is forward design, not critique-plus-patch

### Context

Three consecutive prose patches to the repair flow (the three DEVLOG entries below this one) each fixed the last symptom on the a16z "Weekly usage of models across OpenRouter" chart and exposed the next: dropped the ten model categories → dropped them with a justification → kept all ten but re-rendered the same stacked bar. Every patch was a better sentence; none changed the outcome. They all traced to one root cause: the flow *started by critiquing the source chart*, which anchors everything on the existing image, and `dataviz-selector` was only a conditional downstream helper with an "unless the form is clearly correct" escape hatch. So the path of least resistance was always "re-render the source form, tidied." Prose guardrails cannot overcome the ordering.

### Decision

Stop patching sentences; change the order. Repair becomes forward design informed by the source, not critique-plus-patch. New six-step order:

1. **INTENT** (`dataviz-brief`, new skill) - key messages + required content, explicit drops, audience, story, authoritative constraints, thin keep-notes, and the edit-vs-redesign mode.
2. **DATA** (`dataviz-extract`, new skill) - the full period-by-category table, in parallel with intent.
3. **SELECT** (`dataviz-selector`) - run cold on intent+data; the source form gets no vote; no "clearly correct" escape hatch in the redesign path.
4. **BUILD** (`karthik-data-visualization` + `chart-annotations` + headline/subhead).
5. **CRITIQUE** (`dataviz-critique`) - now a downstream checker only: does the candidate carry the step-1 intent, and is it a good chart? In-context, ≤2 passes.
6. **EVAL** - one blind `dataviz-eval` subagent on the converged candidate. Unchanged.

Four forks were confirmed with Karthik before implementing: intent-extraction is its own new skill (not a critique mode); the edit-vs-redesign fork lives in the brief's output; data-extraction is its own new skill; and source-diagnosis survives only as a thin "anything worth keeping?" pass feeding intent, not a fault-list.

### What moved

- `dataviz-critique` lost its "step 1 of repair" role and its design job (key messages + required content moved up into `dataviz-brief`). It keeps the standalone "what's wrong with this chart?" path and becomes the downstream checker in repair.
- `dataviz-selector` was promoted from optional downstream helper to the forward-design engine at step 3, run cold.
- `dataviz-fix` orchestration rewritten to the six-step order; the bounded-edit path stays anchored to the source form and skips selection.
- Two new skills, both surfaces, byte-identical. `docs/design/dataviz-fix-repair-flow.md` rewritten; new skill doc pages; indexes, folder READMEs, root README, and CHANGELOG updated.

The general principle - repair = forward design from intent+data, source form has no vote, preserve the message not the form - is deliberately not overfit to the a16z chart. No "always small multiples for stacks" rule was encoded; the selector picks the form the data shape and message want, cold.

## 2026-08-21 - Bind the public creator to the canonical skills

The public website updater was correctly fast-forwarding and reinstalling this repository, but the website imported a handwritten `CREATOR_INSTRUCTIONS` constant that had not changed with the latest skill commits. The checkout was current while the behaviour was stale.

`dataviz_mcp.public_repair_contract` now discovers every top-level `<skill>/codex/SKILL.md` directly from the current checkout. There is no list of individual skill names: new, renamed, removed, and revised skill entrypoints change the assembled bundle automatically. A runtime adapter translates relevant guidance into the website's existing one-creator execution boundary: it does not attempt unavailable skill or subagent calls, does not let unrelated skills expand the task, and still requires an inspected `/mnt/data/repaired.png`. The bundle publishes the core Git revision, discovered paths, and content fingerprint. Tests exercise discovery against synthetic additions rather than merely checking a maintained list. The old embedded handwritten fallback has been removed; without canonical repository skill sources, import fails closed.

## 2026-08-21 - Preserving the message is not preserving the form

### Context

After the creator-binding fix deployed and the drop guardrails went live, the hosted repair stopped collapsing the a16z chart to a total - it kept all ten model categories. But it re-rendered the *same stacked bar*: cleaner canvas, legend moved above the plot, "Others" muted, colours retained. That is the form Karthik flagged in the very first message of this thread - a ten-deep stack where you cannot follow any single model's trajectory. The previous guardrail ("the form declares its messages", "preserve the dimension") had been read as "keep the stacked chart type." Preserving the *data* got conflated with preserving the *encoding*.

### Fix

- **Third guardrail: preserving the message is not preserving the form.** The data must survive; the encoding must not, and often should not. Re-rendering the same chart type is not preservation when that form was what made the message hard to read. A many-series stack whose message is per-series comparison or trajectory becomes small multiples, direct-labelled lines, or a ranked/indexed view - not a tidier stack.
- **Tightened the `dataviz-selector` trigger** in `dataviz-fix`: a many-series stacked bar/area is never "clearly correct" enough to skip selection when the message is per-series comparison; expect a form change, not a re-render.

Note the arc across the three same-day edits: drop-the-categories → keep-but-justify-the-drop → keep-but-keep-the-bad-form. Each patch fixed the last symptom. The general principle underneath (preserve the message, choose the form that makes it legible) is not overfit to this chart, but the three-step chase is a reminder that the real lever may be biasing reconstruction toward a form change whenever the source form is the diagnosed weakness, rather than patching the judgment prose again.

## 2026-08-21 - "Hard to read" is not "not key": guardrails on the drop judgment

### Context

The hosted repair (dataviz.karthiks.co) still collapsed the a16z stacked-by-model chart to a single grey total column - but this time with an *explicit reason*, which the previous change had made mandatory. Its stated WHY: "many thin stacked segments and long legend do not support reliable model-by-model comparison" and "without inventing unreadable category precision." So the reasoned-drop slot we added became a rationalization slot: the model converted "hard to recover exact values from a screenshot" and "legend is crowded" into "the categories aren't key," and dropped the mix - the entire reason a stacked-by-model chart exists.

### Fix

Two guardrails on the key-messages judgment in `dataviz-critique` (mirrored into `dataviz-fix`):

- **The form declares its messages.** A stacked, multi-series, or faceted chart has the category comparison as a key message. The primary encoded dimension (colour/stack/facet) is presumptively key unless the prompt redirects. Collapsing to a single total deletes a key message.
- **"Hard to recover" is not "not key".** Approximate screenshot values, crowded legend, too many categories, "unreadable precision" are reasons to pick a *better form* (small multiples, direct-labelled lines, top-N plus "other", share-of-total), never to delete the dimension. Source illegibility triggers redesign, not removal. Approximate-but-labelled values still carry the message.
- Tightened "explicit drops": a drop is legitimate only when the information serves no key message, not when it is inconvenient to recover or render.

### Deploy note

These are source-repo + local skill edits. The hosted site now discovers skills from the checkout (see the creator-binding entry above), so it picks these up on its next restart/redeploy - but not before. Until it restarts, dataviz.karthiks.co keeps reproducing the old behaviour.

## 2026-08-21 - Preservation as a critique judgment, not a keep-everything rule

### Context

An a16z stacked-bar chart (weekly OpenRouter usage, ~10 model categories by colour) came back from a repair with the category breakdown dropped - the key information gone. Traced the failing to the default `dataviz-fix` path: (1) data inference was one vague line ("infer the raw data as usual") with no requirement to capture every encoded dimension, so the maker could infer the total envelope and never register 10 series; (2) the "preservation mapping" guard that would catch a dropped dimension lives only in `karthik-data-visualization`'s audited-contract mode and is off in the default path; (3) that guard's wording was abstract ("observable state proves it did not regress") and had never been understood or exercised.

### Key design decisions

Designed collaboratively, one question at a time (Karthik's call on each fork):

- **Preservation is a judgment, not a rule.** First cut was a hard "keep every category" rule; Karthik rejected it - the real task is reading the source for its *key messages* and deciding what must be shown to carry them, which can even mean several charts (whole + parts). "Keep everything" is wrong; "keep what matters, out loud" is right.
- **The judgment lives in `dataviz-critique`.** Not a new skill. Critique already carries the trifecta and message read; it now also outputs key messages + required content per message. New section, reader-facing template rows, and audited-JSON fields (`key_messages`, `dropped_as_not_key`, `chart_count_hint`).
- **Critique names messages + required content; reconstruction owns the output.** Critique does not lay out charts; it decides what matters. Reconstruction decides chart count, decomposition, and form.
- **Drops must be explicit.** Non-key information may be dropped, but critique names it and says why. Silence is the a16z bug (the breakdown vanished with no decision); a reasoned drop is fine.
- **Full-table data inference stays.** You cannot judge what is key without reading all of it, and the parts view needs the per-category values - so step 1 still infers a value for every period × every category.
- **Eval stays final-image-only.** Considered feeding eval the source image to catch dropped information; rejected - preservation is owned upstream by critique + rebuild, not backstopped by the reviewer. Eval keeps artifact + brief.

### Files touched

- `dataviz-critique/{claude,codex}/SKILL.md`, `dataviz-fix/{claude,codex}/SKILL.md`, `dataviz-fix/README.md`, `docs/skills/dataviz-fix.md`, `docs/skills/dataviz-critique.md`, `docs/design/dataviz-fix-repair-flow.md`, `CHANGELOG.md`.

## 2026-08-21 - Repair flow redesign: one chat, one spawn

### Context

After removing the per-iteration `dataviz-eval` loop for speed, the repair flow regressed in some cases and was "too respectful of the input image". Investigated the recent commits (`51fb61c` eval-loop removal, `8bf4c62` overfit removal) and found the diagnostic substance intact in the underlying skills but the `dataviz-fix` fast path either contradicting them (a "semantic preflight" ban colliding with `karthik-data-visualization`'s required semantic scan) or narrowing them (reinspect only changed regions), and the `chart-annotations` skill dropped from the flow entirely.

### Key design decisions

- **Skills are not sessions.** Invoking a skill loads instructions into the current chat; a subagent is a separate session. The 15-minute iterations came from spawning an independent `dataviz-eval` subagent on every loop turn, not from the checking itself.
- **Default = one chat.** Source critique and the export checker loop run in-context using `dataviz-critique`. Cheap, non-independent, honest about it.
- **One spawn per flow.** Exactly one blind `dataviz-eval` subagent runs once on the converged candidate to recover independence at bounded cost. Fed only the artifact and a brief (prompt, inferred style, headings, message) - no source image, no maker intent or code. Skipped for purely literal/cosmetic edits.
- **Two-pass cap** on the in-context checker loop (a deliberate reintroduction of a bound removed in `814bf4d`).
- **Image not sacred, prompt authoritative.** Redesign freely against the image, biased toward redesign; honour every prompt constraint throughout.
- **Re-wired `dataviz-selector` (default-on) and `chart-annotations` (default-on for redesigns).**
- **Writing/brand skill is conditional** - not in this repo, invoked only if installed.

### Files touched

- `dataviz-fix/{claude,codex}/SKILL.md`, `dataviz-fix/README.md`, `docs/skills/dataviz-fix.md`, `CHANGELOG.md`.

## 2026-08-15 - Metadata-first MCP rendering and inspection

### User prompts

> "Skills contain judgement, analytical method and policy. MCP should provide reliable capabilities underneath them."

> "I care more about a useful inspection primitive than about fancy MCP completeness."

> "properly document all the process and changes, and then commit and push. all in the same repo only"

> "since the skills had changed on origin/main before we wrote the MCP, is there any bugs?"

> "commit and push with proper documentation, then deploy to the client runtime"

> "should the MCP for render_chart be ggplot based, given that my design aesthetic calls for that?"

> "make sure the readme is proper so that anyone just pointing their LLM at the repo can get full value"

> "henceforth in this folder, whenever we make some changes, automatically commit and push to github, and deploy to the client runtime. put that into memory"

### Work done

- Audited the full skill stack, repair state machine, local runner, tester artifacts, docs, and 39-test baseline before designing the MCP boundary.
- Added `render_chart`, `inspect_rendered_chart`, and `compare_chart_artifacts`; deferred profiling and analysis execution because the repo has no reusable implementation to wrap yet.
- Made render metadata the primary geometry source and the exact PNG the source for dimensions, hashes, and pixel comparison. Raster-only inspection now stays explicitly incomplete.
- Bound render bundles and inspection reports into case schema 10. Internal metadata, artifact, inspection, and evaluation hashes must agree, and known deterministic defects now block `Send`.
- Added deterministic defect fixtures and a coffee-price regression through the real case state machine: the bad layout reaches `Revise`, the placement-only repair reaches `Send`, and revision comparison records the improvement.
- Documented the architecture, generation and repair sequences, tool contracts, bundle lifecycle, portable Codex/Claude case paths, client registration, coverage limits, and verification process in the same repo.
- Documented the former client deployment as two explicit surfaces: synced skills and an isolated MCP 2.x stdio process.
- Fixed two deployment issues found on the real host: its system Python lacks `ensurepip`, and the package's test extra omitted the tester's FastAPI dependencies. A bundled Python created the separate environment, and `.[test]` installed the complete suite.
- Deployed the pushed commit to `server`, synced all 13 repo skills, registered `mcp_servers.karthik_dataviz`, restarted the active gateway, and verified 62 host tests, three direct stdio protocol tests, installed-skill parity, and the packaged case-manager runtime.
- Separated renderer infrastructure from visual style. The current Matplotlib geometry adapter no longer gets to force backend translation; project-native code is preserved and new Karthik-style static charts prefer R/ggplot2 where available.
- Turned the root README into a practical entry point for agents and third-party users, including the exact skill reading paths, two-part installation, generic client commands, renderer trade-offs, trust boundary, and current MCP coverage.
- Added tracked `AGENTS.md` and `CLAUDE.md` repository instructions so completed maintainer changes default to validation, commit, push, and exact-commit client deployment. The rule is scoped away from third-party clones and stops on ambiguous worktrees, failed tests, or unsafe remote state.

## 2026-08-12 - Scope-safe chart repairs from live feedback

### User prompts

> "go through the data-visualization conversations and see what possibly needs fixing in these skills, based on my feedback to mistakes; use local files for testing"

### Work done

- Reviewed ten live dataviz-repair cases and separated chart-design mistakes already covered by the skills from a remaining loop defect: narrow requests and preservation requirements were prose, not release checks.
- Added structured intake checks for additions, removals, relocations, and preservation. Later user feedback can now supersede a conflicting evaluator action without deleting the audit trail.
- Made the requested edit boundary authoritative in the fixer, evaluator, local runner, and tester. Untouched regions are regression checks; pre-existing out-of-scope defects are recorded as baseline concerns rather than added to the required work.
- Forward-tested the change on the local Zerodha VIX chart. The first cycle preserved the chart and removed the legend but found one label collision; the second moved only that label and received `Send`. Karthik then caught a missed requirement: the direct band labels belonged on both panels, not only the close-up. A third cycle added all three labels to the decade panel without changing anything else and received `Send`.
- Converted that miss into a panel-completeness rule: a shared legend replacement must enumerate and verify every applicable panel, facet, row, or series rather than passing after the easiest instance.
- Expanded the case-manager and tester regression suites and validated all 13 public skills.

## 2026-08-11 - Bounded repair loop and local tester

### User prompts

> "we need to loop engineer this properly so it doesn't go off into infinite loops"

> "we need the ability to give more prompts on maybe the audience, the purpose, the hypothesis, the message"

> "then to deploy a web app where people can use their own API keys and test this out"

### What changed

- Replaced the implicit prompt loop with explicit states, transition records, stopping reasons, configurable budgets, duplicate-artifact checks, no-progress detection, and best-candidate preservation.
- Made audience, purpose, question, hypothesis, message, medium, delivery details, and constraints editable and versioned. Evaluations now identify the exact context version they used, and changed context cancels or supersedes stale review work.
- Added token, cost, latency, and call telemetry without flattening gate results into one score.
- Converted each user correction into a structured acceptance check: target, current state, required state, and reader consequence.
- Added a localhost FastAPI case console with image paste/upload, context editing, feedback, manual candidate uploads, artifact comparison, limits, stop/resume, and history.
- Added an opt-in local Codex runner. Each user action starts exactly one creator process and one fresh blind-review process against the checked-out skills; the UI never starts the next revision automatically.
- Ran the first real local cycle on the problematic 30-sector chart. It produced one candidate and one independent `Send` verdict in 337 seconds. The candidate kept row labels beside their bar endpoints, removed the unexplained Banks emphasis, used one neutral categorical colour, and made the loss-gain asymmetry the title claim.
- The live run exposed two workflow defects before deployment: the initial prompt was swallowed by the CLI image argument, and the outer development sandbox blocked nested Codex startup. Both failures consumed zero model tokens and were retained as stopped/blocked transitions before the successful resume.
- The successful cycle reported 688,535 cumulative CLI tokens, including 590,592 cached input tokens. That showed that a cumulative token ceiling cannot interrupt one model call and that the tester needs a measured preflight estimate. Added the estimate, moved build checks before calls, and made the wrapper own artifact and verdict transitions.
- Karthik rejected the first `Send` because exact direct labels still sat beside a redundant x-axis and gridlines. The second cycle removed both, retained the meaningful zero baseline, and kept dense row labels at regular weight; Karthik accepted it.
- Classified the first `Send` as an ambiguous evaluator rule. `karthik-data-visualization` already required quantitative scales and references to add information, but `dataviz-eval` made duplicate categorical identity more explicit than duplicate quantitative scaffolding. Tightened only the evaluator rule and kept it conditional on the reading task rather than banning axes on directly labelled charts.
- Kept raw provider adapters, bring-your-own-key handling, stronger isolation, and private deployment as separate milestones.
- Added 26 regression tests across the case manager, tester API, and local-runner orchestration.

## 2026-08-10 - Dataviz eval framework rebuild

### User prompts

> "now let's fix the dataviz-eval skill. it was an ad hoc draft. build it properly from my principles and prior dataviz conversations, and check the 'measuring good' PDF"

### What changed

- Reconstructed the evaluation principles from four repair cases, 28 chart iterations, and the associated user feedback.
- Used Vikram Nayak's Fifth Elephant 2026 talk to separate creator, expert reviewer, and audience reviewer roles and add an offline benchmark method.
- Rebuilt `dataviz-eval` around blind reads, six hard gates, four verdicts, a minimum pass set, and chart-spec operations instead of vague feedback.
- Added a failure taxonomy, gate anchors, representative golden-set guidance, inter-rater calibration, regression reporting, and rules for when a repeated failure should change a skill.
- Forward-tested the skill on four raw repair artifacts. It caught a mistranscribed data row, lost provenance, thumbnail failures, and a broken slopegraph export; a second pass also learned to scope repair checks to source fidelity and not fail an accepted chart on an invented Telegram width.
- Made `dataviz-eval` a required gate inside `dataviz-fix` rather than an optional companion mention. Added deterministic evaluation records to every case packet and explicit routing for `Send`, `Revise`, `Redesign`, and `Not evaluable`.
- Audited the first live full-pipeline run. The evaluator falsely passed a floating FY20 label and a legend/mark colour mismatch, only the first of four iterations was evaluated, HTML was logged instead of the attached screenshot, skill files were changed mid-loop, and several replies omitted the chart. Added deterministic guards and literal edit checks for each failure.
- Added the missed visual diagnosis from that run: totals on stacked bars did not make the intermediate components readable, yellow against white was unacceptable, and distinct legend colours were useless when the plotted segments used a different mapping. Routed these rules to selector, implementation, and evaluation rather than the repair umbrella.
- Replaced the narrow yellow-on-white fix with a full colour system that keeps Tufte's hierarchy intact: focal colour plus grey context, data-type-aware scales, stable semantics, restrained saturation, colour-independent decoding, practical contrast targets, and export checks in grayscale, compressed, and colour-vision-deficiency views.
- Updated both Codex and Claude surfaces, human docs, changelog, and packaging rules for the new runtime reference.
- Audited a later live run where the creator loaded `dataviz-eval` but gave all three of its own exports six `Pass` ratings. The final image still contained colliding text, uncertain label-to-mark pairing, large relationship-breaking gaps, and an unexplained focal colour.
- Replaced self-review with a fresh independent reviewer and a structured, artifact-hashed report. `case_manager.py` now rejects `Send` unless all six gates and five evidence-backed release checks pass.
- Kept the repair generic: the reusable rules concern visual integrity, relationship traceability, spatial economy, encoding semantics, and delivery robustness. The failed sector chart remains a regression artifact; no sector name, chart type, colour, canvas size, or fixed threshold entered the skills.

## 2026-08-10 - Dataviz eval gate and documentation pass

### User prompts

> "document these new skills and today's changes explicitly as well and push them to the GitHub"

### What changed

- Added the `dataviz-fix` repair loop and its persistent case manager for originals, iterations, feedback, acceptance, and skill diagnosis.
- Fixed the pushed repair-loop bundle: `case_manager.py` had been hidden by the repo-wide private-script ignore rule even though `dataviz-fix` invokes it at runtime.
- Added validation for missing or ignored runtime scripts and repaired the thirteen-skill navigation indexes.
- Added the initial `dataviz-eval` inspection gate and documented it in the public skill index.
- Updated the dataviz skill stack with inspect-revise-render, geometry-before-type, and export-vs-viewport guidance.

## 2026-08-03 - Chart explainer skill

### User prompts

> "next i want to build a skill to explain a data exploration. like sometimes i tell claude / codex \"build a notebook to help explore this data\". and the thing is because i'm not running the explorations myself, i don't know what hte insight in the data is. rather - when someone else sees a dataviz i've made, i'ts difficult for htem to know what teh message in it is. this has nothing to do wtih the text on the dataviz itserlf - this is about accompanying / explaining. think about sending a graph along with an email (2 lines per graph only; not too long). it could also apply to a table etc. i need you to build a skill for this. there are 2 data sources for this. one is - my own Rmd files wehere i'e explored data and written notes. the seoncd are my Mint articles (in ../Mint) where i've written articles along with graphs etc . first gather material etc. and ask clarifiing questions, and then buikld the skill. don't build straight away."

> "5 verdict types is too narrow. i only need guidelines that the LLM caan then improvise upon"

> "ok do it"

### Where the material came from

Two corpora, and they turned out to teach different halves of the same skill.

**210 `.Rmd` files across `~/Documents/work`.** Ranked by prose volume outside code chunks, then the prose immediately following plot-producing chunks was extracted. Most of it is forward-looking - "Let's look at orders by date by commodity" - and useless. The valuable residue is the small set of terse verdicts he writes after seeing a plot:

```
No signal here.
No real correlation between rejects and routes.
Clusters seem very very similar. So not much information from them.
One is larger than the other, that's all.
Interesting that some commodities are not ordered much on Sundays.
In general, it seems like our prices are less volatile than BigBasket.
Or is this just a data collection issue?
```

These are the source of the null-verdict rule. In an exploratory notebook the honest answer is usually "nothing here", and the notebooks prove he writes it that way.

**614 files in `~/Documents/work/Mint`.** 145 sentences containing a figure or chart reference were extracted from the `.docx` files by unzipping `word/document.xml` and stripping tags. This is where the two-line contract came from. The consistent shape is a claim sentence with the figure reference welded on, followed by one payoff sentence:

```
Debit cards were swiped at points of sale 234 million times in November, nearly
twice the monthly average from the first nine months of the calendar year (Figure 2).

Figure 4, however, suggests otherwise - the number of wickets lost per innings has
come down over the years.

Until then, the average rate of scoring during the slog overs of the chase was just
over eight runs per over. In 2014, however, that average jumped up to over 9 runs
per over, and has stayed there.
```

Every number in the Mint corpus carries an anchor. "234 million" never appears without "nearly twice the monthly average". That observation became the hardest rule in the skill.

The corpus also showed a pattern worth encoding rather than banning: sentences like "Figure 1 shows a scatter plot of marginal and effective tax rates for different countries" are weak alone, but he always pairs them with a payload sentence immediately after. That is the orientation exception - line 1 may orient, but line 2 must then carry the claim.

### Decisions taken

- **Two lines, hard.** Line 1 is the claim with an anchored number; line 2 is exactly one of contrast, consequence, or caveat. Rejected: a flexible length that scales with the chart's complexity. The constraint is the point - it forces a decision about what the exhibit is for, and the request was explicitly "2 lines per graph only".
- **Guidelines, not a taxonomy.** The first draft classified every note into five verdict types (signal, reversal, regime change, no signal, plumbing). Karthik rejected this as too narrow. The five survive only as a non-exhaustive prompt list, explicitly flagged as "to loosen your thinking, not to classify into". The instruction that replaced them: say out loud what the chart is actually saying, then compress. Reason: a menu of five produces notes that fit the menu, and most real charts say something that is not on it.
- **Nulls are mandatory output.** "Nothing here" is a required capability, not a permitted one, with two sub-rules: say what you looked for and did not find, and never upgrade weak to moderate. This is the failure the skill exists to prevent - an agent-run notebook of dead ends being written up as a deck of findings.
- **Compute, never eyeball.** When data is available every number is computed from it. Rejected: allowing numbers read off a rendered chart when they are "clearly legible". See the test section below for why.
- **Register asked once, defaults to note-to-self.** Three registers - self, colleague, client. Register changes wording only; it never softens a null into a maybe. Rejected: inferring register silently from the folder or the presence of an email draft, which fails quietly and in the expensive direction.
- **Chart quality is out of scope.** A bad chart still gets a note, with no critique attached. `dataviz-critique` and `chart-improver` own that. Rejected: a one-line "this reads better as a slope chart" flag, on Karthik's call - keeping skills separate beats a helpful aside.
- **Batch mode refuses to build a narrative.** Twelve plots get twelve notes in figure order, no summary paragraph, no reordering, no dropping the nulls. This is the same failure as the null rule, one level up.
- **`examples.md` ships inside each surface directory**, not at the skill root. `sync-skills.py` only copies `<skill>/codex/` and `<skill>/claude/`, so a root-level `references/` folder is repo-only and invisible to the installed skill. The example bank has to be readable at runtime, so it is duplicated across both surfaces and the edit rule in the folder README says to update both.

### Testing the skill on real charts

Ran it against `india-ias-officers/ias-profile.csv`, a dataset not used to build the skill. Three quick charts: female share of allotments by year, median age at joining by year, domicile distribution.

The compute-don't-eyeball rule earned its place immediately. The first pass at chart 2 sampled the head and tail of the series:

```python
a = d.groupby('Allotment_Year').age.median()
print(a.head(3).to_dict(), a.tail(3).to_dict())
# {1970: 24.4, 1971: 24.0, 1972: 24.3} {2018: 28.1, 2019: 26.5}
```

which reads as a clean, publishable finding: median joining age crept up from 24 to 28. Forcing the full series out instead showed medians above 47 across the whole of the 1990s and 2000s, peaking at 52.5 in 2005-06. `Date_of_Joining` is not the entry date for most cohorts. The eyeballed version would have shipped as a finding; the computed version produced a plumbing note telling the reader not to use the field.

The three notes the skill produced:

```
1. Female share of IAS allotments rose from ~10% in the 1970s to 26% in the 2010s.
   The rise stopped around 2013 - it has bounced between 16% and 34% since, with no
   further trend.

2. Median age at joining reads 24 in 1970 but 47-52 through the 1990s and 2000s.
   Date_of_Joining is not the entry date for most cohorts - don't use this field
   until that's resolved.

3. Domicile is blank for 21% of the 12,134 officers - more rows than any state
   except Uttar Pradesh (1,471).
   Any domicile ranking off this is provisional.
```

Two of three are caveats rather than findings, which is the correct ratio for a cold dataset and the thing a narrative-building version of this skill would have hidden.

### Follow-up: firing on notebook-build requests

> "this chart explanation skill needs to be invoked whenever i ask an LLM to \"build an exploratory notebook for this data\" etc. as well"

The original description only matched requests that mention a chart. A notebook-build request mentions no charts and the plots do not exist yet, so the skill would have been invoked - if at all - as a cleanup pass after the notebook was written, which is too late: the notes have to come from each chunk's computed output, not from a later reading of the finished file.

Three changes:

- **Description widened** on both surfaces to name "build an exploratory notebook", "explore a dataset", and "produce analysis someone else will read" as triggers. The Claude description was rewritten too, and stays under the 200-character validator limit at 161.
- **New section, "Exploratory notebooks you are building"**, establishing that in this case the notes are the deliverable rather than a later pass. Five rules: note in markdown under every plot chunk; written after running the chunk, from its output; note-to-self register by default; nulls stay in with their plots; no findings summary unless asked.
- **Cross-reference added to `karthik-r-analysis-style`**, in the "Prose style inside notebooks" section. That skill's existing note examples are all lead-ins ("Let's only look at stores with enough days") - what you are about to look at. It had nothing about what a plot turned out to show. The new subsection marks `chart-explainer` as a required sub-skill for after-plot notes, and repeats the register constraint so the two-line note does not arrive as scaffolding in a skill that bans scaffolding headings.

`karthik-r-analysis-style` has no copy in this repo - it exists only as installed files under `~/.claude/skills` and `~/.codex/skills`, which differ slightly from each other. Both were patched by anchor rather than by overwrite. If it ever gets a source repo, that edit needs to move there.

### Follow-up: analysis-style skill into the repo, and a consistency pass

> "add that analytics style to the repo. and make sure all of this is consistent in boht claude and codex"

`karthik-r-analysis-style` is now `karthik-r-analysis-style/{codex,claude}/` in this repo, imported from the installed copies. Both `SKILL.md` bodies were already byte-identical - only the frontmatter differed, in exactly the way this repo's convention expects (Codex gets the long trigger-rich description plus `metadata.claude-description`; Claude gets the short one). The `references/` folder ships inside each surface directory rather than at the skill root, because `SKILL.md` reads `references/style-observations.md` and the two audit files at runtime, and `sync-skills.py` only copies `<skill>/codex/` and `<skill>/claude/`. Same reason `chart-explainer/examples.md` sits where it does.

One repair on the way in: the Claude description contains a colon (`Karthik-style R analysis: local-precedent...`), which is invalid as a bare YAML scalar. It had survived as a folded block scalar in the installed file. Now JSON-quoted on both surfaces.

Then an audit across all eleven skills, on two axes:

```
skill                            claude_desc_len  mirror_ok  body_identical
chart-annotations                       112         fixed         True
chart-explainer                         161         True          True
dataset-question-generator              100         True          True
dataviz-critique                         91         True          False   <- flagged
dataviz-orchestrator                    110         fixed         True
dataviz-selector                        122         fixed         True
karthik-analysis-planner                136         True          True
karthik-data-cleaning                   145         fixed         True
karthik-data-visualization              147         True          True
karthik-powerpoint-style                175         True          True
karthik-r-analysis-style                128         True          True
```

- **`mirror_ok`** - whether the Codex file's `metadata.claude-description` matches the description the Claude file actually ships. Four had drifted: two were missing the field entirely, and two carried superseded wording (`chart-annotations` still said "annotate" where the live description says "mark"; `dataviz-selector` carried an entirely different sentence). Mirrored the live Claude description in each case, since that is the one a running agent reads. Documentation-only.
- **`body_identical`** - whether the two surfaces teach the same thing. Ten of eleven match. `dataviz-critique` does not: the Claude body is a genuinely condensed rewrite, 122 lines against 186, with sections merged and the "Inputs to seek or infer" list dropped. That is a behavioural divergence, not drift, and reconciling it means choosing which version is correct. Left alone and raised with Karthik rather than resolved silently.

Also deleted the memory note saying this skill has no source repo. It does now.

### Wiring

`dataviz-orchestrator` was left alone. The orchestrator ends at a critiqued chart; narration for an absent reader is a separate job and Karthik did not ask for the loop to be extended. Worth revisiting if the orchestrator starts producing multi-chart outputs meant to travel.

## 2026-08-03 - Chart annotations skill

### User prompts

> "i want to build a \"chart annotations\" skill. how do we go about this? basically - i think wiht LLMs, now it's good practice to mention in a dataviz what the clear message is. actually mark it out and write a comment there. however, tehre is skill involved in this - how do you figure out hwat to hightlight? hwo do you figure out what is more significant? and then how do you figure out how to write the label concisely? i think tehre must be enough material on this c omputer (or in this folder) that will point you to how to build this. as a first step gather all of it, and summarise the insights. and then we can go about building the skill."

> "this should be a standalone skill. and the dataviz orchestrator in some sense needs to include this. let's also resovl the gaps you've mentioned (ask one by one) before you build the skill"

### Where the material came from

The gather step found existing material scattered across four places, and one of them turned out to be the whole spine of the skill:

- `bangalore/weather/fewshot_annotations/distilled_editorial_rules.md` and `fewshot_prompt_draft.md` - a reviewed bank of 12 historical weather windows where Karthik wrote the preferred lead framing for each and noted what the model should learn. This already contained a signal hierarchy, negative guidance, and headline templates. It is the source of the significance ladder and the concentration check.
- `bangalore/weather/bangalore_weather_update.R` (system prompt, ~line 610-625) - the production wording constraints: under 18 words, one claim, numbers tied to their named window, banned dramatic and bureaucratic registers, "observant resident not lab report".
- `dataviz-selector` - the geometric candidate list: knee-bends, inflections, local extrema, temporary peaks, thresholds, events.
- Zerodha workshop material (`what-makes-good-dataviz.md`, `insight-to-visual-brief.md`) - the eraser test's explicit carve-out that annotations needed for comparison must not be erased, and the evidence → claim → comparison → visual job chain.

Roughly 200 `annotate()` / `geom_text()` calls across 58 R files supplied the mechanics but no written rules, which is why placement and visual weight had to be decided fresh.

### Decisions taken (four gaps, resolved one at a time)

- **Title vs annotation.** Title states the claim in words; annotation locates it on the evidence. Rejected: neutral title with the claim living entirely in the annotation, and a medium-dependent rule. Reason: the same sentence appearing twice is the failure being prevented, and a single rule is easier to hold than a per-medium branch. A standalone-travelling chart is an explicit exception, not a second rule.
- **How many.** Hard cap of one primary plus at most two supporting; more surviving candidates means split the chart. Rejected: strictly one per chart (under-annotates real S-curves), and scaling with chart type (too soft to enforce).
- **Visual weight.** Two tiers - primary takes accent and bold, supporting stays grey and small. Rejected: annotation always quieter than data, which would have made the primary annotation too weak to lead the eye.
- **Connectors.** Proximity first, hairline segment only when the nearest free space is ambiguous, arrowhead only when the target is one point among similar points, never crossing data. Rejected: always connect (chartjunk), and never connect (forces dropping legitimate annotations).
- **Verification.** Rendering and inspecting the exported image is mandatory in the skill, not delegated to whichever skill is driving. Placement is the one thing that cannot be checked from code.

### Generalisation choices

The weather material is domain-specific and had to be lifted without dragging rainfall with it:

- "If most rainfall came from one burst, do not call the window wet" became the **concentration check**: before annotating any aggregate, test whether a small subset explains most of it. Given a rough threshold (<20% of observations carrying >50% of the effect) so it is actionable rather than a vibe.
- "Record clusters beat temperature departures beat rain bursts" became a five-rung **significance ladder** in domain-neutral terms, explicitly marked as a default that can be overridden with a stated reason.
- The six weather headline templates collapsed into **four label shapes** covering event+consequence, run+gap, sustained extreme, and aggregate+subset.
- The banned-word list kept its structure (dramatic register, bureaucratic register) but the examples were generalised past rainfall.

### Wiring

`dataviz-orchestrator` now lists `chart-annotations` as a companion skill and calls it at step 7, between choosing the visual and running the critique pass. Both the Codex and Claude variants were patched.

### Testing the skill on real charts

> "can you do that yourself? pick a few charts, run this and evaluate, and rewrite teh skill accordingly."

Three charts were built from real data in `data_work`, chosen to attack different weak points. Every revision below traces to a defect in a rendered image, not to a principle.

**Chart A - All-India annual rainfall, 1871-2011.** Chosen because the series has no trend at all: `lm` slope -0.07 mm/yr at p = 0.74, decade means bouncing in a 1031-1146 band. The skill had a candidate inventory full of knee-bends and extrema and no way to say "nothing here qualifies". Following it literally pushed toward marking the wettest year (1917) or the longest above-mean run (1942-49), both of which are noise. The first fix drew a +/- 1 SD band with decade averages over it and annotated the absence: "Every decade average falls inside the band". Karthik overruled this - "if there is no story there should be no annotation" - and he is right: that callout is the title said twice, spending chart space to restate what the band already shows. Re-rendered with no annotation at all and it reads better. The rule is now: no story, no annotation; the absence goes in the title; the band and decade line stay as **context layers**, which encode data or a stated baseline rather than pointing at a feature, and so sit outside the annotation cap. Added the "When nothing clears the bar" section and the would-this-survive-a-different-sample test.

The context-layer/annotation distinction was the real yield here. It was implicit and doing no work until the absence case forced it out.

**Chart B - Bangalore mean maximum temperature, 1901-2000.** Flat overall (-0.015C/decade) but V-shaped: a breakpoint scan put the knee at 1956, with -0.18C/decade before and +0.22C/decade after. The rendered chart was clean and the annotations were correctly capped, but two things were wrong in substance. The knee came from taking the minimum SSE over a scan of 61 candidate years, with no test that it was real, and it got a bare "1956" label implying single-year precision. And the two-segment fit was drawn in accent red over faint grey observations, so the loudest thing on the chart was a model rather than data. Added the observed/derived split to the candidate inventory and the "Annotating derived features" section.

**Chart C - state liquor revenue per capita, 2025-26 vs 2026-27.** The existing chart in `data_work` labels six of ten states; the skill's cap says one primary plus two supporting. The capped version was better, but produced two genuine defects. First, the annotation coordinates were hand-typed as `y = 8.6` and `y = 1.55`, and both landed on the wrong rows - "+Rs 147" appeared between Andhra Pradesh and Karnataka, and "+Rs 7" sat above Rajasthan rather than on Tamil Nadu. Rebuilding with an annotation frame filtered from the plotting data, positioned as `x = pc_2026 + 40` against `y = state_f`, fixed both. This is the single highest-value rule found by testing: a mislabelled row looks completely correct and states something false. Second, the first title read "Haryana drives almost all of the per-capita increase" - but Haryana is 418 of a 1,071 total, or 39%. The concentration check would have caught it, except the skill only applied it to annotations. Corrected to a rank claim, and the check now gates the title too.

Also found in both A and C: annotation text clipped at the right edge because scale limits were set for the data, not for the data plus its labels. And in C the period labels collided with the primary annotation, which raised the question of whether orienting labels count against the cap - they do not, but they must be collision-checked.

### Revisions made

- Derive annotation coordinates from the data, never hand-type them; worked R example included.
- New "When nothing clears the bar" section: absence as a legitimate annotation, with the band-and-inside device.
- New "Annotating derived features" section: validate before marking, word to the method's real precision, never let the fit outshout the data.
- Concentration check now gates the title as well as the annotation, with the rank-claim vs share-claim distinction spelled out.
- Orienting labels named as a class outside the cap, but still collision-checked.
- Reserve axis headroom for label text before rendering.
- Six new rows in the common-mistakes table, each from an observed defect.

Skill grew from 164 to 225 lines. Test charts were scratch work and are not committed.

### Second test round: three fresh charts

> "ok now test on 3 new charts before pushing"

New shapes, chosen to avoid repeating the first round: a scatter with a cluster rather than single-point outliers, a long time series with a takeoff, and a small state-level scatter with a metric that means two opposite things.

**Chart D - 495 Indian cities over 100,000 people, overall literacy against the male-minus-female literacy gap.** Two failures, both instructive. The label read "Rajasthan: 13 of the 20 widest gaps"; the number is 12. It was typed rather than computed, and the previous round's derive-from-the-data rule covered position only - it said the label text should be computed too, but as an aside inside the placement section, and that was not enough to stop it. Promoted to a hard rule of its own. Second, the label was anchored at the median of the Rajasthan points, which is the centroid of the cluster, which is the densest and least readable place on the chart. Deriving the coordinate was right; resting the text there was wrong. The rule is now anchor on the group, then offset to the outside edge of the cloud.

The deeper problem with D was that the title claimed one thing ("cities with low literacy are also the least equal", a statement about the whole cloud at r = -0.56) and the annotation marked another (a subgroup holding the tail). Both true, and the chart still failed - the reader is handed two findings and told which matters by neither. The "one dominant frame" filter only governed competing annotations, not title-annotation coherence. Rebuilt around the Rajasthan claim alone and it works.

**Chart E - share of women among IAS officers by allotment year, 13,571 rows.** The annotation read "share triples after 2005, flat for the 45 years before". The second half is false: the pre-2005 period runs from 5.7% in the 1960s to 13.9% in the early 2000s, a slope of 1.5 points per decade at p = 0.0002. The chart was inventing a plateau. This is a distinct failure from a wrong number, because no number appears in the phrase - "flat" is a quantitative claim in plain clothes, and so are unchanged, steady, doubled, tripled, halved. Added them by name to the wording constraints. The honest framing turned out to be better anyway: an acceleration from 1.5 to 12.1 points per decade beats a fabricated flat-then-takeoff.

E also exposed a hole in the derived-features rule. That rule was written for a breakpoint found by scanning. Here 2005 was picked by eye, which felt like observation and is actually worse - a split chosen after seeing the outcome, with no scan to point at. Extended the rule to cover analyst-chosen splits explicitly.

**Chart F - median age at marriage by state, women's age against the men-minus-women gap.** Built to test whether the skill stops a metric whose low values have two opposite meanings: Rajasthan has one of the narrowest gaps in India at 3.0 years, and also the earliest marriage for women at 18.6, so "narrowest gap" reads as equality and means the opposite. The skill did not prevent it - what prevented it was writing the title as the negative claim and marking both ends. That produced a new finding: the two labels are halves of one claim, and tiering them into primary and supporting would say one end matters more when the comparison is the whole point. Contrast pairs now count as one annotation and share weight.

F also clipped its Rajasthan label off the left edge, while the previous round's headroom rule only mentioned right-hand labels. Generalised to every edge the text can reach.

Skill now 252 lines. Verified the fixes by rebuilding chart D against the revised rules: single claim, all three numbers computed, label offset to clean whitespace, no clipping.

## 2026-07-19 - Slide-style fixes from the Zerodha workshop deck

Building a workshop deck surfaced repeated misses that fed back into `karthik-powerpoint-style` and `karthik-writing-style`:

- Kept producing clever aphoristic slide titles ("Analysis is never a straight line", "The machine does the work. You make the calls.") and "X, not Y" reveals. Karthik's real decks use plain labels and questions ("Normalisation", "What is average?", "Compared to what?"). The skill's old "make the title an analytical claim, not a topic label" line was actively pushing the wrong way; softened it and added explicit Slide-title do/don't guidance.
- Paraphrased Karthik's own "Smelling Bullshit" slides into fresh prose instead of lifting them verbatim. Added a "reuse own material verbatim" principle to both skills.
- Flattened real deck images into text stand-ins. Added guidance to pull real images from `.pptx` `ppt/media/`.
- Wrote out full instructions on hands-on slides that never get projected. Added the facilitator cue-card pattern.

`karthik-writing-style` lives only as installed Claude/Codex copies, not in this repo, so those were edited in place.

## 2026-06-19 - Dataviz selector skill session

### User prompts

> "i already have one data visualisatiohn skill. now i want to build one more to pick the right kind of visualisation for a given data set / problem statementt."

> "check out my old blog visualisations.substack.com where i've commented on various visualisations. both good and bad."

> "also mine my Mint articles (Mint folder here) to get more insgihts from there. also powerpoints in this folder with datavizs."

> "ok now put all this together to make a skill."

> "ok now put this skill as well into this git https://github.com/skthewimp/karthik-data-visualization-skill"

### Work done

- Built a new public `dataviz-selector` skill to choose chart forms from a dataset plus question/hypothesis/story.
- Calibrated the skill from Karthik's Mint articles, local PowerPoints, Substack visualisation critiques, and one-at-a-time user feedback on chart-choice scenarios.
- Added hard guardrails against pie, donut, 3D, animated, interactive-first, gauge, radar/spider, and decorative infographic recommendations.
- Red-teamed the selector with out-of-sample prompts and rendered local examples from fuel-price, small-airport, and management PBT-miss data.
- Added the skill to this public repo, updated `sync-skills.py` to build/install multiple skills, generated Codex and Claude distributions, and pushed commit `df5c507`.
- Added repo documentation, skill docs, this devlog, and a short blog-style writeup about the process.

## 2026-06-19 - Navigation docs preference

- Repo should be easy for a new person to navigate from GitHub alone.
- Keep README files in every public folder, including skill folders and `codex/` / `claude/` subfolders.
- Do not expose private `references/` or `scripts/`; those stay local-only and ignored.

## 2026-06-24 - PowerPoint style skill

- Added `karthik-powerpoint-style` as a third public skill, with both `codex/SKILL.md` and `claude/SKILL.md` to match the repository's per-skill surface layout.
- The skill captures reusable instructions for making analytical PowerPoint-style slides in Karthik's style: claim-first titles, sparse layouts, direct labels, chart-first evidence, minimal decoration, source notes, and management-ready slide patterns.
- Added folder-level READMEs for the new skill and a human guide at `docs/skills/karthik-powerpoint-style.md` so a new GitHub reader can navigate the skill without prior context.
- Updated the root README and docs index to describe how the PowerPoint skill relates to `dataviz-selector` and `karthik-data-visualization`.

## 2026-06-25 - Dataviz critique skill and documentation

### User prompts

> "Now I want to build a new skill on how to critique a visualization..."

> "Can it come up with two or three different new alternatives for visualization?"

> "you need to put a changelog /devlog / ... right now the documentation isveryvery weak"

### Work done

- Added `dataviz-critique` as a public Codex/Claude skill for reviewing existing charts, dashboards, slide visuals, and AI-generated plots.
- Based the critique workflow on Kaiser Fung's Question–Data–Visual trifecta and Karthik's clarity-first, intentional-design visualization philosophy.
- Extended the skill from critique-only to critique-plus-redesign: it now proposes minimal repair, better analytical redesign, and different story-lens alternatives where useful.
- Expanded `docs/skills/dataviz-critique.md` into a full human-facing guide with fit, inputs, output contract, redesign patterns, and example skeleton.
- Added `CHANGELOG.md` so public repository changes are easier to scan separately from session notes.



## 2026-06-30 - Analysis planner skill

### User prompts

> "Build the next unchecked skill from the TODO list as a Codex skill... let's start with analysis planner... go through a sample of [~/Documents/work]... pay special attention to ~/Documents/work/Mint..."

> "all skills that we're building in this session need to be built for both Claude and Codex and pushed to my data visualisation skills repo. see the format of that repo and build accordingly"

### Work done

- Added `karthik-analysis-planner` to the public data visualization skills repo with both `codex/SKILL.md` and `claude/SKILL.md`.
- Based the skill on Karthik's recurring notebook pattern: question, pulse check, row grain, denominator, comparison, sanity checks, falsifier, caveat, then prose.
- Included the Bangalore 4pm rain question as the mini-example and updated README/docs/changelog navigation.

## 2026-07-03 - Dataset question generator skill

### User prompts

> "do we already have a skill that, just given a raw dataset, figures out what questions to generate?"

> "ok do that. use all the analysis in my computer. including outside this folder. to get training data for htis."

> "ok and now produce both codex and claude versions of it, push it to karthik-data-visualisaiotn repo in the right format, etc. also update your memory..."

### Work done

- Added `dataset-question-generator` as a public skill with both Codex and Claude versions.
- Based the skill on Karthik's local analysis patterns: Bangalore weather normals, wind/rain mechanism questions, payments volume/value/ticket-size splits, election swings and corners, operations bottlenecks, survey subgroup comparisons, and urban morphology questions.
- Made the skill explicitly reject stale prompts and generic "trend of X" questions unless there is a clear comparison, denominator, or visual signal.
- Updated README, docs index, skill docs, changelog, and local memory workflow.

## 2026-07-03 - Contextual data cleaning skill and repo alignment

### User prompts

> "should we update teh orchestrator skill now that we have a contextual data cleaning skill as well?"

> "actually look through the repo and see what else needs updating based on everythign else that's there now"

### Work done

- Added `karthik-data-cleaning` to the public skill set and wired it into the rest of the repo navigation.
- Updated `dataviz-orchestrator` so the workflow is no longer “profile then analyse” in the abstract; it now explicitly includes contextual inspection, cleaning, reshaping, joins, and validation before charting.
- Updated `dataset-question-generator` and `karthik-analysis-planner` so messy data gets cleaned only when that is needed to make signals or metrics legible.
- Filled in missing README files for newer Codex/Claude skill subfolders and brought the docs indexes/changelog up to date.

<!-- codex-session:019f26a5-c9d8-7292-8734-869cb2992a60:start -->
## 2026-07-03 11:53 IST | Codex session `019f26a5-c9d`

### User prompts
> should we update teh orchestrator skill now that we have a contextual data cleaning skill as well?
> actually look through the repo and see what else needs updating based on everythign else that's there now
> is the repo clean now?

### Work done
- Need changelog mention README pass.
- Done. - Proper READMEs added/expanded across public skill folders, Codex/Claude folders, docs folders. - Kept private reference/script contents ignored, but allowed their README files. - Data-cleaning is public again,...
- Touched files: `.gitignore`, `CHANGELOG.md`, `README.md`, `dataset-question-generator/README.md`, `dataset-question-generator/claude/README.md`, `dataset-question-generator/claude/SKILL.md`, `dataset-question-generator/codex/README.md`, `dataset-question-generator/codex/SKILL.md`
- .gitignore | 8 +++-

<!-- codex-session:019f26a5-c9d8-7292-8734-869cb2992a60:end -->

<!-- codex-session:019ff565-7102-71d1-b38d-b03059979603:start -->
## 2026-08-12 15:24 IST | Codex session `019ff565-710`

### User prompts
> ok we need to audit all the skills again. using hte local zerodha images for testing. now in the last few iterations, the fixes seemm to be way too specific to the specific cases and feedback and not generic enough. s...
> ok can you clean up the stuff, putting things in the most important skill? so there is no overlap or contraciction?
> yeah just push, commit, and deploy to the client runtime

### Work done
- Review `git diff --stat`; the ownership cleanup is complete. Step 4/4 done: 1. Consolidated responsibilities across all 13 skills. - `dataviz-selector`: form and encoding choice. - `karthik-data-visualization`: visual...
- Start a new client session to load the updated skill text. Step 3/3 done: 1. Committed `b83b929 refactor(skills): clarify ownership boundaries` 2. Pushed `main` to GitHub. 3. Deployed and verified all 13 skills...

<!-- codex-session:019ff565-7102-71d1-b38d-b03059979603:end -->

<!-- codex-session:01a004f8-6490-7812-9a21-1e1cb2166794:start -->
## 2026-08-15 15:59 IST | Codex session `01a004f8-649`

### User prompts
> You are working in my repo: https://github.com/skthewimp/karthik-data-visualization-skill I want you to take over implementation work from here. What I am trying to achieve The repo already has a fairly elaborate skil...
> i'm using one venv on this c omputer. use that.
> ok what command do i need to run and how does it work?

### Work done
- `codex mcp add karthik-dataviz -- /Users/Karthik/envs/datascience/.venv/bin/python -m dataviz_mcp` **Step 7/7 done: MCP MVP and exact-artifact repair loop implemented.** 1. **MCP tools** - `render_chart`: emits PNG, s...
- ```bash codex mcp add karthik-dataviz -- /Users/Karthik/envs/datascience/.venv/bin/python -m dataviz_mcp ``` Run this once in Terminal, from any directory. 1. **Register the server** The command tells Codex: - server...
- Touched files: `.gitignore`, `CHANGELOG.md`, `README.md`, `dataviz-eval/claude/SKILL.md`, `dataviz-eval/codex/SKILL.md`, `dataviz-fix/claude/SKILL.md`, `dataviz-fix/claude/scripts/README.md`, `dataviz-fix/claude/scripts/case_manager.py`
- .gitignore | 1 +

<!-- codex-session:01a004f8-6490-7812-9a21-1e1cb2166794:end -->

<!-- codex-session:01a005d3-ca03-7a21-930e-1d5d62205760:start -->
## 2026-08-15 19:59 IST | Codex session `01a005d3-ca0`

### User prompts
> check the latest dataviz-fix in the client runtime. i'm not happy with this at all. seems like it has done nothing. the person who had sent me the chart had sent me this feedback about the original chart. Issues with the top chart...
> so oinly the skills got changed? how do we make sure this doesn't happen? so many times i've got this "agent ignored existing rules". look into history you can see
> how do i trust you this time, when you've told me several times b efore that you've fixed it? like even the previous iteration didnt work. exact same (poor) result happened.

### Work done
- Step 2/4 done: 53 workflow tests pass, including hard failure when the writing skill is missing and rejection when either presentation gate is absent or non-pass. Next: run the full repository validation.
- Step 3/4 done: all 80 tests pass; skill-bundle validation and `git diff --check` pass. Next: publish this generic workflow fix and deploy the exact commit to the client runtime.

<!-- codex-session:01a005d3-ca03-7a21-930e-1d5d62205760:end -->

<!-- codex-session:01a019ea-68e4-7180-849a-ffb68e689458:start -->
## 2026-08-19 17:36 IST | Codex session `01a019ea-68e`

### User prompts
> ok now it produces an output quickly, but turns out it's not precise enough. like look at this output chart. font on axis labels is way too big. i don't knwo if we need "years" there> we have direct labels and still a...
> wait - did you hardcode this "years" thing? if so, remove. this is th reason why we got such a complicated skill today.
> simiarly look for other hardcoded examples and overfitting in the skill and mcp

### Work done
- Rerun the same chart; the repair stack no longer carries case-specific design defaults. Step 4/4 done: - Removed fixed issue and redesign-option counts. - Removed forced structural redesigns. - Removed Matplotlib-only...
- Rerun the other conversation; neither requirement remains. Step 3/3 done: - Dimensions are optional; profile defaults work. - No mandatory “exact, approximate, or mixed” statement. - Internal safeguards still prevent...

<!-- codex-session:01a019ea-68e4-7180-849a-ffb68e689458:end -->

<!-- claude-session:f7d7de41-ee72-45fb-aa79-99daa5f3782d:start -->
## 2026-08-21 09:41 IST | Claude session `f7d7de41-ee7`

### User prompts
> made a bunch of recent changes to this set of skills. basically it had become too slow and so we did away wiht the loop involving the dataviz-eval skill. now it seems to have regressed in ome cases. can you see if the...
> actually wait. before this, can we summarise what the critique skill says, and if it has changed materially in the recent times? (look at old gits etc)
> before that, can you give me a flowchart on how dataviz-fix works?

### Work done
- Yes — and I think your reordering is not just a better critique, it's the structural fix we've been circling. Let me think it through. ## What's actually wrong with the current order Critique is doing three jobs at on...
- Reran and no fix — agreed, prose guardrails have hit their ceiling. Here's a self-contained handoff prompt for a fresh session. On MCPs: **no new MCP needed.** The reorder is pure skill-flow logic. Rendering/inspectio...

<!-- claude-session:f7d7de41-ee72-45fb-aa79-99daa5f3782d:end -->

<!-- claude-session:2660d710-f0c6-4bac-b8a3-f1a28c1b8712:start -->
## 2026-08-21 16:36 IST | Claude session `2660d710-f0c`

### User prompts
> Repo: /Users/Karthik/Documents/work/karthik-data-visualization-skill # Task: restructure the dataviz repair flow so it stops re-rendering the source chart ## Background (why we're doing this) The repair flow (dataviz-...
> are we overfitting to this one case? i had a hard time undoing such s tuff in the past
> yes do that now

### Work done
- Honest state: the selector already carries most of Tufte's *selection*-level principles — comparison-first (step 2 = "compared to what?", the core Tufte question), simplest form (step 5 = smallest effective difference...
- Pushed `bd0be77`. Tree clean, in sync. **Direct answer:** most of Tufte was *already* in the selector — it just wasn't labelled as such: | Tufte selection principle | Was it there? | |---|---| | "Compared to what?" (c...

<!-- claude-session:2660d710-f0c6-4bac-b8a3-f1a28c1b8712:end -->

<!-- claude-session:863824a3-d75b-406c-be51-f49a9cc4a003:start -->
## 2026-08-21 21:01 IST | Claude session `863824a3-d75`

### User prompts
> one thing we've missed out in this suite of skills - a well formatted table can also be a good visualisation. rihgt now this doesn't do tables. if given a badly formatted table, we get a visualisation. some grpahs tha...
> commit and push. and go on with phase 2.
> the tablegrob thing is a problem. need the table to be of hte appropriate size in teh canvas

### Work done
- Mirroring, noting in CHANGELOG, validating, syncing, committing.
- Done, pushed (`a6373d6`). Precision principle is now **bidirectional**: it's significant digits, not decimal places. It rounds to the left of the decimal - ending large numbers in zeros (tens/hundreds/thousands) when...
- Touched files: `Rplots.pdf`

<!-- claude-session:863824a3-d75b-406c-be51-f49a9cc4a003:end -->

<!-- claude-session:573fb7bb-aec9-47e8-ae40-8d76697ca8b4:start -->
## 2026-08-21 21:41 IST | Claude session `573fb7bb-aec`

### User prompts
> recent changes in some of teh skills have made the dataviz-fix WORSE. [Image #4] from the logs: }, "request": { "mode": "automatic_critique", "repair_brief": "No user-specific change was supplied. Run a complete exper...

### Work done
- `Rplots.pdf` is a stray R artifact, not mine — unstaging it.
- Done. Pushed `a1441d2`. ## What was wrong Not a weakened guardrail. The de-overfit commit kept every rule. The chart collapsed through the one door nobody had sealed: the guardrails all block **value/precision** excus...
- Touched files: `Rplots.pdf`

<!-- claude-session:573fb7bb-aec9-47e8-ae40-8d76697ca8b4:end -->

<!-- claude-session:32df88b3-3350-4321-9be8-2f72668c7a50:start -->
## 2026-08-22 09:53 IST | Claude session `32df88b3-335`

### User prompts
> can you test the dataviz-fix skill on @~/Downloads/openrouter.png ?
> where is it stored?
> yeah downloads

### Work done
- It's my commit — the 3-rule change you were unhappy with, still sitting on `origin/main` (not in your local anymore after the reset). Here's exactly what it added: **`karthik-data-visualization`** (2 lines): 1. *"A sh...
- Local now at `0079ed0`, in sync with `origin/main` (no ahead/behind). Skills reinstalled to both surfaces. State: the 3 skill rules are committed, pushed, and installed. The global CLAUDE.md and the significant-figure...
- Touched files: `Rplots.pdf`

<!-- claude-session:32df88b3-3350-4321-9be8-2f72668c7a50:end -->

<!-- claude-session:d6f10a8c-6b4a-438f-865e-969e68e74534:start -->
## 2026-08-22 10:30 IST | Claude session `d6f10a8c-6b4`

### User prompts
> the problem with the current structure of teh skills, especially when implemented through a web app, is that it sends all the skills as part of one mega prompt and there is context rot. what we need is something like...
> [Request interrupted by user]
> don't rename it. repurpose it

### Work done
- Yes — all committed and pushed. `git log origin/main..HEAD` is empty, so nothing is unpushed. The three commits from this work are all on `origin/main`: - `0ef589e` — staged pipelines, killed the mega-prompt (contract...
- Removed. Working tree is now clean and everything's pushed.

<!-- claude-session:d6f10a8c-6b4a-438f-865e-969e68e74534:end -->

<!-- claude-session:5a415341-5371-494f-8450-312eb561684e:start -->
## 2026-08-24 08:48 IST | Claude session `5a415341-537`

### User prompts
> as part of this suite of data visualisation skills and MCPs, i want to add two other capabilitlies. one is to choose colours for a graph and the ohter is to figure out the appropriate number of significant digits to d...
> <task-notification> <task-id>af5678bd45af1fd8d</task-id> <tool-use-id>toolu_01XoG5mrVsvcK28tPkDgeSk2</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/5a...
> <task-notification> <task-id>a2b95c3ddf1064449</task-id> <tool-use-id>toolu_01KDuJT8NanQsCmA1eXQykRK</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/5a...

### Work done
- Adding a regression test for the ordering guarantee, then shipping.
- Both refinements shipped and pushed. **1. `colour_groups` = max series per panel.** No longer "colours the encoding needs" — now the **maximum number of series sharing a single panel**. So small multiples with 3 lines...

<!-- claude-session:5a415341-5371-494f-8450-312eb561684e:end -->

<!-- claude-session:fce8f599-2913-48f4-a0bf-32666203e1ab:start -->
## 2026-08-24 10:10 IST | Claude session `fce8f599-291`

### User prompts
> a few changes needed in my r-exploration-style - 1. don't write SQL. use dbplyr / duckplyr / arrow / ... when accessing database stuff; 2. i always prefer right assignmetns (-> ) in long chains, so i can easily run st...

### Work done
- Check DEVLOG, then run sync.
- Done. 3 rules added to `karthik-r-analysis-style`, all copies synced, committed + pushed. **Changes:** 1. **No raw SQL** - data access via `dbplyr`/`duckplyr`/`arrow`; SQL strings only for unavoidable one-off DDL/conf...

<!-- claude-session:fce8f599-2913-48f4-a0bf-32666203e1ab:end -->

<!-- claude-session:110c274e-a7c9-4fef-b448-1daf40432fd4:start -->
## 2026-08-24 10:19 IST | Claude session `110c274e-a7c`

### Work done
- Session captured, but there was not enough structured activity to summarize.

<!-- claude-session:110c274e-a7c9-4fef-b448-1daf40432fd4:end -->

<!-- claude-session:025c440f-6057-44ae-b311-e23c172d8190:start -->
## 2026-08-24 10:51 IST | Claude session `025c440f-605`

### User prompts
> we have some issues with the dataviz selector. check out these two outputs from the current pipeline. the first one is oriented the wrong way. it should just be a set of simple slope graphs, but put in a way that it i...
> ok now look at these two examples. for whatever reason, we have two separate graphs. a stacked bar and small multiples. i don't know if we need both! this actually confuses, if you think of it. [Image #3] [Image #4] ....
> a related thing - even when the total changes over time, just showing that is good, we don't need a stacked bar there. (again i'm giving just one example. don't hard code anything)

### Work done
- Right — the totals view should be a **plain total line**, not a stacked bar. A stacked bar tries to do both jobs (total = full height, parts = segments) and does neither well: internal segments float so parts are hard...
- Pushed. Rule now: when total genuinely varies and you need both total + mix → **total line + breakdown**, never a stacked bar/area. The stack does both jobs badly (floating segments hide the parts, moving height hides...

<!-- claude-session:025c440f-6057-44ae-b311-e23c172d8190:end -->

<!-- claude-session:10270db0-824f-471a-ae30-a8179b3b7400:start -->
## 2026-08-24 11:24 IST | Claude session `10270db0-824`

### User prompts
> recommendation from an LLM which is deploying this set of skills on a website: ## 1. Fix upstream first The colour-count semantics are already fixed in the latest upstream code: colour_groups now means the maximum num...
> - Upstream’s 74 tests pass, but sync.sh --no-pull --validate-only fails because the YAML description in /home/karthik/apps/karthik-data- visualization-skill/dataviz-precision/codex/SKILL.md:3 contains an unquoted colo...

### Work done
- Strict-YAML clean across all skills. Cleaning up the temp pyyaml install (wasn't a project dep):
- Fixed and pushed. Local matches `origin/main`. **Fix:** quoted the codex `dataviz-precision` description - it had `choose precision: how many` (colon-space) as a plain YAML scalar, which strict parsers reject. My `syn...

<!-- claude-session:10270db0-824f-471a-ae30-a8179b3b7400:end -->

<!-- claude-session:32b31352-6112-4229-920d-3a2fcf857353:start -->
## 2026-08-24 12:54 IST | Claude session `32b31352-611`

### User prompts
> more issues in the skill set. again i dont konw where to fix this. check out this chart. Y axes are too dense. and given the direct labelling, ew don't need the axes at all. and why do we have small multiples here rat...
> <task-notification> <task-id>a3cf0386b2971dd28</task-id> <tool-use-id>toolu_019ZjLeLZBiG2qeeun7aTNGT</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/02...
> ok let's figuer out where to fix this. thing is - i don't know why the "don't repeat axes" things was never implemented for quantitative axes. tit was always intended to

### Work done
- Installed to `~/.codex` + `~/.claude`, diff-check clean, only the 6 intended files changed. Fetching, committing, pushing.
- Shipped. `863be42..3951d4e` pushed to `origin/main`, local matches upstream. **Done this session:** - **Skill fix 1** - quantitative axes/gridlines now drop-unless when direct labels carry the values (was keep-unless,...

<!-- claude-session:32b31352-6112-4229-920d-3a2fcf857353:end -->

<!-- claude-session:d69d5a99-7e52-4439-ba28-929ee7e6fcdf:start -->
## 2026-08-25 17:44 IST | Claude session `d69d5a99-7e5`

### User prompts
> we are having some deployment issues, especilly with weaker models. downstream LLM recommends: 1. Upstream skill/stage contract: - Add a structured distinction between source_fidelity and external_validation. - When e...

### Work done
- DEVLOG is auto-generated per session (separate commit). Now commit + push per maintainer default:
- Shipped. All 3 recs landed, 77 tests green, synced + pushed. **What changed:** 1. **External validation no longer blocks.** Root cause of your failure: a check demanding "exact denominator/dataset/methodology" had no...

<!-- claude-session:d69d5a99-7e52-4439-ba28-929ee7e6fcdf:end -->

<!-- claude-session:94f7df76-e044-4b03-9fc9-f1ff331a8411:start -->
## 2026-08-25 18:15 IST | Claude session `94f7df76-e04`

### User prompts
> The underlying problem is upstream: recommend_colours knows positional series indices, not semantic category identities. The contract simultaneously required its reordered palette and preservation of the old semantic...
> this is on the colour recommender. resulted in an unnecessary failure. Case 2 had four semantic colour assignments in the source: - cacheRead → light green - cacheWrite → dark green - output → amber - input → grey Ter...
> actually we don't need this last change. revert it. it's way too specific.

### Work done
- Reverting via `git revert` (no history rewrite, safe to push).
- Reverted. `fb0c898` pushed, all 7 files back to pre-change state, local matches `origin/main`. `recommend_colours` is count-only again.

<!-- claude-session:94f7df76-e044-4b03-9fc9-f1ff331a8411:end -->

<!-- claude-session:6d1d1db3-64a5-4986-bf17-ee71544982e8:start -->
## 2026-08-25 21:54 IST | Claude session `6d1d1db3-64a`

### User prompts
> i'm thinking about the colour selector - if there is a way we can also get it to choose SEMANTICALLY APPROPRIATE colours. how would we code it, if we would want to add this?
> ok soft families, judgment in the model; we should use semantic colouring whenever the LLM thinks its appropriate unless the promopt or brand style or something else has strongly recommended against it.
> [Request interrupted by user]

### Work done
- Local is one commit ahead of remote (the devlog auto-commit) and clean to fast-forward. Staging and committing:
- Pushed. Local and `origin/main` both at `a52e8f3`. Shipped: - `recommend_colours` now takes `semantic_hints` (hard pins / soft hue families + away-kit `alternates`), with the priority you set - distinctness hard, mean...

<!-- claude-session:6d1d1db3-64a5-4986-bf17-ee71544982e8:end -->

<!-- claude-session:22f8f071-11b4-4531-9d41-f338f4fd3e25:start -->
## 2026-08-26 09:44 IST | Claude session `22f8f071-11b`

### User prompts
> recently we moved the dataviz-fix and orchestrator workflows from a monolith to a series of LLM calls with only the right contexts loaded in. however the issue with this is that it now overly depends upon json output...
> one more thing - we have skilslfor codex and claude. how will other LLMs work with this? how should the harness be s tructured for that?
> [Request interrupted by user]

### Work done
- Now remove the project-local duplicate so it lives in one place:
- Done. The principle now lives globally in `~/.claude/CLAUDE.md`, under **Coding Behavior → "LLM handoffs: markdown over JSON"**, so it applies to every project: > Avoid JSON "contracts" unless absolutely necessary. An...

<!-- claude-session:22f8f071-11b4-4531-9d41-f338f4fd3e25:end -->

<!-- claude-session:9b830eee-8084-42e7-ab5f-38f7284325c1:start -->
## 2026-08-26 15:44 IST | Claude session `9b830eee-808`

### User prompts
> forget the downstream harness that i'm building. how does this repo currently stand as a set of standalone skills and MCPs for building and repairing dataviz, and analysing data? anything is off or overfit or hardcoded?
> ok first undo the machine-specific overfit. don't push yet.
> ok now for hte other issues. how do we deal wtih it? "demote" doesn't sound good.

### Work done
- Pushed. `main` up to date with `origin/main`, clean. **Committed `f550edf`** (+ the prior devlog commit `b5186cc` that was already ahead) → pushed `cc05cf2..f550edf`. - 16 skill files reframed/cleaned + CHANGELOG + DE...
- Synced. All 18 skills installed to both `~/.claude` and `~/.codex`. Everything's committed, pushed, and the local installs now match.

<!-- claude-session:9b830eee-8084-42e7-ab5f-38f7284325c1:end -->

<!-- claude-session:8425f19b-86ce-401d-9590-5d2ad3b66afc:start -->
## 2026-08-26 21:50 IST | Claude session `8425f19b-86c`

### User prompts
> changing from strict json to markdown has made the process much much slower. is this expected?
> is it possible for you to run samples using both the latest code and the old JSON code, on a local file here, to see if there is a material difference? maybe use ~/Downloads/openrouter.png
> this is enough. undoing the conditinoals change now

### Work done
- Functionally: **all downstream.** The resolvers (`palette.py`, `precision.py`) are complete and already in this repo - your driver just imports and calls them. Nothing here needs to change for Option A to work. The on...
- Deliverable written straight (caveman is chat-only). Copy-paste this to your downstream agent: --- **Task: resolve chart colour & precision as data before the build stage, instead of loading the colour/precision skill...

<!-- claude-session:8425f19b-86ce-401d-9590-5d2ad3b66afc:end -->

<!-- claude-session:8790f9f9-4747-4cdd-b51d-2ba641f40999:start -->
## 2026-08-27 13:15 IST | Claude session `8790f9f9-474`

### User prompts
> check out @sol
> check out @sol-terra-luna-canonical-comparison.pdf . this is for one harness that i'm running on one website, but shows how diferent openai models are changing a b unch of input graphs. right now i'm not happy with aa...
> case 1: 1. dark mode is a problem. highly unreadable. unless specifically requested in the prompt, this shouldn't be getting selected at all 2. very weird font 3. i always prefer direct labels (you see sol and terra h...

### Work done
- Short answer: yes, lean harder on MCPs and the harness - but "MCP vs text skill" is the wrong axis to cut on. The useful split is three-way, and the Luna failures tell you exactly which pieces are in the wrong place....
- Written and pushed (`0cbe24b`): [`docs/plans/weak-model-repair-hardening.md`](docs/plans/weak-model-repair-hardening.md), indexed in the plans README. It's codename-free so it sits fine in the public repo. The shape:...

<!-- claude-session:8790f9f9-4747-4cdd-b51d-2ba641f40999:end -->

<!-- claude-session:aac159d2-3b6b-4db4-b518-c8e3b1a866e9:start -->
## 2026-08-27 17:39 IST | Claude session `aac159d2-3b6`

### User prompts
> right now, in the diagnose part of the dataviz-fix, we do several things - get the raw data, figure chart message, figure out what is wrong with the given chart. should we be separating these out?
> i gave a github heatmap and asked to "fix" expecting a line graph but got the same thing out instead. the logs say this: "request": { "mode": "prompted_repair", "repair_brief": "User repair request: this chart is hard...
> actually critique had b een removed (by jmisttke) from stage 1.

### Work done
- Got it - removed *by mistake*, not a person. Noted. Doesn't change the diagnosis: that removal is in the repo's stage 1, and Luna never ran the repo's stage 1 - it ran the hosted app's critique-first orchestrator. So...
- Fair - let me separate what I actually verified from what I inferred. **Evidence (verified this session):** - Your log fields are `mode: prompted_repair`, `source_assessment`, `recommendation`, `build_decisions`, `pre...

<!-- claude-session:aac159d2-3b6b-4db4-b518-c8e3b1a866e9:end -->

<!-- claude-session:ee9a9607-2333-4906-8527-1fd1e283204e:start -->
## 2026-08-27 19:36 IST | Claude session `ee9a9607-233`

### User prompts
> one more failure. here are the logs that have been captured in the website flow. and i'm pasting the input and output after this. why did this 1. pick small multiples b y day of week? i expected one single line; 2. no...
> i'm wondering if this is a good time to bring back the evals layer and the loop. maybe we should use all the examples so far (and maybe construct a few more) to look at failure poihnts and thne do the evals. or should...
> remember i wanted to redo the dataviz eval - since it was looking at the wrong things.

### Work done
- Seed found: `../luna-eval-private/dataviz-eval-first-principles.md`. Reading it so the redo builds on it, not around it.
- Read the seed (`dataviz-eval-first-principles.md`). It already scopes your redo — and it changes the answer to your last question. Key tension to surface: ## The seed says eval is the *wrong layer* for these failures...

<!-- claude-session:ee9a9607-2333-4906-8527-1fd1e283204e:end -->

<!-- claude-session:fb930fbc-7913-4e91-8ec2-90fd8d74c823:start -->
## 2026-08-28 09:52 IST | Claude session `fb930fbc-791`

### User prompts
> i'm thinking of a change in teh dataviz-fix (and even create) workflow - rather. both need to coalesce into one workrflow after having figured out what to do / change. bsaically the graph creation part can be integrat...
> <task-notification> <task-id>ab5ddc860fb320762</task-id> <tool-use-id>toolu_01NGKsm5SL56AorYbSLfF3No</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/87...
> <task-notification> <task-id>aceebfcf5b4094bf4</task-id> <tool-use-id>toolu_011PZwJmEqWnRd7zWjx5XLW5</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/87...

### Work done
- 114 passed (+3), validation clean. Install + commit + push:
- Pushed (`e6b2781..315d415`). You were right - the note states the finding, not the pixels. It's now its own `explain` stage that reads the insight artifact + plan, **never the render**, and runs in parallel with build...

<!-- claude-session:fb930fbc-7913-4e91-8ec2-90fd8d74c823:end -->

<!-- claude-session:3c738231-b329-41e1-baf7-a8187bd65160:start -->
## 2026-08-28 14:19 IST | Claude session `3c738231-b32`

### User prompts
> this is a live example fromyseterdya. on the hcart fixing stage - which we added in today - this is a good example of what to catch. is it wired proerly to catch something like this? [Image #4]

### Work done
- Real deterministic collision detection exists (inspection.py: `text_text_collisions`, `text_mark_collisions`). But it needs per-element bbox metadata. Checking whether the renderer actually emits that — else it silent...
- ## Verdict: half-wired. The rule catches it; the deterministic net doesn't cover this render type. **What IS wired (good):** 1. Execution gate skill explicitly lists this defect — `dataviz-execution` Geometry check: *...

<!-- claude-session:3c738231-b329-41e1-baf7-a8187bd65160:end -->

<!-- claude-session:6762c11a-a5f9-4732-91a7-a061738a785d:start -->
## 2026-08-28 14:22 IST | Claude session `6762c11a-a5f`

### User prompts
> inspect the dataviz-fix and datviz-orchestrator skills. how are tehy doing in the balance between MCPs and skills? assuming we'll be using weak / open weight LLMs, don't want to load too much judgment into skills that...
> ok how do we patch this? if we have MCPs for rendering and inspecting charts, how do we maek sure they get used?
> this is too verbose. i don't understadn. what exactly is the problem we are fixing here?

### Work done
- Committing and pushing.
- Done. Pushed. What changed so the execution gate must use the MCP: 1. **Contract (`EXECUTION_SCHEMA`)** — new required `inspection` block: `geometry_source` + the numbers only the inspector produces (min text pt, over...

<!-- claude-session:6762c11a-a5f9-4732-91a7-a061738a785d:end -->

<!-- claude-session:e663a386-0403-48bb-80cd-33158927a15e:start -->
## 2026-08-28 14:51 IST | Claude session `e663a386-040`

### User prompts
> there aer a bunch of chaneges we've made in this repo today. give a quick summary on what has been changed and why which I can now pass on to the downstream harness so these can take effect.

### Work done
- Here's a handoff summary of today's work. All of it lands in the `dataviz-construct` unification and its follow-ups - one shared terminal pipeline with two gates, then hardening that tail so a cheaper/weaker model can...

<!-- claude-session:e663a386-0403-48bb-80cd-33158927a15e:end -->

<!-- claude-session:2512ce59-17bd-44bc-a567-1b208e4e7aaf:start -->
## 2026-08-28 14:56 IST | Claude session `2512ce59-17b`

### User prompts
> i want to understand deeply how the part where we figure out what the insight in hte data is is built.
> ok this is okay for now. question is - how good will weak models be at this in the current form?
> youve disgnosed well but the recommendstions look wesk

### Work done
- Fair. Looking it up.
- Rates found — **sol $5/$30, luna $0.20/$1.20** per 1M in/out. Sol is **25× luna on both**. Per one chart run (50k in / 12k out): | Scenario | Cost/run | vs all-luna | vs all-sol | |---|---|---|---| | 100% sol | **$0.6...

<!-- claude-session:2512ce59-17bd-44bc-a567-1b208e4e7aaf:end -->

<!-- claude-session:31c7e4d6-182c-4876-a37d-36f8a709e031:start -->
## 2026-08-29 09:23 IST | Claude session `31c7e4d6-182`

### User prompts
> i've changed the downstream harness to make plpts exclusively using ggplot2. now, weaker LLMs arent that greaet at this, so I"m wondering if I can help them wiht this. look through this computer - there is a very larg...
> forget style - that's already covered. i'm talking about implementation. and only look at 2019+ code.

### Work done
- Plan updated with the corrected, 2019+-evidence-based idiom set. The linter rules inherit from the corrected anti-idiom table ("one rule per anti-idiom above"), and the fixtures still hold. Re-exiting for approval.
- Stored. Plan sits at `~/.claude/plans/mighty-sniffing-book.md` — persists across sessions, nothing runs. Recap for when you pick it up: **skill `karthik-ggplot-style`** (2019+ implementation idioms — patchwork, `%>%`,...

<!-- claude-session:31c7e4d6-182c-4876-a37d-36f8a709e031:end -->

<!-- claude-session:e9c69206-33a2-443d-9353-6383344e176e:start -->
## 2026-08-29 15:56 IST | Claude session `e9c69206-33a`

### User prompts
> how do we decide right now in dataviz-selector whether it needs to be a table or a graph?

### Work done
- Question answer, no plan needed. Decision lives in `dataviz-selector/{claude,codex}/SKILL.md` under **## Table or chart?** (lines 31-38), plus a supporting note in `references/selection-prior.md`. **How it decides now...

<!-- claude-session:e9c69206-33a2-443d-9353-6383344e176e:end -->

<!-- claude-session:35a3234c-c0e3-438b-aaaa-33a7f0c97712:start -->
## 2026-08-31 09:29 IST | Claude session `35a3234c-c0e`

### User prompts
> We recently discussed in a in a notebook or something or another chat about how we need to come up with some an arc or GG plot guidelines to create good data visualizations based on the data visualization skills that...
> no wait. we got past some of those issues. here are the diagnoses from the latest run: | Case | Job | Pipeline result | Source-grounded review | Time | Est. token cost | Main finding | |---|---|---|---|---:|---:|---|...
> so how can we solve this at the skill / tool level? forget number of iterations / hard gates etc. that's for the harness to figure out.

### Work done
- Agreed - a `FLAT_PANELS` check or a facet-scale tool is exactly the trap again. "Facet scale wrong" isn't its own thing; it's one instance of a general question that has nothing to do with facets: **Does the chosen en...
- Checked - it's already covered, generally, and better than a facet check would be. The idea gate's **EXPRESSION** question (`dataviz-idea-critique`): > "Is the selected form the right vehicle for *this* claim, or will...

<!-- claude-session:35a3234c-c0e3-438b-aaaa-33a7f0c97712:end -->

<!-- claude-session:70c97a15-c607-4407-b97b-7ff870a3bd18:start -->
## 2026-08-31 11:50 IST | Claude session `70c97a15-c60`

### User prompts
> look at @canonical-examples.pdf . that will show you where the current harness works well or not. the text placement stuff has gone in (and yet to gbe integrated there, this is before that). what else should we change...
> we'vde moved ahead the repo since the aerlier part of this conversation, so r evise these recos based on htat
> yes all of these need fixing. figure out the most efficient way of doing this, and remember that we might use weak models, so more in tools than skill text

### Work done
- DEVLOG is hook-managed (auto-written per session block) — no manual edit. Staging only my files (leaving the pre-existing `sync-skills.py` change alone) and committing:
- Done. Committed `8ead8d9`, pushed to main. ## Shipped — 3 fixes, logic in tools | Failure (case) | Tool that now does it | Skill pointer | |---|---|---| | over-label every value → collide (04) | **new `recommend_label...

<!-- claude-session:70c97a15-c607-4407-b97b-7ff870a3bd18:end -->


<!-- claude-session:da94dd90-b18f-47b9-a821-6ea5b2f28474:start -->
## 2026-08-31 12:58 IST | Claude session `da94dd90-b18`

### User prompts
> free_y is normal ggplot terminology: facet_wrap(..., scales = "free_y") But recommend_layout accepts only: fixed free The model naturally emitted free_y. The website validator rejected the entire resolver- input objec...
> also look through @canonical-examples.pdf and see what the failuers there are . this s BEFORE we fixed the text placement etc (that run didn't run properly due to this free_y failure). figure out what we need to fxi b...

### Work done
- Let me check what these failure codes (R1, R2, D1, F2, I1, V1) mean in the eval framework:
- Read all 5 cases + failure-code defs + confirmed the two code gaps. Diagnosis: ## The through-line Cases 03/04/05 are **faceted small-multiples** — exactly where the model emits `free_y`. The fallback reverted them to...
- Touched files: `sync-skills.py`
- sync-skills.py | 8 ++++++--

<!-- claude-session:da94dd90-b18f-47b9-a821-6ea5b2f28474:end -->

<!-- claude-session:584254e6-50cf-4d88-9726-476dfced4c89:start -->
## 2026-08-31 13:36 IST | Claude session `584254e6-50c`

### User prompts
> check @canonical-examples.pdf . still a LOT of failures. why is this happening? it's actually getting worse! and the full report is here: # Latest website: five canonical examples Run date: 31 August 2026 Website revi...
> i'm very happy wtih the actual choice of graphs. it's the implementaiton
> no you don't know anything. you're giving all wrong diagnoses

### Work done
- You're right - I was theorizing off the PDF and reading code, never looked at the actual run. That's guessing, not diagnosing. Let me get real evidence instead of another theory.
- Run dir gone - can't inspect the actual traffic. So I have no ground truth, and I shouldn't keep inventing theories. Tell me what I'm getting wrong. Concretely: is the real cause something like - - pipeline isn't even...

<!-- claude-session:584254e6-50cf-4d88-9726-476dfced4c89:end -->

<!-- claude-session:6ddefe66-ce6a-4e6a-98ab-c56cb2c0aa00:start -->
## 2026-08-31 15:14 IST | Claude session `6ddefe66-ce6`

### User prompts
> look at @canonical-examples.pdf . t6oo many defects. why is each facet so small? why do facets have borders? can you tell me the actual pixellation and sizing and font size? the labels are also misplaced - seems like...
> A nad B for sure. where will you fix? let's plan first
> implement A. should be quick. don't bohter committing right now. let's make all the fixes first and then do it

### Work done
- Synced, 156/156 pass. Committing + pushing:
- Shipped. `3668ab5..3c82105` on `main`. **Both added to `recommend_text_placement` (build-phase tool):** 1. **Resize** — ladder is now move → **shrink toward 8pt floor** → tighten-wrap → hand-review. Returns `suggested...

<!-- claude-session:6ddefe66-ce6a-4e6a-98ab-c56cb2c0aa00:end -->

<!-- claude-session:52b681c8-834c-442d-997a-ae38083f52b2:start -->
## 2026-08-31 20:42 IST | Claude session `52b681c8-834`

### User prompts
> see the new @canonical-examples.pdf . here are my issues. any skills / MCPs to fix? and make your own judments. actually i'm mostly happywith this. only issues are: 1.chart 1: some data labels are not adjacent to thei...
> ok - chart 1 is MINOR. i'd just fix that in the text placement MCP, where we recommend that all labels be placed CLOSE to the points they represent, and if not, join by a thin line (like in ggrepel). second, remove do...
> [Request interrupted by user]

### Work done
- You're right — issue 2 was **Case 02** (token share vs cost share, the paired dot plots), not Case 01. And that changes the picture: the selector edits I already made **do** address it. Case 02's paired dot plots are...
- Installed all skills to local Claude + Codex copies. Done — changes committed, pushed, and live locally.

<!-- claude-session:52b681c8-834c-442d-997a-ae38083f52b2:end -->

<!-- claude-session:ceba26f0-757c-421b-bf42-0ecdd8cefe3f:start -->
## 2026-08-31 22:09 IST | Claude session `ceba26f0-757`

### User prompts
> titles are getting wrapped randomly.why is thishappening? [Image #1]
> check the text placement MCP. that should be guiding it. not deterministic wrapping. if it's fixed at 40, needs tobe undeon. is it inthis skills +MCP thing or downstream?

### Work done
- Title not random - wrap at fixed pixel width. "Bollywood's male-lead age mix shifted older" wider than wrap box → breaks after "shifted". Deterministic, keys on box width not word logic. Common causes in these rendere...
- Checked. Not the MCP. Nothing to undo there. **text_fit MCP (`recommend_text_placement`) does NOT hardcode 40.** For a fixed block (title role, `movable=False`), `text_fit.py:182`: ``` avail = width_px - 2 * margin ``...

<!-- claude-session:ceba26f0-757c-421b-bf42-0ecdd8cefe3f:end -->

<!-- claude-session:677536ba-f9da-4aff-a81f-3b97b9c38f98:start -->
## 2026-09-01 10:50 IST | Claude session `677536ba-f9d`

### User prompts
> in a @dataviz-fix/ workflow, a stacked bar was wrongly chosen instead of multiple lines. i'm pasting below the reasoning for it. is there something in the dataviz slector skill that can be fixed os this doesn't happen...
> [Request interrupted by user]
> wait

### Work done
- All 158 pass, import clean. (inspection.py has no existing unit tests - it needs rendered artifacts - so I'm matching repo coverage rather than adding an isolated one; the new branch mirrors the already-working `legen...
- Done. Committed + pushed. **The gap:** the inspector only flagged the *redundant* case - `EXTERNAL_LEGEND`/`REDUNDANT_COLOUR` (low, eraser-test) when a legend duplicates existing direct labels. The inverse - colour ca...

<!-- claude-session:677536ba-f9da-4aff-a81f-3b97b9c38f98:end -->

<!-- claude-session:3c45bd2e-a80f-44f4-a78c-9a13963d1b8b:start -->
## 2026-09-01 11:04 IST | Claude session `3c45bd2e-a80`

### User prompts
> we have some issues with @recommend_text_placement. this was for a stacked bar wwhere hte lables had to ON the boxes, but the labels were pushed out, and evetrything became malformed. here is the entire logs. i'm also...
> [Image #6] i have a problem wtih this graph taht was again produced in the fix workflow. since the categories are q1:q4, it's basically a time series. and to invert axes for a time series is not correct. also , i don'...
> [Image #7] another case - 1. we should ideally have free Y axes for this? or a slopegreaph rather than small multiples? 2. annotations aer both benign and distract. and possibly have too many significant digits. 3. we...

### Work done
- Now CHANGELOG + DEVLOG, then commit.
- Pushed `2ce5b39`. 18 tests green, validated, installed. ## What it does now `recommend_text_placement` gets a post-placement pass. It already receives both the annotations and the on-mark `data_label`s with positions,...

<!-- claude-session:3c45bd2e-a80f-44f4-a78c-9a13963d1b8b:end -->

<!-- claude-session:b6f11ead-9e24-43d1-abf3-ced4aa84581a:start -->
## 2026-09-01 12:22 IST | Claude session `b6f11ead-9e2`

### User prompts
> this is in response to my comment taht charts that are being pr oduced using htis skill nowadays don't look "premium enough". one issue is - we might have too many labels. how do we resolve that here? this is the c om...
> [Request interrupted by user]
> dont do all of this. int he list above, fix 1 (add what earns a direct label in skill), 2 (rule on when axis needs to be dropped), 3 only. others less important

### Work done
- All changes trace to the task. Commit + push.
- Done. Pushed `32494f5`, local == `origin/main`. New skill live and installed. ## What shipped **New `dataviz-aesthetic`** — post-render composition gate. Runs after execution clears defects, as one step-back-and-look-...

<!-- claude-session:b6f11ead-9e24-43d1-abf3-ced4aa84581a:end -->

<!-- claude-session:eaa89029-a2ba-487f-9123-6ae626373144:start -->
## 2026-09-01 13:26 IST | Claude session `eaa89029-a2b`

### User prompts
> input: [Image #10] ;output: [Image #11] . a few failures in the chart selection. 1. why 2 graphs here? 2. why even the s tackedchart? i would've just maybe drawn 4 lines. 3. why do wehave a Y axis here?
> no don't render. think of what skills we need to fix here.
> this is the logs from the run,if it helps you debug better : { "case_id": "2a81a87f78c24b3bb2861ec4ef91d503", "email": "karthik.shashidhar@gmail.com", "prompt": "", "created_at": "2026-09-01T09:54:35.306076+00:00", "c...

### Work done
- Fair. My reject rules were just this chart's failure encoded as triggers - exactly the [[no-hardcoded-cases-in-skill-rules]] trap. "Stacked+time→reject", "twin-panel identical values→reject" don't generalize; next fai...
- Then capability floor is out. Luna can do the claim↔form check - it just didn't here. What's different about this path: `mode: automatic_critique`, no user prompt. Luna had to self-derive the claim, pick the form, *an...

<!-- claude-session:eaa89029-a2ba-487f-9123-6ae626373144:end -->

<!-- claude-session:4820239b-8003-4eb2-86d6-0ce5720debe5:start -->
## 2026-09-01 15:58 IST | Claude session `4820239b-800`

### User prompts
> label placement algo is comelely broken. check here: [Image #13]

### Work done
- All checks pass, no remote divergence, all 4 files are mine. Committing + pushing.
- Pushed. `main` now matches `origin/main`. **Done — anti-crossing pass shipped.** `dataviz_mcp/text_fit.py` What it does: after all labels are placed, any pair of displaced movable labels whose leader lines cross trade...

<!-- claude-session:4820239b-8003-4eb2-86d6-0ce5720debe5:end -->

<!-- claude-session:945da497-160a-43bd-b68b-3e92af2471e0:start -->
## 2026-09-01 18:57 IST | Claude session `945da497-160`

### User prompts
> one problem - feel like we're more aggressive in using small multiples ratehr than multiple lines. like there's a case with 4 lines which have been divided into small multiples which is overdoing it. way i think about...
> ok no you are confusing. i'll look at these two as completely differnet points (smoothed lines nad facets), and i typically don't draw more than one (max 2) smooth line per graph./ default - one panel, directly labell...
> correct. go on.

### Work done
- CHANGELOG + DEVLOG, then sync and push.
- Pushed. Encoded only the ordering lesson: - **Small-multiple panels** (`dataviz-selector` + `karthik-data-visualization`, both copies): order by decreasing peak value or decreasing story importance, top-left → bottom-...

<!-- claude-session:945da497-160a-43bd-b68b-3e92af2471e0:end -->

## Session (2026-09-01): small-multiples unit rule + one-message-one-graph

### Prompt (paraphrased)
- Small multiples only when all graphs share units, else misleading (example: a grid mixing character length, dollars, and counts).
- Do not use two graphs to convey one message; the only permissible case is decomposing a non-100% stacked bar into an overall total trend line plus per-component small multiples.
- Asked for the specific rules, not a generic meta-principle; no hardcoded example.

### Decisions
- Encoded as two plain selector rules, no "two-currencies" abstraction, no reference to the source example.
- Rule 1 hung off the existing small-multiples bullet, flagged as distinct from shared-vs-free scale (which is within one unit).
- Rule 2 extended the existing "two panels, same grain and numbers" guardrail. Exception restricted to non-100% stacks - a 100% stack total is constant, a flat line that earns no graph.
- Scope: `dataviz-selector` only (both copies). Not extended to idea-critique/execution.

### Work done
- Edited both SKILL.md copies, verified identical, ran `./sync.sh --no-pull`.
- CHANGELOG entry added. Commit + push.

## Session (2026-09-01): do not invent groupings to manufacture a claim

### Prompt (paraphrased)
- A recent output split one distribution into two panels (100% stacked bar + a lines panel), and the lines panel collapsed several categories into a single bucket to force a clean two-way crossover.
- Beyond the two-panel redundancy (already covered), the stronger general rule: do not invent groupings just to make a point; you need a strong reason to group data.
- "Other" is the important exception - grouping the residual you are *not* claiming about is fine.

### Decisions
- New Hard guardrail in `dataviz-selector` (both copies), placed right after the graphical-integrity guardrail (both are integrity rules).
- Test encoded: suspect when a grouping merges the very categories the claim rests on to sharpen the claim; fine when it sets aside residual categories the claim does not depend on ("Other").
- No example baked in; scope selector only.

### Work done
- Edited both SKILL.md copies, verified identical, ran `./sync.sh --no-pull`.
- CHANGELOG entry added. Commit + push.

<!-- claude-session:276f617e-658c-497b-995b-eef6f35ef0ed:start -->
## 2026-09-01 19:19 IST | Claude session `276f617e-658`

### User prompts
> another thing - small multiples only when all graphs have the same units. else can be really misleading. like in this csae (showing both original and corrected). [Image #16] . the other (fairly important) thing - we d...
> not generic. just put teh specifics. don't hardcode like you have here. discuss before committing
> 1. yes, restrict to non100% stacked only. else we get a flat line getting its own graph which si pointless; 2. selector only

### Work done
- Good catch - "Other" is exactly the licensed case, and my draft wrongly used it as the example of the sin. Revised: > **Do not invent groupings to manufacture a claim.** Merging categories into coarser buckets (forcin...
- Pushed. New Hard guardrail in `dataviz-selector` (both copies), synced, CHANGELOG + DEVLOG updated: **Do not invent groupings to manufacture a claim** - grouping needs a reason in the data or the question, never that...

<!-- claude-session:276f617e-658c-497b-995b-eef6f35ef0ed:end -->

<!-- claude-session:218aeedc-a773-4ea4-ae39-89a76948f5b1:start -->
## 2026-09-01 19:57 IST | Claude session `218aeedc-a77`

### User prompts
> suddenly i'm wondering if scales=free_y for small multiples is actually a good idea.
> i'm wondering - if the key claim is teh "slope" in multiple charts, is small multiples the rihgt idea at all?
> so basically if small multiples, then we have shared Y only. there is no case now for free Y. and maybe we should tighten the small multiple selection as well - if it's a trend we need to show, may not be ideal to use...

### Work done
- Synced/installed. Commit + push.
- Done. Pushed. Both edits, both copies, synced + installed: 1. **Shared y** now triggered by *any* cross-panel comparison - levels **or** slopes/rates. Free scales narrowed to per-panel shape with no cross-panel read....

<!-- claude-session:218aeedc-a773-4ea4-ae39-89a76948f5b1:end -->

<!-- claude-session:af2047bf-4a94-4053-8b63-035e10cbf0ea:start -->
## 2026-09-01 20:27 IST | Claude session `af2047bf-4a9`

### User prompts
> annotations here seem rather weak. is this a model issue? earlier using possibly stronger models i've got annotations like this: [Image #20]. and now i'm getting stuff like this: [Image #21]
> causal is fine - we don't ahve that data here in the new place. it's the fact taht such weak annotations are being creatd in the first place. i don't think the checker is the right place to get rid o them
> i made some changes on the website side and i still get this, including hte badly placed annotations: [Image #22]

### Work done
- Agree. Checker is post-hoc trim - catches mechanical id-level redundancy (`redundant_annotations`) after weak candidates already exist. Wrong lever. Two deeper problems it can't fix: 1. **Restatement that isn't litera...
- Website change didn't take, and the annotation actually got worse. Three failures in this render: 1. **Fabricated series.** The dashed grey diagonal from 20% (1970s) up to ~58% (2020s), pinned to two grey ghost dots -...

<!-- claude-session:af2047bf-4a94-4053-8b63-035e10cbf0ea:end -->

<!-- claude-session:0a6d0d5f-479c-4c3d-91d3-d56eafa5f0f9:start -->
## 2026-09-01 21:01 IST | Claude session `0a6d0d5f-479`

### User prompts
> latest run of canonical set produced some really horrible charts. here is the logs: { "schema_version": 2, "experiment_id": "experiment", "content_retention": "metadata_and_fingerprints_only", "privacy": "Private audi...
> [Request interrupted by user for tool use]

### Work done
- Charts seen. Real problems, per case + systemic. Caveman. **What broke, case by case:** - **01**: Input = "Men" table (implies Women table too). Output dropped gender entirely + floating annotation boxes + value label...

<!-- claude-session:0a6d0d5f-479c-4c3d-91d3-d56eafa5f0f9:end -->

<!-- claude-session:fe89a7b7-aa35-431f-bc6b-22f18cfc2983:start -->
## 2026-09-02 11:10 IST | Claude session `fe89a7b7-aa3`

### Work done
- Session captured, but there was not enough structured activity to summarize.

<!-- claude-session:fe89a7b7-aa35-431f-bc6b-22f18cfc2983:end -->

<!-- claude-session:4200f127-8e8b-404a-bd4e-738b14100a4a:start -->
## 2026-09-02 11:10 IST | Claude session `4200f127-8e8`

### User prompts
> i wnat to isolate the effects of teh core skill set here and the harness that sits on top, and see what mgiht b e causing this issue. can you start by applying @dataviz-fix/ on ~/Downloads/openrouter.png ?
> where is the output? put it back in downloads
> ok there is a huge problem here. we're losing a lot of data. why did we decide that showing individual series was not important? also - the dataviz-fix skill creates a bunch of sub-sessions i thought to isolate maker-...

### Work done
- Synced and installed. Committing + pushing.
- Fixed and shipped. **What changed:** the driverless fallback in `dataviz-construct` + `dataviz-fix` (claude + codex) no longer says "walk stages inline." It now says: if handed the skill directly **and** you can spawn...

<!-- claude-session:4200f127-8e8b-404a-bd4e-738b14100a4a:end -->

<!-- claude-session:13896fdc-f69b-438b-8e67-6d7a1a429f13:start -->
## 2026-09-02 11:35 IST | Claude session `13896fdc-f69`

### User prompts
> i want to test the skills locally and see what regression happens here and hwat in the harness. cna you lok at openrouter.png in the downloads folder and fix it/
> <task-notification> <task-id>abd7d0609b4a2c460</task-id> <tool-use-id>toolu_01RmSW6VgaxzvecKiB59rtqP</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/42...
> <task-notification> <task-id>a2d6fa3428fe6bea4</task-id> <tool-use-id>toolu_01HBGoLjjctYyJuyWegAivVH</tool-use-id> <output-file>/private/tmp/claude-501/-Users-Karthik-Documents-work-karthik-data-visualization-skill/42...

### Work done
- It's not new, and it's in the package because it's **executable driver code, not skill content.** `stage_contracts.py` is a real Python module. It defines the staged pipelines (`REPAIR_PIPELINE`, `STORY_PIPELINE`, the...
- Leaving it. Done for this session: skill guidance decoupled from your harness (visual read is now a real check; HTML/SVG a legit renderer), no R/Python regression, committed + pushed (`82ca2dd`). `stage_contracts.py`...

<!-- claude-session:13896fdc-f69b-438b-8e67-6d7a1a429f13:end -->

<!-- claude-session:2c3f1bab-8c32-4855-b5ac-62621403c95c:start -->
## 2026-09-02 12:36 IST | Claude session `2c3f1bab-8c3`

### User prompts
> we have a problem with annotations. most are next to useless. check out @canonical-examples.pdf for example. we put in a new rule yesterday preventing anotations that direcxtly label numbers but including those that t...
> a more important thing - a lot of charts actually DON'T need annotations. are we forcing them? how do we put a higher threhold for placing them? and i don't want the new whitelist to genrate nonsensical stuff now

### Work done
- All 28 pass. Extending the CHANGELOG entry with this threshold work:
- Done. Attacked the forcing function at all three layers, not just the wording. **Were we forcing annotations? Yes — structurally, in three places:** 1. **`needs_annotations` defaulted on vibes.** The selector set it f...

<!-- claude-session:2c3f1bab-8c32-4855-b5ac-62621403c95c:end -->

<!-- claude-session:52978d48-02cd-4697-bef7-0964c4149f0f:start -->
## 2026-09-02 12:48 IST | Claude session `52978d48-02c`

### User prompts
> check these charts. [Image #2] (there are 2 from 2 runs, side by side for comparison). label placement is very off. like we don't need those dashes for hte series labels. they could ahve been put closer to the point....
> one more thing - is there a hierarchy? data labels placed first. then things like category labels. FINALLY annotations.

### Work done
- All green. Commit + push (repo maintainer default + auto-push):
- Fixed + pushed. Root cause and fix: **Bug (`recommend_text_placement`):** anchor was used as the box's top-left corner, drawn *on* the point. Point is an obstacle → box always overlaps → always bounced by ring-search...

<!-- claude-session:52978d48-02cd-4697-bef7-0964c4149f0f:end -->

<!-- claude-session:c7939796-c4b6-4957-8dd6-885d36814c3d:start -->
## 2026-09-02 13:46 IST | Claude session `c7939796-c4b`

### User prompts
> back to the annotations thing, the recent fix has NOT solved it. still get meaningless annotations. and check these two plots (the one on the right has SEVERAL other issues, but we'll get to that after we've got measj...
> in this case the annotaitons shouldn't have been generated at all. they add zero value. that's the fix. not the later gates
> [Request interrupted by user]

### Work done
- Pushed. Let me fold the label side into memory so both guards travel together.
- Done. The three-way cut is now consistent across all skills, contract, and docs; committed + pushed; memory holds both guards. **The rule now:** - **Annotation** = a fact not in the data (cause, event, regime change)....

<!-- claude-session:c7939796-c4b6-4957-8dd6-885d36814c3d:end -->

<!-- claude-session:8011ebd8-8b7a-4918-958a-87a86fa6d2e5:start -->
## 2026-09-02 17:00 IST | Claude session `8011ebd8-8b7`

### User prompts
> we have a "no small multiples unless units are same" rule but this keeps happening [Image #1]
> check again. i've rsestarted my account
> continue what you were doing

### Work done
- Case 03 is the bad one. Here's what happened. ## Case 03 — the lower panel is a black smear The redesign is **total line (top) + one 100%-stacked-area panel (bottom)**. The bottom panel — "Model mix (share of weekly u...
- Good call — the metadata does explain it, once you line up `execution` call counts against the "measured defects" in each footer. ## The execution gate is the common thread | Case | build calls | **execution calls** |...

<!-- claude-session:8011ebd8-8b7a-4918-958a-87a86fa6d2e5:end -->

<!-- claude-session:a2bd1afb-a324-4c95-8c9f-5e4694cb2c7f:start -->
## 2026-09-03 10:27 IST | Claude session `a2bd1afb-a32`

### User prompts
> one problem i'm findng with the current dataviz-fix harness is that the R code it generates is way too verbose (i'll paste an example below). i've been writing fairly concise R code for sevearl yaesr now (since 2019 a...
> eg: library(ggplot2) library(grid) build_chart <- function() { # dataviz-section: data periods <- c("1970", "1980", "1990", "2000", "2030", "2050") categories <- c( "Cereals, food", "Roots and tubers", "Sugar", "Pulse...
> 2

### Work done
- Parking. Writing the design doc so it's recoverable, then stopping.
- Parked. Design + corpus evidence + resume path saved: `docs/parked-karthik-ggplot-skill.md` Captures: it's a code-efficiency rule set (not a theme/style), the 7 rules with anti-pattern map, non-frozen framing, corpus...
- Touched files: `docs/parked-karthik-ggplot-skill.md`

<!-- claude-session:a2bd1afb-a324-4c95-8c9f-5e4694cb2c7f:end -->

<!-- claude-session:469eb3ac-86b4-4535-9b4f-3da425a1c86c:start -->
## 2026-09-03 11:43 IST | Claude session `469eb3ac-86b`

### User prompts
> rigvht now the problem wtih the @dataviz-construct/ is that there are too many loops. t oo amny revisions. the bteter idea is to build better on the first go and eliminate these loops and revisions. a harness did some...
> too much jargon herei 'm not undertsanading
> yes this is better. also remember we have a text placement MCP already. for wrapping, adjustment etc. now - should we really draw to be able to find the places of all the labels and stuff? can't this be done bya a mod...

### Work done
- Done, pushed (`02093e6`). All three extensions work and are proven on real renders. ## What now works on R | Case | How | Proof | |---|---|---| | **coord_flip** | Cross-term affine (flip maps x→vertical, y→horizontal;...
- Good call — this thread's done its job. Here's a self-contained prompt for a fresh session: ``` Build a `refit_chart` MCP tool in the dataviz repo. Repo: /Users/Karthik/Documents/work/karthik-data-visualization-skill...

<!-- claude-session:469eb3ac-86b4-4535-9b4f-3da425a1c86c:end -->

<!-- claude-session:30cee37e-d275-4710-878e-ab672b3051af:start -->
## 2026-09-04 10:37 IST | Claude session `30cee37e-d27`

### User prompts
> Build a `refit_chart` MCP tool in the dataviz repo. Repo: /Users/Karthik/Documents/work/karthik-data-visualization-skill Use skills: test-driven-development, dataviz-construct. Python venv at .venv (`.venv/bin/python...
> was this the thing about refit, or was this more about the fonts and stuff?

### Work done
- Done. Pushed to main (`02093e6..10fca8d`), local == upstream. **`refit_chart` shipped** - deterministic render→inspect→grow loop, no model turn for geometry arithmetic. - **`dataviz_mcp/refit.py`** - render → inspect...
- This was **refit** - the resize loop. Not the fonts/text stuff. Quick line between them: - **refit (this session)** - only grows the *canvas* when something clips the edge or facet panels get squashed. Pure "make the...

<!-- claude-session:30cee37e-d275-4710-878e-ab672b3051af:end -->

<!-- claude-session:f8a961d6-04b0-4d1d-9881-884ca3be0f41:start -->
## 2026-09-04 11:10 IST | Claude session `f8a961d6-04b`

### User prompts
> now that we've recently pushed a bunch of tools, any skills around this we need to rewrite? think through carefully and do a comprehensive job
> not just refit. we have other recent tools as well
> is reserrve frame and place on hcart being claled appropriately?

### Work done
- All 212 pass. Adding CHANGELOG note and committing.
- Pushed `62bfeb3`. Answer to "are `reserve_frame` and `place_on_marks` being called appropriately?": **Mostly yes — but found and fixed one real misdirection bug.** How they're wired (all correct): - They're MCP tools;...

<!-- claude-session:f8a961d6-04b0-4d1d-9881-884ca3be0f41:end -->

<!-- claude-session:b4103f1b-ba79-4005-9d0b-1c33ff6d27bc:start -->
## 2026-09-04 11:25 IST | Claude session `b4103f1b-ba7`

### User prompts
> recnently made a few new changes in the repo - some MCPs got added. do another comprehensive pass of all the MCPs and skills and make sure theey are all internally consistent.
> some inputs from the harness: 2. Leader-line placement needs to become deterministic. The patch model received measured placement evidence but generated: geom_segment(x = 6, y = value, xend = 5.34, yend = label_y) Tha...
> are you sure that this is fixed properly, and that the skills have been appropriately modified to reflect the new tools?

### Work done
- 221 pass, clean. Committing the follow-up.
- You were right to push back. Verifying instead of asserting turned up two real gaps in what I'd shipped: **What was actually wrong in my first pass:** 1. **`karthik-data-visualization` — the umbrella skill — was misse...

<!-- claude-session:b4103f1b-ba79-4005-9d0b-1c33ff6d27bc:end -->

<!-- claude-session:d0d1e6cc-d183-48b3-8f50-3a4022302c58:start -->
## 2026-09-04 16:28 IST | Claude session `d0d1e6cc-d18`

### User prompts
> have our skills gotten too heavy and verbose through multiple iterations? can we audit them to make sure they are concise while still maintianing full essense?

### Work done
- Clean change set — exactly the 20 edited skills (×2 surfaces) plus CHANGELOG; the three untouched lean skills correctly absent. No upstream divergence. Committing and pushing.
- Done. Pushed to `origin/main` (`6fd647f..9166903`), local matches upstream, all 221 tests pass, validator clean. ## What the audit found and fixed Your instinct was right — the skills had bloated, in two distinct ways...

<!-- claude-session:d0d1e6cc-d183-48b3-8f50-3a4022302c58:end -->

<!-- claude-session:698b3052-ff22-481f-b43d-bb360baf0089:start -->
## 2026-09-04 17:08 IST | Claude session `698b3052-ff2`

### User prompts
> a recent run produced this graph.[Image #2] i thougth with our new layout selector and other MCPs, this should ahve been better. but hte Y axis is badly f ormed (don't need to go till 100 here). what'sh appening?
> no the objective here is to fix the process not hte chart.
> [Request interrupted by user]

### Work done
- Pushed as `6d6702e`. Now fix the memory note — my earlier update drew the wrong lesson (it said "add a deterministic planning tool"), which we just reversed.
- Done. Reverted and pushed as `6d6702e`. **Final state — no tool, just the real fix:** - Undid the nudge: *"data scales represent the intended data domain"* → *"the data's plotted extent, not 0-100 unless the data reac...

<!-- claude-session:698b3052-ff22-481f-b43d-bb360baf0089:end -->

<!-- claude-session:606c28b2-6cf8-424e-bc19-7b4f2e66b4c9:start -->
## 2026-09-04 17:41 IST | Claude session `606c28b2-6cf`

### User prompts
> inputs from the harness on what should improve inthe skills / tools These changes belong in the visualization skill/MCP layer: - Give every rendered label a stable semantic identity: series, period/category, value, so...
> [Request interrupted by user]
> again i think this is overengineering abandon this effort

### Work done
- Abandoning. Reverting everything.
- Reverted. `git status` clean, `git diff` empty — identity.py deleted, text_fit.py and its tests back to original. No changes remain on disk. Nothing committed, nothing pushed. The scratchpad plan doc still exists (out...

<!-- claude-session:606c28b2-6cf8-424e-bc19-7b4f2e66b4c9:end -->

<!-- claude-session:49f9acbf-6e2a-4e46-88a1-55ff4116875e:start -->
## 2026-09-04 21:13 IST | Claude session `49f9acbf-6e2`

### User prompts
> we are having some issues in the harness, with the results of the inspection, since now we're not regenerating full code at inspection. from the harness:: The immediate upstream defect is therefore: > On-mark labels l...
> ok this is really silly that we are looking at clashes between a labeland itself. surely there must be an easy way of dealingiwth it? also harness can be fixed as per what skill / MCP demands. another issue i've seen...
> recommend A for the data lable thing. just fixit simply. and fix the nearest search thing. remember we can wrap andstuff . also - do we reallyneed taht skill rule? seems overengineerting to me

### Work done
- Now fix my ggplot test — the labels are now role `label` with `on_data_layer`, not `data_label`.
- Good question, and it cuts to the actual root — I've been patching a check whose premise is wrong. **Direct answer: for text-vs-mark, you're right — we mostly don't need it.** A direct label is *supposed* to sit on it...
- Touched files: `dataviz_mcp/inspection.py`, `dataviz_mcp/rendering.py`, `dataviz_mcp/tests/test_render_inspect.py`
- dataviz_mcp/inspection.py | 7 +++++++

<!-- claude-session:49f9acbf-6e2a-4e46-88a1-55ff4116875e:end -->

<!-- claude-session:f9fc71c3-f7e4-4286-ae55-0aece8378831:start -->
## 2026-09-04 22:08 IST | Claude session `f9fc71c3-f7e`

### User prompts
> started a new session becasue we're going round and round in circles. this was a recent output and it was flagged as problematic (text clashes and stuff). this looks perfectly good toe me[Image #5]
> NO. i'm only interserted in fixing code (in this folder) never fixing graphs
> see these are relatively minor. and revisions are expensive in both time andtokens.

### Work done
- Verify tree now matches session-start (only the `on_data_layer` diff remains):
- Reverted. `grep -c` returned 0 = my helpers gone (the exit 1 is just grep finding no matches — expected). Working tree now matches session start: only the pre-existing `on_data_layer` diff remains (inspection.py 7+, r...
- Touched files: `dataviz_mcp/inspection.py`, `dataviz_mcp/rendering.py`, `dataviz_mcp/tests/test_render_inspect.py`
- dataviz_mcp/inspection.py | 7 +++++++

<!-- claude-session:f9fc71c3-f7e4-4286-ae55-0aece8378831:end -->

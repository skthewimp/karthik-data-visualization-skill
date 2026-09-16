# Reliable chart-value reads for `dataviz-extract`

Date: 2026-09-16
Status: approved design, pre-implementation

## Problem

Extraction - recovering the period-by-category data table out of a source chart
image - is the least-engineered step in the repair pipeline. The whole method is
one line in `dataviz-extract`: *"read the numbers off the image with judgment."*
That asks the model for an **absolute value estimate** straight from pixels, which
is exactly the read models (and humans) are worst at: the internal pixel-to-value
mapping is fuzzy, biased toward round numbers, and compresses range. Two failure
shapes recur:

1. **Position reads** (no printed label) - the value is guessed off the gridlines
   and lands wrong, worse on log/transformed axes.
2. **Label misreads** (printed label present) - the number is there but read wrong
   (dropped decimal, 3.8 as 3.6, thousands separators).

We want the *read itself* to be more reliable. This is deliberately **not** about
downstream reconciliation, provenance tags, or validation gates - those were
considered and rejected. The fix is the reading technique plus a deterministic
arithmetic assist.

## Design

### 1. Read method (the core change - `dataviz-extract` skill prose)

Replace *"read the numbers off the image with judgment"* with a two-regime read
primitive, kept general (no enumerated regimes, counts, or example-specific rules):

- **Labelled cell** → transcribe the printed number literally, glyph by glyph, at
  resolution; trust it over any position estimate. This is the only real lever on
  label misreads: read the glyphs, do not infer the number you expect.
- **Unlabelled cell** → do **not** estimate the value. Identify the two nearest
  printed reference ticks that bracket the mark and the fraction (0-1) between them,
  then obtain the value by interpolating that bracket. Bracket-and-interpolate is
  the judgment models are actually good at; it is local, so scale error does not
  accumulate; and log axes fall out per-bracket with no special-casing.

The interpolation arithmetic is done by the tool below (the normal path), not in
the model's head.

### 2. New MCP tool - batch bracket interpolation

A new deterministic tool in `dataviz_mcp/` (new module, e.g. `mark_read.py`, core
function `read_marks_from_anchors`, registered in `server.py` beside
`recommend_precision`, with tests in `dataviz_mcp/tests/`).

- **Input:** axis `transform` (`"linear"` | `"log"`) and a list of `marks`, each
  `{key, lo, hi, fraction}` where `lo`/`hi` are the two bracketing printed tick
  **values** and `fraction` ∈ [0,1] is the mark's position between them.
- **Output:** a list of `{key, value}`.
  - linear: `value = lo + fraction * (hi - lo)`
  - log: `value = 10 ** (log10(lo) + fraction * (log10(hi) - log10(lo)))`
- **Guards:** `lo < hi` ordering enforced/normalised; `fraction` clamped to [0,1]
  with a warning; log requires `lo > 0`. Model does the perception (which ticks,
  what fraction), code does all the scale math.

### 3. Tool coupling - required-when-present

The skill instructs the tool call as the **normal** path for unlabelled cells, not
an optional accelerator. Only if the MCP server is genuinely not registered does the
model interpolate the bracket by hand. This keeps extract consistent with the tools
already beside it in the pipeline (`render_chart`, `place_on_marks`,
`extract_palette_from_image`, `recommend_precision`), which are all
required-when-present and degrade rather than hard-fail. The skill drops its current
"there is no MCP tool for it" line.

### 4. Schema - no change

`_DATA_TABLE` in `stage_contracts.py` already holds final cell values in `rows`; the
tool's output populates those cells. Nothing new is added to the diagnose artifact.
(Per-cell provenance tags were considered and rejected.)

## Files touched

- `dataviz-extract/claude/SKILL.md` and `dataviz-extract/codex/SKILL.md` (currently
  byte-identical - same edit).
- `docs/skills/dataviz-extract.md`.
- `_REPAIR_DIAGNOSE` prose in `dataviz_mcp/stage_contracts.py` (the extract
  instructions embedded in the repair contract).
- New tool module + `server.py` registration + `dataviz_mcp/tests/` test.
- README tool list / CHANGELOG / DEVLOG per repo workflow.
- Install via `./sync.sh --no-pull`.

## Test plan (before any commit or push)

Real cases only, judged against the source image by eye - the picture is the truth.

1. Select 2-3 real `original.png` cases from `tester-outputs/*/runtime/cases/`
   spanning both regimes (at least one labelled, one position-read; a log axis if
   available).
2. Per case, run extraction twice with weak subagents (sonnet + haiku): **old skill**
   vs **new skill + tool**.
3. Judge by eye - read table beside the source image: which method's numbers match
   the picture, with fewer round-number snaps and misreads.
4. Commit only if the new method is at least as good as the old across the cases.

## Explicitly out of scope

- Reconciliation / sum-to-total / share-to-100 checks.
- Per-cell provenance or confidence tags in the artifact.
- Deterministic pixel-coordinate reading (models can't report exact pixels
  reliably; the bracket+fraction primitive replaces it).
- Any change to label identity rules (`extract-labels-read-only` stands unchanged).

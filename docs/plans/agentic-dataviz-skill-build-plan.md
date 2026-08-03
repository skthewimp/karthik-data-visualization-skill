# Agentic dataviz skill build plan

Purpose: build Karthik's repeatable agentic dataviz workflow inside this repo, without context rot.

Core thesis:

```text
question/source → contextual cleaning → denominator → comparison → evidence → claim → visual brief → chart → critique → revision
```

This repo now covers chart selection, chart taste, slide style, critique, analysis contracts, raw-dataset question generation, contextual cleaning, and an end-to-end orchestrator. The remaining gap is narrower: evidence building, claim validation, and a reusable visual brief.

## Current baseline

Already in this repo:

| Skill | Role | Status |
|---|---|---|
| `karthik-analysis-planner` | fuzzy question → analysis contract | built |
| `dataviz-selector` | claim/comparison → chart form | built |
| `karthik-data-visualization` | Karthik chart taste/style | built |
| `dataviz-critique` | critique/redesign existing charts | built |
| `karthik-powerpoint-style` | analytical slides/decks | built |
| `dataset-question-generator` | raw dataset → fresh visualisable questions | built |
| `karthik-data-cleaning` | contextual inspection/cleaning before analysis | built |
| `dataviz-orchestrator` | full dataset-to-visual-story workflow | built |

## Skills to build

Build these as root-level skill folders, matching existing repo shape:

```text
<skill-name>/
  README.md
  codex/SKILL.md
  claude/SKILL.md
  references/*.md
```

### 1. `dataset-story-profiler` / now mostly `dataset-question-generator`

**Job:** inspect a dataset plus optional question/context; propose visual stories before charting.

**Use when:** user says “visualise this dataset”, “what can we show from this?”, “find chart ideas”, or gives data without a sharp claim.

**Inputs:** dataset path/preview, optional question, optional audience/context.

**Outputs:**

- row grain
- columns/types/units/time range
- missingness/weirdness
- likely denominators
- 5 candidate stories
- evidence needed for each
- likely chart form
- comparison baseline
- confidence
- misleading risk
- recommended first story
- “do not visualise yet” list

**Current state:** the built `dataset-question-generator` covers most of this. Do not build a second overlapping profiler unless it has a clearly different output contract.

**Depends on:** `karthik-data-cleaning` when the raw source is messy, and `karthik-analysis-planner` when user gives a fuzzy question.

**Test cases:**

- Surbhi Bollywood `movies.json`
- Bangalore 4pm rain question/data

### 2. `karthik-evidence-builder`

**Job:** turn selected story/hypotheses into computed facts from data, not prose from priors.

**Use when:** a story/claim needs validation against raw data before charting or writing.

**Outputs:**

- data profile
- analysis table grain
- explicit denominator/numerator
- computed facts table
- sanity checks
- sensitivity checks where definitions are ambiguous
- candidate supported claims
- caveats from data limitations

**Rules:**

- never answer from model memory
- inspect schema first; use `karthik-data-cleaning` when parsing/reshaping/joins affect the answer
- compute denominators explicitly
- keep facts before prose
- flag when data cannot answer the question

**Depends on:** `dataset-question-generator` or `dataviz-orchestrator`, `karthik-analysis-planner`, `karthik-data-cleaning`.

### 3. `karthik-claim-validator`

**Job:** decide which claims survive evidence.

**Use when:** computed facts or candidate claims exist and need scrutiny before charting/public use.

**Checks:**

- claim matches metric
- denominator explicit
- comparison fair
- sample size adequate
- outliers/seasonality/selection effects considered
- causal language avoided unless design supports it
- likely misreadings listed
- caveat preserved

**Outputs:**

- supported / weakened / rejected verdict
- revised defensible claim
- evidence bullets
- caveats
- charting recommendation
- human-review trigger if risky

**Depends on:** `karthik-evidence-builder`.

### 4. `visual-brief-generator`

**Job:** convert a surviving claim into a chart spec before code.

**Use when:** a story is selected and validated, before chart generation.

**Outputs:**

- main claim
- audience
- evidence columns
- filters/aggregation
- comparison baseline
- chart form
- X/Y/colour/facet/label encodings
- annotations
- source/caption/caveat
- acceptance criteria
- refusal / pause conditions

**Depends on:** `dataviz-selector`, `karthik-data-visualization`, `karthik-claim-validator`.

### 5. `matplotlib-deslopper`

**Job:** clean default Python/matplotlib charts into acceptable static charts.

**Use when:** chart code/output is matplotlib/plotnine/seaborn and looks default, cluttered, or workshop-participant-ish.

**Fixes:**

- white background
- charcoal text
- remove top/right spines
- simplify grids
- replace default colours
- direct labels where possible
- claim-first title/subtitle/caption
- source/caveat
- static PNG/SVG export

**Depends on:** `karthik-data-visualization`.

### 6. `agentic-dataviz-workflow`

**Job:** umbrella orchestrator for the full workflow.

**Current state:** largely covered by the built `dataviz-orchestrator`. Extend that skill unless a separate workflow skill becomes clearly necessary.

**Use when:** user wants to visualise a dataset end-to-end.

**Sequence:**

```text
context/data intake
→ analysis contract if question is fuzzy
→ contextual data cleaning if needed
→ dataset-question-generator if no question exists
→ choose/rank story
→ karthik-evidence-builder
→ karthik-claim-validator
→ visual-brief-generator
→ chart implementation
→ dataviz-critique
→ one revision
→ next-run notes
```

**Build last**, after upstream skills settle.

## Parallel build lanes

### Lane A: analytical middle

Can run in parallel but coordinate output contracts:

1. `dataset-story-profiler`
2. `karthik-evidence-builder`
3. `karthik-claim-validator`

### Lane B: chart production

Can run independently:

1. `visual-brief-generator`
2. `matplotlib-deslopper`

### Lane C: integration

Run after A+B:

1. `agentic-dataviz-workflow`
2. end-to-end test
3. remove overlap between skills

## Shared definition of done

Each skill is done only when it has:

- `README.md`
- `codex/SKILL.md`
- `claude/SKILL.md`
- at least one `references/*.md` if workflow is long
- concise trigger description in YAML frontmatter
- output template
- failure modes / refusal conditions
- mini-example using Surbhi Bollywood JSON or Bangalore rain
- docs page under `docs/skills/<skill>.md`
- README root list updated
- `docs/skills/README.md` updated
- local sync tested with `./sync.sh --no-pull`

## Shared test datasets/questions

### Test 1: Surbhi Bollywood JSON

Source:

```text
https://raw.githubusercontent.com/surbhi-bh/outlier-talk-slides-2026/main/assets/posters/movies.json
```

Known facts:

- 350 rows
- years 1990–2024
- top 10 films per year
- fields: `rank`, `movie`, `year`, `movie_db_link`, `img_link`, `primary_genre`, `nationalist`
- key caveat: top-10 box office sample, not all Bollywood films
- likely story: action rises, romance falls, nationalist-coded films cluster after 2015

### Test 2: Bangalore 4pm rain

Question:

```text
Does Bangalore rain around 4pm?
```

Purpose: test denominator/definition discipline.

Required caveats:

- 4pm must be local time
- rain probability differs from rainfall amount
- “around 4pm” needs a window definition
- complete-hour/day denominator matters

## Standard session prompt

Use this to launch one independent build session:

```text
We are building one skill for the Karthik Data Visualization Skills repo.

Repo:
/Users/Karthik/Documents/work/karthik-data-visualization-skill

Read first:
- docs/plans/agentic-dataviz-skill-build-plan.md
- README.md
- relevant existing skill SKILL.md files

Build only: <skill-name>

Do not build other skills. Keep SKILL.md concise; put long checklists/templates/examples in references/.
Follow existing repo layout: README.md, codex/SKILL.md, claude/SKILL.md, docs/skills/<skill>.md.
Test the skill on the Surbhi Bollywood JSON or Bangalore 4pm rain question.
Update this plan status and relevant docs.
```

## Status board

| Skill | Owner/session | Status | Notes |
|---|---|---|---|
| `dataset-story-profiler` | 2026-07-03 | mostly superseded | covered by `dataset-question-generator`; do not duplicate without new scope |
| `karthik-evidence-builder` | unassigned | todo | depends on profiler output shape |
| `karthik-claim-validator` | unassigned | todo | depends on evidence output shape |
| `visual-brief-generator` | unassigned | todo | can build in parallel |
| `matplotlib-deslopper` | unassigned | todo | can build in parallel |
| `agentic-dataviz-workflow` | 2026-07-03 | mostly superseded | covered by `dataviz-orchestrator`; extend, don't duplicate |

## Integration checks

Before final merge/release:

1. Each skill triggers distinctly; no vague duplicate descriptions.
2. `agentic-dataviz-workflow` names when to call each subskill.
3. Output templates connect cleanly:
   - profiler stories → evidence builder plan
   - evidence facts → claim validator verdict
   - validator claim → visual brief
   - visual brief → chart code
4. No skill encourages charting before claim/evidence unless user explicitly asks for a quick rough draft.
5. Public docs explain the workflow in one screen.

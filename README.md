# Karthik Data Visualization Skills

Public data visualization skills for Codex and Claude, with a local MCP layer for exact-artifact rendering and inspection.

## Start here: agents and LLMs

If you have been pointed at this repository and asked to create or repair a chart, do not begin with the MCP implementation. Start with the skill that owns the judgement, then use MCP for the mechanical stages it supports.

**For a new chart:**

1. Read the `SKILL.md` for your client under `dataviz-orchestrator/{codex,claude}/`.
2. Follow only the handoffs the task needs. Do not add evaluation or case logging to a normal repair.
3. Use `render_and_inspect_chart` for static repairs when available. Inspect the exact export once, then return the best valid artifact; MCP or review failures must not suppress it.

**For an existing chart:**

1. Read `dataviz-fix/{codex,claude}/SKILL.md`.
2. Build and inspect one real artifact.
3. Return the best valid version; use `dataviz-eval` or the case manager only when an audited workflow is needed.

The architecture has one firm boundary:

```text
skills and agent    question, evidence, chart choice, visual judgement, release decision
MCP capabilities    deterministic rendering, exact-file hashes, geometry checks, comparison
```

Installing the skills does not register the MCP server. For the full workflow, complete both parts of [the quick start](#quick-start): install the client-specific skills and register the local stdio server.

### Renderer policy

`render_and_inspect_chart` is backend-neutral and chooses ggplot2 first when `Rscript`, `ggplot2`, and `ragg` are available and the adapter supports the requested static output.

- An explicit user renderer requirement wins.
- Otherwise use ggplot2 through `ragg` when the availability probe succeeds.
- Use Matplotlib only when ggplot2 is unavailable or the adapter cannot produce the requested output, and record the reason in the manifest.
- If Matplotlib is the practical fallback, specify the theme, typography, palette, grid, axes, labels, and spacing deliberately; default Matplotlib aesthetics are a failed visual implementation.
- Both adapters emit the same artifact, specification, layout, inspection, review-view, and manifest bundle. Coverage limitations remain explicit in the inspection report.

This repo contains thirteen related skills, coordinated as a context-sensitive visualization workflow:

1. **`dataviz-fix`** - output-first repair rules: rebuild a pasted chart, inspect the exact export once, return the best valid artifact, and improve it from user feedback.
2. **`dataviz-eval`** - artifact and creator-system evaluation rules for separate blind review, scoped send/revise/redesign decisions, failure analysis, and regression benchmarks.
3. **`dataviz-selector`** - chart-selection rules for deciding what kind of visualization fits a dataset plus question, hypothesis, or data story.
4. **`karthik-data-visualization`** - style rules for producing charts in Karthik's preferred visual language: low chartjunk, direct labels, careful typography, meaningful colour, and Tufte-inspired restraint.
5. **`karthik-powerpoint-style`** - slide and deck rules for making PowerPoint-style presentations in Karthik's analytical, claim-first style.
6. **`dataviz-critique`** - chart critique and redesign rules for diagnosing existing visuals using the question-data-visual trifecta plus Karthik's clarity-first standards, then proposing better alternatives.
7. **`karthik-analysis-planner`** - analysis-contract rules for turning fuzzy natural-language questions into operational definitions, denominators, comparisons, metrics, caveats, and falsifiers before evidence-building.
8. **`dataviz-orchestrator`** - end-to-end workflow for turning a dataset, loose question, and audience into an analysed, styled, critiqued visual story.
9. **`dataset-question-generator`** - upstream skill for profiling raw datasets and generating fresh, visualisable questions before planning or charting.
10. **`karthik-data-cleaning`** - data-cleaning rules for Karthik-style exploratory analysis: inspect, clean in context, inspect again, and avoid generic unsupervised fixes.
11. **`chart-annotations`** - annotation rules for deciding what a chart should mark, which competing candidate wins, how the label is worded, and where it sits.
12. **`chart-explainer`** - accompanying-note rules for writing the two lines that travel with a finished chart or table into an email, notebook, or message.
13. **`karthik-r-analysis-style`** - notebook rules for how an exploratory R scratchpad is written: local precedent, analyst-first probes, tidyverse/tidytable idiom, and the working-note register.

The split is deliberate. The orchestrator routes the work and preserves handoffs; it does not duplicate every specialist procedure. Planning defines the analytical claim and evidence contract. Cleaning establishes provenance, grain, and data validity. Question generation proposes supported questions. Selection chooses an encoding for the task. Construction implements it. Annotation adds supported context. Explanation communicates the result at calibrated strength. Critique diagnoses interpretive failures. Repair manages bounded revisions and reusable lessons. Evaluation independently verifies semantic, visual, evidentiary, and delivery outcomes.

## Repository layout

```text
.
├── dataviz-fix/                     # Output-first chart repair and feedback
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── dataviz-eval/                    # Artifact gate and chart-creator benchmark
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── dataviz-selector/                # Chart-selection skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-data-visualization/      # Chart-style skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-powerpoint-style/        # Presentation-slide skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── dataviz-critique/                # Visualization critique skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-analysis-planner/        # Analysis-contract skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── dataviz-orchestrator/            # End-to-end visual-story workflow skill
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── dataset-question-generator/      # Raw dataset to fresh question prompts
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-data-cleaning/           # Context-sensitive exploratory data cleaning
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── chart-annotations/               # What a chart marks and what the label says
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── chart-explainer/                 # The two-line note that travels with a chart
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-r-analysis-style/        # How an exploratory R notebook is written
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── tester/                          # Local repair-loop case console
├── dataviz_mcp/                     # Local stdio MCP: render, inspect, compare
├── docs/                            # Human docs; subfolder READMEs explain contents
├── sync-skills.py                   # Install Codex or Claude skill surfaces
└── sync.sh                          # Pull + install wrapper
```

Each skill owns its Codex and Claude versions directly. Every public folder has a README so newcomers can navigate without prior context. No generated `dist/` tree is committed.

## Skills

### `dataviz-fix`

Use this when you want to paste or upload a chart, receive a real regenerated visual, iterate with short feedback until it is right, and turn the accepted result into a narrow reusable improvement to the skill stack.

See: [`docs/skills/dataviz-fix.md`](docs/skills/dataviz-fix.md)

### `dataviz-eval`

Use this after rendering when you need a `Send`, `Revise`, `Redesign`, or `Not evaluable` verdict based on evidence, intended meaning, blind audience reading, visual reasoning, and the actual delivery medium. It also supports golden-set regression tests for chart-producing agents and skills.

See: [`docs/skills/dataviz-eval.md`](docs/skills/dataviz-eval.md)


### `dataviz-orchestrator`

Use this when you have a dataset, a loose question, and an audience, and want the full loop: analysis plan, contextual data inspection/cleaning, analysis, story selection, visual choice, Karthik-style charting, critique, and iteration.

See: [`docs/skills/dataviz-orchestrator.md`](docs/skills/dataviz-orchestrator.md)

### `dataviz-selector`

Use this when you have a dataset and a question such as:

- "Which channel is getting less efficient?"
- "Did this launch work?"
- "Why did costs overshoot budget?"
- "Which constituency map shows gerrymandering?"
- "What chart should I use for this survey result?"

The skill chooses the chart form and explains the encoding. Commonly risky forms are treated as context-dependent choices: assess them against the claim, evidence, audience, medium, density, accessibility, and risk of misinterpretation rather than applying a universal blacklist.

See: [`docs/skills/dataviz-selector.md`](docs/skills/dataviz-selector.md)

### `karthik-data-visualization`

Use this after chart selection, when generating or reviewing the visual itself. It covers typography, colours, direct labels, gridlines, axes, annotations, facets, chart density, and export defaults.

See: [`docs/skills/karthik-data-visualization.md`](docs/skills/karthik-data-visualization.md)

### `dataviz-critique`

Use this when you have an existing visual and context such as the intended story, data, audience, or decision, and you want to know what works, what fails, and how to improve it. Alternatives are proposed only when they address a diagnosed mismatch.

See: [`docs/skills/dataviz-critique.md`](docs/skills/dataviz-critique.md)


### `karthik-analysis-planner`

Use this before data work when the question is fuzzy and needs an explicit analysis contract: definitions, unit, denominator, numerator, metric, comparison, caveats, and falsification conditions.

See: [`docs/skills/karthik-analysis-planner.md`](docs/skills/karthik-analysis-planner.md)

### `karthik-powerpoint-style`

Use this when turning analysis into PowerPoint-style slides or deck outlines. It covers claim-first titles, slide layout, chart placement, annotation, source notes, typography, colour, and what to avoid in management presentations.

See: [`docs/skills/karthik-powerpoint-style.md`](docs/skills/karthik-powerpoint-style.md)


### `dataset-question-generator`

Use this when you have a raw dataset and need good seed questions before analysis or charting. It profiles the data, looks for visual signals and denominator traps, rejects stale prompts, and returns a ranked set of fresh visualisable questions.

See: [`docs/skills/dataset-question-generator.md`](docs/skills/dataset-question-generator.md)


### `karthik-data-cleaning`

Use this when preparing messy data for analysis, charting, modelling, or data stories. It follows Karthik's inspect → clean → inspect loop, keeps cleaning context-sensitive, and avoids generic unsupervised fixes.

See: [`docs/skills/karthik-data-cleaning.md`](docs/skills/karthik-data-cleaning.md)


### `chart-annotations`

Use this when a chart is built but the reader cannot see the point without narration. It picks what to mark, ranks competing candidates, constrains the label wording, and sets placement and visual weight.

See: [`docs/skills/chart-annotations.md`](docs/skills/chart-annotations.md)


### `chart-explainer`

Use this when a chart or table is finished and someone else has to be told what it says - a concise note above a graph in an email, under a figure in a notebook, or alongside a screenshot in chat. It uses the shortest sufficient explanation, anchors claims to evidence and comparison, and treats "nothing here" as a legitimate answer instead of manufacturing a finding.

See: [`docs/skills/chart-explainer.md`](docs/skills/chart-explainer.md)


### `karthik-r-analysis-style`

Use this when writing the R analysis itself - an exploratory scratchpad, an RMarkdown or Quarto notebook, a first pass at a dataset that just landed. It covers notebook shape, probe sequencing, the rough working-note register, tidyverse/tidytable defaults, and routing to dbplyr, Arrow, or DuckDB when the data will not sit in memory. It requires an after-plot note on every plot and delegates the wording to `chart-explainer`.

See: [`docs/skills/karthik-r-analysis-style.md`](docs/skills/karthik-r-analysis-style.md)

## Quick start

Clone the repository and choose the skill surface for your client:

```bash
git clone https://github.com/skthewimp/karthik-data-visualization-skill.git
cd karthik-data-visualization-skill

./sync.sh --no-pull --surface codex   # Codex
# or
./sync.sh --no-pull --surface claude  # Claude Code
```

Install the MCP package into an existing environment or a new local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
MCP_PYTHON="$(pwd)/.venv/bin/python"
```

Register it with Codex:

```bash
codex mcp add karthik-dataviz -- "$MCP_PYTHON" -m dataviz_mcp
codex mcp get karthik-dataviz
```

Or register it with Claude Code:

```bash
claude mcp add-json --scope user karthik-dataviz \
  "{\"type\":\"stdio\",\"command\":\"$MCP_PYTHON\",\"args\":[\"-m\",\"dataviz_mcp\"]}"
claude mcp get karthik-dataviz
```

Start a new client session after installation so it loads both the skill text and MCP tools. No daemon is required; the client starts the stdio process when needed.

### Skill installation details

```bash
./sync.sh
```

This pulls latest changes and installs all skills to:

- `~/.codex/skills/karthik-data-visualization`
- `~/.codex/skills/dataviz-selector`
- `~/.codex/skills/karthik-powerpoint-style`
- `~/.codex/skills/dataviz-critique`
- `~/.codex/skills/karthik-analysis-planner`
- `~/.codex/skills/dataviz-orchestrator`
- `~/.codex/skills/dataset-question-generator`
- `~/.codex/skills/karthik-data-cleaning`
- `~/.codex/skills/chart-annotations`
- `~/.codex/skills/chart-explainer`
- `~/.codex/skills/karthik-r-analysis-style`
- `~/.codex/skills/dataviz-fix`
- `~/.codex/skills/dataviz-eval`
- `~/.claude/skills/karthik-data-visualization`
- `~/.claude/skills/dataviz-selector`
- `~/.claude/skills/karthik-powerpoint-style`
- `~/.claude/skills/dataviz-critique`
- `~/.claude/skills/karthik-analysis-planner`
- `~/.claude/skills/dataviz-orchestrator`
- `~/.claude/skills/dataset-question-generator`
- `~/.claude/skills/karthik-data-cleaning`
- `~/.claude/skills/chart-annotations`
- `~/.claude/skills/chart-explainer`
- `~/.claude/skills/karthik-r-analysis-style`
- `~/.claude/skills/dataviz-fix`
- `~/.claude/skills/dataviz-eval`

To install without pulling:

```bash
./sync.sh --no-pull
```

To validate metadata without installing:

```bash
./sync.sh --no-pull --validate-only
```

To install one surface only:

```bash
./sync.sh --no-pull --surface codex
./sync.sh --no-pull --surface claude
```

## Run the local repair tester

The local tester exercises the bounded case state machine before provider APIs are connected. It accepts a pasted or uploaded chart, records versioned context, explicit preservation requirements, and structured feedback, enforces iteration and cost limits, preserves original/current/best artifacts, and exposes the case history. Narrow repairs are treated as edit boundaries rather than invitations to redesign the chart. Candidate charts can be uploaded manually or generated through an opt-in local Codex runner.

```bash
python3 -m pip install -r tester/requirements.txt
uvicorn tester.app:app --host 127.0.0.1 --port 8787 --reload
```

Open `http://127.0.0.1:8787`. This development server has no authentication. Keep it on localhost.

Set `DATAVIZ_ENABLE_LOCAL_RUNNER=1` before starting the server to enable one bounded local creator-plus-reviewer cycle per click.

See [`tester/README.md`](tester/README.md) and the [`repair-loop product roadmap`](docs/plans/dataviz-repair-product-roadmap.md).

## MCP tools and current coverage

The metadata-first MCP server exposes deterministic chart rendering, exact-artifact geometry inspection, and revision comparison. It leaves analytical and visual judgement in the skills.

The server exposes five tools: `probe_renderers`, `render_and_inspect_chart`, the backward-compatible Matplotlib-only `render_chart`, `inspect_rendered_chart`, and `compare_chart_artifacts`. The backend-neutral workflow produces a PNG, chart spec, layout metadata, inspection, review views, and a hash-bound manifest. Comparison remains mechanical and does not make a subjective release decision.

See [`docs/mcp.md`](docs/mcp.md) for the architecture, exact-artifact workflow, version guarantees, inspection coverage, and tested repair sequence. See [`dataviz_mcp/README.md`](dataviz_mcp/README.md) for installation, client registration, tool parameters, the chart-builder contract, and the local security boundary.

## Trust and limitations

- Rendering executes trusted local Python or R. It is not a sandbox; do not use it on untrusted chart source.
- Matplotlib geometry covers text, lines, bars, patches, and common collections. The ggplot2 adapter resolves drawn gtable tracks and captures every panel plus rect, point, polygon, polyline, and text grobs; uncommon grobs remain explicit limitations.
- Mechanical inspection does not replace analytical critique, delivery-size visual review, or user acceptance.
- Local/private `references/` and `scripts/` remain ignored by default. Public runtime files required by a skill, such as `dataviz-fix/scripts/case_manager.py`, are tracked.

## Development notes

- [`AGENTS.md`](AGENTS.md) contains the maintainer-only validation and publish rule. It does not apply to third-party clones or forks.
- Source skills live in `<skill>/{codex,claude}/SKILL.md`.
- `sync-skills.py` discovers every root-level directory containing both surface files.
- `sync-skills.py --validate-only` checks frontmatter without copying files.
- Repair-loop changes are covered by `dataviz-fix/tests/` and `tester/tests/`.
- No generated `dist/` output is committed.
- Keep README files in public folders. They are navigation aids for newcomers and should be updated when layout changes.

## Session notes and writeups

- [`CHANGELOG.md`](CHANGELOG.md) - release-style summary of public repo changes.
- [`DEVLOG.md`](DEVLOG.md) - session notes with prompts and work done.
- [`docs/blog/building-the-dataviz-selector-skill.md`](docs/blog/building-the-dataviz-selector-skill.md)

## License

MIT.

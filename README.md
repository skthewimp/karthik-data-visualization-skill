# Karthik Data Visualization Skills

Public data visualization skills for Codex, Claude, and Hermes.

This repo contains thirteen related skills:

1. **`dataviz-fix`** - iterative repair and learning-loop rules: rebuild a pasted chart, require an independent artifact-hashed review, preserve revisions and feedback, then route reusable lessons to the owning skill.
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

The split is deliberate. The repair-loop skill answers **"rebuild this chart, keep revising it with me, then learn from what I corrected"**. The evaluation skill answers **"does the audience recover the intended question and insight, is the artifact ready to send, and is the creator system improving?"**. The data-cleaning skill answers **"how do we make this source analysable without hiding judgement calls?"**. The question generator answers **"what is worth asking of this raw dataset?"**. The orchestrator answers **"take this from dataset to visual story"**. One skill answers **"what chart should I use?"**. Another answers **"how should this chart look once I have chosen it?"**. The critique skill answers **"what is wrong with this chart, how should it improve, and what alternatives would work better?"**. The PowerPoint skill answers **"how should this analysis become slides?"**. The analysis planner answers **"what exactly are we measuring, against what denominator, and what would falsify the claim?"**. The annotation skill answers **"what should this chart mark, and what should the mark say?"**. The explainer skill answers **"what do I write next to this chart so the reader knows what it says?"**. The R analysis skill answers **"how should the notebook doing all of this be written?"**.

## Repository layout

```text
.
├── dataviz-fix/                     # Iterative chart repair, feedback capture, and skill learning
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
├── docs/                            # Human docs; subfolder READMEs explain contents
├── sync-skills.py                   # Install Codex/Claude or the explicit Hermes surface
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

The skill chooses the chart form and explains the encoding. It also has hard guardrails against bad defaults: no pie charts, donut charts, 3D charts, animated charts, interactive charts as the core recommendation, gauges, radar/spider charts, or decorative infographic forms.

See: [`docs/skills/dataviz-selector.md`](docs/skills/dataviz-selector.md)

### `karthik-data-visualization`

Use this after chart selection, when generating or reviewing the visual itself. It covers typography, colours, direct labels, gridlines, axes, annotations, facets, chart density, and export defaults.

See: [`docs/skills/karthik-data-visualization.md`](docs/skills/karthik-data-visualization.md)

### `dataviz-critique`

Use this when you have an existing visual and context such as the intended story, data, audience, or decision, and you want to know what works, what fails, how to improve it, and what 2-3 alternative visualizations would work better.

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

Use this when a chart or table is finished and someone else has to be told what it says - two lines above a graph in an email, a note per figure in an exploratory notebook, or a line carrying a screenshot into a chat. It enforces a claim with an anchored number plus one payoff, computes numbers from the data rather than reading them off the image, and treats "nothing here" as a legitimate answer instead of manufacturing a finding.

See: [`docs/skills/chart-explainer.md`](docs/skills/chart-explainer.md)


### `karthik-r-analysis-style`

Use this when writing the R analysis itself - an exploratory scratchpad, an RMarkdown or Quarto notebook, a first pass at a dataset that just landed. It covers notebook shape, probe sequencing, the rough working-note register, tidyverse/tidytable defaults, and routing to dbplyr, Arrow, or DuckDB when the data will not sit in memory. It requires an after-plot note on every plot and delegates the wording to `chart-explainer`.

See: [`docs/skills/karthik-r-analysis-style.md`](docs/skills/karthik-r-analysis-style.md)

## Install locally

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
./sync.sh --no-pull --surface hermes
```

The Hermes surface installs the Claude-compatible copies under `~/.hermes/skills/data-science/`. It is explicit rather than part of `all`.

## Run the local repair tester

The local tester exercises the bounded case state machine before provider APIs are connected. It accepts a pasted or uploaded chart, records versioned context and structured feedback, enforces iteration and cost limits, preserves original/current/best artifacts, and exposes the case history. Candidate charts can be uploaded manually or generated through an opt-in local Codex runner.

```bash
python3 -m pip install -r tester/requirements.txt
uvicorn tester.app:app --host 127.0.0.1 --port 8787 --reload
```

Open `http://127.0.0.1:8787`. This development server has no authentication. Keep it on localhost.

Set `DATAVIZ_ENABLE_LOCAL_RUNNER=1` before starting the server to enable one bounded local creator-plus-reviewer cycle per click.

See [`tester/README.md`](tester/README.md) and the [`repair-loop product roadmap`](docs/plans/dataviz-repair-product-roadmap.md).

## Validation and red-team prompts

The selector skill includes:

- Local/private `references/` and `scripts/` remain ignored by default. Runtime files explicitly required by public skills, such as `dataviz-fix/scripts/case_manager.py`, are tracked.

## Development notes

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

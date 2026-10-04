# Karthik Data Visualization Skills

Skills for Claude Code and Codex that make charts, tables and data stories the way I make them: one claim per chart, direct labels instead of legends, colour only where it means something, no chart furniture that isn't earning its keep, and a render-and-look check before anything is called done.

There is an optional local MCP server that renders charts and measures the exported image (clipping, overlaps, text size, contrast), and computes colour palettes and rounding. The skills work without it; the server makes the mechanical checks exact instead of eyeballed.

## Start here

Pick the entry point that matches what you have.

| You have | Ask your agent to use | What happens |
|---|---|---|
| Data and a chart in mind | `karthik-data-visualization` | Builds the chart in the house style, renders it, and checks the export. Pulls in `dataviz-selector` if the form isn't settled. |
| An existing chart (image or code) that isn't working | `dataviz-construct` | Recovers the message and the data, picks a form fresh, rebuilds, and returns a real image. |
| A dataset and a loose question | `dataviz-construct` | Finds the story, pins down the metric and denominator, cleans the data, then builds the chart. |
| A chart someone else made | `dataviz-critique` | Says what works, what misleads, and what to change. |
| A table to format | `karthik-table-style` | Alignment, rounding, emphasis and in-cell bars or shading. |

For a single chart, `karthik-data-visualization` on its own is the whole thing. The staged pipeline below is what `dataviz-construct` runs when the job is bigger than one chart, or when you want each step checked by a separate call.

Install in two commands (details in [Quick start](#quick-start)):

```bash
git clone https://github.com/skthewimp/karthik-data-visualization-skill.git
cd karthik-data-visualization-skill && ./sync.sh --no-pull --surface claude   # or: --surface codex
```

R with `ggplot2` and `ragg` is the preferred renderer. Python and Matplotlib work as a fallback, but only with the typography, palette and spacing set deliberately; default Matplotlib output fails these skills.

## How the pieces fit

`dataviz-construct` runs both creation and repair. They have different front halves and share one back half:

```text
dataset -> discover -> contract -> clean ─┐
                                          ├─> insight -> select -> idea -> build -> execution
chart image -> diagnose + extract ────────┘
```

- **insight** computes the facts and names the one headline claim before any form is chosen.
- **select** picks the simplest form that makes that claim hard to misread (a well-formatted table counts).
- **idea** checks the plan before anything is drawn: right data, right form, honest claim.
- **build** draws it in the house style.
- **execution** looks at the exported image for defects and composition in one review, fixes them in one revision, and verifies.

Each stage loads only its own skill, so no call carries all twenty.

## Skill map

**Start points**
- [`karthik-data-visualization`](docs/skills/karthik-data-visualization.md) - chart craft: typography, direct labels, colour, axes, whitespace, export check.
- [`dataviz-construct`](docs/skills/dataviz-construct.md) - the staged pipeline: dataset to visual story, or repair an existing chart by forward design.
- [`dataviz-critique`](docs/skills/dataviz-critique.md) - standalone chart critique, and the repair brief that opens a rebuild.

**Choosing and checking**
- [`dataviz-selector`](docs/skills/dataviz-selector.md) - which form fits the claim, including when a table beats a chart.
- [`karthik-evidence-builder`](docs/skills/karthik-evidence-builder.md) - facts and headline claim.
- [`dataviz-idea-critique`](docs/skills/dataviz-idea-critique.md) - the pre-render gate.
- [`dataviz-execution`](docs/skills/dataviz-execution.md) - the post-render gate: defects and composition, reviewed together.
- [`dataviz-eval`](docs/skills/dataviz-eval.md) - formal blind review and benchmarks. Only when you need an audit; it slows ordinary work down.

**Craft details**
- [`dataviz-color`](docs/skills/dataviz-color.md) - choose and assign colours for this chart; brand first, then accessibility.
- [`dataviz-precision`](docs/skills/dataviz-precision.md) - how many digits to show, set by the spread of the numbers.
- [`chart-annotations`](docs/skills/chart-annotations.md) - annotate only with facts from outside the data; word and place labels.
- [`chart-explainer`](docs/skills/chart-explainer.md) - the two lines that travel with a chart in an email or notebook.
- [`karthik-table-style`](docs/skills/karthik-table-style.md) - tables as visualizations.
- [`karthik-powerpoint-style`](docs/skills/karthik-powerpoint-style.md) - claim-first, sparse analytical slides.

**Repair internals**
- [`dataviz-extract`](docs/skills/dataviz-extract.md) - read the full data table out of a chart image.

**Before the chart**
- [`dataset-question-generator`](docs/skills/dataset-question-generator.md) - good questions from a raw dataset.
- [`karthik-analysis-planner`](docs/skills/karthik-analysis-planner.md) - turn a fuzzy question into metric, denominator, comparison and falsifiers.
- [`karthik-data-cleaning`](docs/skills/karthik-data-cleaning.md) - inspect, clean in context, inspect again.

**R style**
- [`karthik-r-analysis-style`](docs/skills/karthik-r-analysis-style.md) - how an exploratory R notebook is written.
- [`karthik-r-code-style`](docs/skills/karthik-r-code-style.md) - how R code is laid out.

## Repository layout

```text
.
├── <skill>/{codex,claude}/SKILL.md   # 20 skills, one folder each, a SKILL.md per client
├── dataviz_mcp/                      # Optional local stdio MCP: render, inspect, refit, colour, precision
├── docs/                             # Human docs, one page per skill
├── sync-skills.py                    # Install Codex or Claude skill surfaces
└── sync.sh                           # Pull + install wrapper
```

Every public folder has a README. No generated `dist/` tree is committed.

## Quick start

Clone the repository and choose the skill surface for your client:

```bash
git clone https://github.com/skthewimp/karthik-data-visualization-skill.git
cd karthik-data-visualization-skill

./sync.sh --no-pull --surface codex   # Codex
# or
./sync.sh --no-pull --surface claude  # Claude Code
```

Install the MCP package into your existing Python environment:

```bash
python3 -m pip install -e .
MCP_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
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

This pulls latest changes and installs every skill to `~/.codex/skills/<skill>` and `~/.claude/skills/<skill>`.

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

## MCP tools and current coverage

The MCP server is optional. The skills work without it; the tools make the mechanical checks exact instead of eyeballed. Analytical and visual judgement stays in the skills.

It exposes twelve tools:

| group | tools |
|---|---|
| render and inspect | `render_and_inspect_chart`, `inspect_rendered_chart`, `refit_chart`, `probe_renderers` |
| colour | `recommend_colours`, `validate_palette`, `extract_palette_from_image`, `recommend_continuous_scale`, `validate_scale` |
| numbers and scales | `recommend_precision`, `recommend_scale_transform` |
| reading a chart image | `read_marks_from_anchors` |

R is optional. Automatic rendering prefers ggplot2 when `Rscript`, `ggplot2` and `ragg` are installed, and falls back to Matplotlib otherwise; existing R code is not translated. R build errors are reported, never silently retried in Python. The render workflow produces a PNG, chart spec, layout metadata, inspection report, review views, and a hash-bound manifest. `refit_chart` grows the canvas in code until clipping, overflow and squashed panels clear, so no model turn is spent on that arithmetic.

See [`docs/mcp.md`](docs/mcp.md) for the architecture, exact-artifact workflow, version guarantees, inspection coverage, and tested repair sequence. See [`dataviz_mcp/README.md`](dataviz_mcp/README.md) for installation, client registration, tool parameters, the chart-builder contract, and the local security boundary.

## Trust and limitations

- Rendering executes trusted local Python or R. It is not a sandbox; do not use it on untrusted chart source.
- Matplotlib geometry covers text, lines, bars, patches, and common collections. The ggplot2 adapter resolves drawn gtable tracks and captures every panel plus rect, point, polygon, polyline, and text grobs; uncommon grobs remain explicit limitations.
- Mechanical inspection does not replace analytical critique, delivery-size visual review, or user acceptance.

## Development notes

- [`AGENTS.md`](AGENTS.md) contains the maintainer-only validation and publish rule. It does not apply to third-party clones or forks.
- Source skills live in `<skill>/{codex,claude}/SKILL.md`.
- `sync-skills.py` discovers every root-level directory containing both surface files.
- `sync-skills.py --validate-only` checks frontmatter without copying files.
- For a localized fix, run the affected test files, optionally narrowed with `-k`:
  `python3 -m pytest -q dataviz_mcp/tests/test_scales.py`. Prose-only edits need metadata
  validation, not rendering tests. See [AGENTS.md](AGENTS.md) for check selection.
- `python3 -m pytest -q` runs the full core MCP suite, including live renders; reserve it for
  cross-cutting changes. Add `--durations=10` to locate slow tests. R availability is checked
  lazily once per test session for integration-test prerequisites.
- For quick feedback, use `python3 -m pytest -q -m 'not integration'`; add an affected file
  before `-m` to narrow it further. `-m integration` selects live chart renders and renderer
  probes. The default command still runs both groups.
- Extend an existing test when it already builds the same scenario. Keep separate cases for
  distinct failure modes and renderer behavior; avoid duplicate renders, wording snapshots,
  and tests that merely repeat implementation constants.
- No generated `dist/` output is committed.
- Keep README files in public folders. They are navigation aids for newcomers and should be updated when layout changes.

## Session notes and writeups

- [`CHANGELOG.md`](CHANGELOG.md) - release-style summary of public repo changes.
- [`DEVLOG.md`](DEVLOG.md) - session notes with prompts and work done.
- [`docs/blog/building-the-dataviz-selector-skill.md`](docs/blog/building-the-dataviz-selector-skill.md)

## License

MIT.

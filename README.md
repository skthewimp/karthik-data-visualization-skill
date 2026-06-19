# Karthik Data Visualization Skills

Public data visualization skills for Codex and Claude.

This repo contains two related skills:

1. **`karthik-data-visualization`** - style rules for producing charts in Karthik's preferred visual language: low chartjunk, direct labels, careful typography, meaningful colour, and Tufte-inspired restraint.
2. **`dataviz-selector`** - chart-selection rules for deciding what kind of visualization fits a dataset plus question, hypothesis, or data story.

The split is deliberate. One skill answers **"what chart should I use?"**. The other answers **"how should this chart look once I have chosen it?"**.

## Repository layout

```text
.
├── karthik-data-visualization/      # Chart styling skill
├── dataviz-selector/                # Chart selection skill
├── docs/                            # Human docs and writeups
├── dist/
│   ├── codex/                       # Built Codex-ready skill copies
│   ├── claude/                      # Built Claude-ready skill copies
│   └── claude-zips/                 # Claude import ZIPs
├── sync-skills.py                   # Build + install script
└── sync.sh                          # Pull + build + install wrapper
```

## Skills

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

## Install locally

```bash
./sync.sh
```

This pulls latest changes, builds the Codex and Claude copies, and installs both skills to:

- `~/.codex/skills/karthik-data-visualization`
- `~/.codex/skills/dataviz-selector`
- `~/.claude/skills/karthik-data-visualization`
- `~/.claude/skills/dataviz-selector`

To build and install without pulling:

```bash
./sync.sh --no-pull
```

## Build outputs

Running `./sync.sh --no-pull` rebuilds:

- `dist/codex/`
- `dist/claude/`
- `dist/claude-zips/`

The Claude ZIPs are intended for sharing/import:

- `dist/claude-zips/karthik-data-visualization.zip`
- `dist/claude-zips/dataviz-selector.zip`

## Validation and red-team prompts

The selector skill includes:

- Local-only `references/` and `scripts/` helpers may exist for development, but are ignored and not committed to the public repo.

## Development notes

- Source skills live at repo root.
- `sync-skills.py` discovers every root-level directory containing `SKILL.md`.
- The script writes Codex copies as-is.
- For Claude copies, it rewrites frontmatter to use the short Claude-safe description from `metadata.claude-description` when present.
- Avoid putting extra README files inside skill directories unless they are meant to ship as skill resources. Human documentation belongs in `docs/`.

## Session notes and writeups

- [`DEVLOG.md`](DEVLOG.md)
- [`docs/blog/building-the-dataviz-selector-skill.md`](docs/blog/building-the-dataviz-selector-skill.md)

## License

MIT.

# Karthik Data Visualization Skills

Public data visualization skills for Codex and Claude.

This repo contains three related skills:

1. **`dataviz-selector`** - chart-selection rules for deciding what kind of visualization fits a dataset plus question, hypothesis, or data story.
2. **`karthik-data-visualization`** - style rules for producing charts in Karthik's preferred visual language: low chartjunk, direct labels, careful typography, meaningful colour, and Tufte-inspired restraint.
3. **`karthik-powerpoint-style`** - slide and deck rules for making PowerPoint-style presentations in Karthik's analytical, claim-first style.

The split is deliberate. One skill answers **"what chart should I use?"**. Another answers **"how should this chart look once I have chosen it?"**. The PowerPoint skill answers **"how should this analysis become slides?"**.

## Repository layout

```text
.
├── dataviz-selector/                # Chart-selection skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-data-visualization/      # Chart-style skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── karthik-powerpoint-style/        # Presentation-slide skill; folder README explains layout
│   ├── codex/SKILL.md
│   └── claude/SKILL.md
├── docs/                            # Human docs; subfolder READMEs explain contents
├── sync-skills.py                   # Install both surfaces locally
└── sync.sh                          # Pull + install wrapper
```

Each skill owns its Codex and Claude versions directly. Every public folder has a README so newcomers can navigate without prior context. No generated `dist/` tree is committed.

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

### `karthik-powerpoint-style`

Use this when turning analysis into PowerPoint-style slides or deck outlines. It covers claim-first titles, slide layout, chart placement, annotation, source notes, typography, colour, and what to avoid in management presentations.

See: [`docs/skills/karthik-powerpoint-style.md`](docs/skills/karthik-powerpoint-style.md)

## Install locally

```bash
./sync.sh
```

This pulls latest changes and installs all skills to:

- `~/.codex/skills/karthik-data-visualization`
- `~/.codex/skills/dataviz-selector`
- `~/.codex/skills/karthik-powerpoint-style`
- `~/.claude/skills/karthik-data-visualization`
- `~/.claude/skills/dataviz-selector`
- `~/.claude/skills/karthik-powerpoint-style`

To install without pulling:

```bash
./sync.sh --no-pull
```

## Validation and red-team prompts

The selector skill includes:

- Local-only `references/` and `scripts/` helpers may exist for development, but are ignored and not committed to the public repo.

## Development notes

- Source skills live in `<skill>/{codex,claude}/SKILL.md`.
- `sync-skills.py` discovers every root-level directory containing both surface files.
- No generated `dist/` output is committed.
- Keep README files in public folders. They are navigation aids for newcomers and should be updated when layout changes.

## Session notes and writeups

- [`DEVLOG.md`](DEVLOG.md)
- [`docs/blog/building-the-dataviz-selector-skill.md`](docs/blog/building-the-dataviz-selector-skill.md)

## License

MIT.

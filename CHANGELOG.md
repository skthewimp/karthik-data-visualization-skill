# Changelog

All notable public changes to this repository are recorded here.

## 2026-07-03

### Added

- Added `dataset-question-generator` as a public Codex/Claude skill for profiling raw datasets and producing fresh, visualisable analysis questions before planning or charting.
- Added human-facing docs and repository navigation entries for the new skill.

## 2026-06-30

### Added

- Added `karthik-analysis-planner` as a public Codex/Claude skill for turning natural-language data questions into analysis contracts before coding, charting, or prose.
- Added human-facing docs for the analysis planner and updated repository indexes/install notes.

## 2026-06-25

### Added

- Added `CHANGELOG.md` to separate release-style repository changes from the session-oriented `DEVLOG.md`.
- Expanded the human-facing documentation for `dataviz-critique` with usage examples, input expectations, output contract, redesign alternative types, and how it differs from the other visualization skills.

### Changed

- Extended `dataviz-critique` from a critique-only skill into a critique-plus-redesign skill: after diagnosing a visual, it now proposes two or three better visualization alternatives when useful.
- Updated the Codex and Claude versions of `dataviz-critique` so alternatives are not random chart suggestions; each option must have a distinct analytical purpose, audience use, or intervention level.

## 2026-06-24

### Added

- Added `dataviz-critique` as a fourth public skill, with Codex and Claude skill files.
- Added `dataviz-critique/README.md` and `docs/skills/dataviz-critique.md`.
- Added `karthik-powerpoint-style` as a public presentation-slide skill.

### Changed

- Updated the root README and docs index to explain the four-skill structure.
- Fixed YAML quoting in `karthik-powerpoint-style` frontmatter so repository validation passes cleanly.

## 2026-06-19

### Added

- Added `dataviz-selector`, a chart-selection skill for choosing visualization forms from a dataset plus analytical question, hypothesis, or story.
- Added multi-skill sync/validation support through `sync-skills.py` and `sync.sh`.
- Added initial repository documentation and public skill docs.

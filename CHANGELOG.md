# Changelog

All notable public changes to this repository are recorded here.

## 2026-08-03

### Added

- Added `chart-annotations` as a public Codex/Claude skill for deciding what a chart should mark, ranking competing annotation candidates, wording the label, and placing it.
- Added human-facing docs and repository navigation entries for the new skill.

### Changed

- Updated `dataviz-orchestrator` to call `chart-annotations` at the charting step, alongside `karthik-data-visualization`.
- Revised `chart-annotations` after testing it on three real charts. Added: derive annotation coordinates from the data instead of hand-typing them; a "when nothing clears the bar" section establishing that no story means no annotation, with the absence stated in the title and context layers distinguished from annotations; a higher bar for derived features such as scanned breakpoints and fitted slopes; the concentration check now gates the title as well as the annotation; orienting labels treated as a separate class outside the annotation cap; and axis headroom reserved for label text before rendering.
- Revised `chart-annotations` again after a second round of testing on three fresh charts. Added: numbers and comparative words in labels must be computed rather than typed; split points chosen by eye are derived features and need the same validation as scanned ones; derived coordinates must be offset into whitespace, since a cluster centroid is the worst available position; title and annotation must make the same claim; contrast pairs count as one annotation and share weight; and label headroom applies to every panel edge, not only the right.

## 2026-07-19

### Changed

- Reworked `karthik-powerpoint-style` title guidance: slide titles are plain claims, concept labels, or direct questions - not crafted aphorisms or "X, not Y" one-liners. Added a "Slide titles" section with good and banned examples, and softened the old "make the title an analytical claim, not a topic label" step that pushed toward crafted headlines.
- Added a "Slide bodies" section: bullets or one short line, 3-5 points, no academic numbered procedures.
- Added "Start from Karthik's own material": reuse his decks/blogs verbatim and lift real images from `.pptx` `ppt/media/` rather than paraphrasing or re-creating them.
- Added a "Workshop / facilitator cue-card slide" pattern: during hands-on exercises the slide face carries only a plain title and a `time · artifact` anchor, with detail in facilitator notes.
- Updated `docs/skills/karthik-powerpoint-style.md` to match.

## 2026-07-03

### Added

- Added `dataset-question-generator` as a public Codex/Claude skill for profiling raw datasets and producing fresh, visualisable analysis questions before planning or charting.
- Added human-facing docs and repository navigation entries for the new skill.
- Added `karthik-data-cleaning` as a public Codex/Claude skill for context-sensitive tabular data preparation before analysis, modelling, and charting.
- Added missing Codex/Claude subfolder README files for newer skills.
- Expanded README coverage across skill folders, surface folders, docs folders, and public reference/script directories so the MIT repo is navigable from GitHub.

### Changed

- Updated `dataviz-orchestrator` so the full dataset-to-visual-story loop now explicitly includes contextual data inspection, cleaning, reshaping, joins, and validation.
- Updated `dataset-question-generator` and `karthik-analysis-planner` to hand off to `karthik-data-cleaning` when the raw source needs cleaning before the question or metric is trustworthy.
- Updated sync docs for metadata-only validation and single-surface installs.

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

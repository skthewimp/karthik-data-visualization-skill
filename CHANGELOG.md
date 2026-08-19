# Changelog

## Unreleased

### Platform separation

- Removed the client-specific release-guard plugin, installation surface, state paths, identity defaults, attachment syntax, deployment instructions, and host checks from this repository.
- Kept the reusable independent-review workflow, case state machine, Codex and Claude skill surfaces, and MCP server client-neutral.
- Moved the client adapter and host deployment workflow to the client repository that owns them.

### Repair reliability

- Replaced the default contract-and-review loop with an output-first repair path: build, inspect once, and deliver the best valid artifact even when MCP or independent review is unavailable.
- Removed default candidate, elapsed-time, and stalled-evaluation caps. Explicit user-supplied budgets remain available for audited runs.
- Aligned the packaged public repair contract with the skill: the default stage is now creator-only, while planning and independent review are explicitly optional.
- Narrowed the default test suite to core MCP behaviour and marked the case manager and local tester as explicitly audited tools rather than the normal repair route.
- Documented that `dataviz-eval` is a formal optional audit whose strict gates can block `Send` and create unnecessary loops when inserted into ordinary repair.
- Kept structured contracts, blind review, and case logging available for explicitly audited or high-risk work instead of imposing them on every repair.
- Kept honest status labels: unreviewed or partially inspected artifacts are delivered as such rather than being hidden or falsely approved.

### Workflow and skill generalization

- Reworked the visualization skill family around explicit ownership and handoffs: planning → cleaning → question generation → selection → construction → annotation → explanation → critique/repair → independent evaluation.
- Generalized chart-selection, annotation, explanation, and critique guidance so recommendations depend on the analytical question, evidence, audience, medium, density, accessibility, and delivery constraints.
- Removed example-specific and overfitted defaults, including fixed chart-type blacklists, mandatory annotation counts, fixed explanation lengths, named-domain assumptions, and universal legend or interaction rules.
- Added semantic checks for measure meaning, time boundaries, universe and denominator, units, claim strength, and likely reader interpretation.
- Kept Codex and Claude skill surfaces synchronized.

### Verification

- `./sync.sh --no-pull --validate-only`
- `./sync.sh --no-pull --surface claude`
- `./sync.sh --no-pull --surface codex`
- `git diff --check`
- `pytest -q dataviz-fix/tests` — 23 tests passed

All notable public changes to this repository are recorded here.

## 2026-08-15

### Added

- Added a local stdio MCP server with three mechanical capabilities: render a trusted Matplotlib builder into a versioned bundle, inspect the exact raster with renderer geometry, and compare two inspected revisions.
- Added layout metadata for plot bounds, text and annotation boxes, line paths, legends, and data-to-pixel transforms. Inspection reports clipping, canvas overflow, annotation collisions, annotation-series intersections, text margins, and long unwrapped labels.
- Added deterministic fixtures for each failure mode plus an end-to-end coffee-price annotation repair that fails its first inspection and passes after a placement-only revision.

### Changed

- Extended repair-loop cases to preserve render manifests, chart specs, layout metadata, and artifact-hashed inspection reports. Independent evaluations must reference the same inspection hash when one exists.
- Updated the local runner to attach inspection evidence before blind review. Metadata-aware builders receive complete geometry checks; raster-only candidates retain explicit unknowns.
- Added minimal orchestrator, evaluator, and fixer instructions requiring exact-artifact inspection without moving analytical or visual judgement into MCP.
- Documented the architectural boundary, hash/version flow, tool contracts, Codex and Claude Code setup, supported geometry, honest unknown states, repair sequence, and end-to-end test procedure.
- Tightened generation and repair after rebasing the MCP work onto the generalized skill stack: Matplotlib output now uses the metadata-producing renderer when available, and the explicit repair sequence records the bundle and inspection before blind review.
- Added state-machine enforcement so mismatched internal metadata is rejected and a reviewer cannot issue `Send` while known deterministic defects remain. Incomplete coverage can still be assessed visually but is never presented as a deterministic pass.
- Expanded the coffee regression through the real case state machine: bad geometry reaches `Revise`, the placement-only repair reaches `Send`, and the exact repaired artifact becomes current.
- Removed a client-only runtime assumption. Codex and Claude Code now resolve their own installed case-manager path, retain the returned case id, and use the same versioned workflow.
- Completed the test extra with the local tester's FastAPI dependencies so `pip install -e ".[test]"` can run the repository's configured full suite on a clean host.
- Clarified that the MCP renderer is a backend adapter rather than a style system. Project-native renderers are preserved, new Karthik-style static charts prefer R/ggplot2 when available, and metadata support cannot justify translating a sound chart into default-looking Matplotlib.
- Reworked the root README into an agent entry point with generation and repair reading paths, Codex/Claude installation, the two-part skills-plus-MCP setup, current renderer limits, security boundaries, and direct links to deeper contracts.
- Added repo-local Codex and Claude instructions for Karthik's default validate → commit → push workflow, with explicit safeguards for third-party clones, unrelated changes, test failures, and remote divergence.

## 2026-08-12

### Changed

- Converted concrete intake edits and preservation requirements into a structured change contract that the independent reviewer must test directly.
- Made narrow repairs scope-aware: changed regions face the full release standard, untouched regions are checked for preservation and regressions, and unchanged pre-existing defects outside scope are recorded separately instead of broadening the required edit.
- Added explicit user-over-evaluator precedence. Later feedback can supersede a conflicting carried evaluator action, and reviewers cannot retain or restore an element the user asked to remove.
- Added regression coverage for preservation checks, intake change checks, evaluator-action supersession, and local creator/reviewer scope instructions.
- Made shared-key replacement panel-complete: intake checks enumerate repeated instances, creators apply the edit across every applicable panel or facet, and reviewers count each expected replacement rather than passing the first complete panel.

## 2026-08-11

### Added

- Added a bounded repair state machine with explicit build, blind review, context reveal, revision, redesign, user review, blocked, stopped, and accepted states.
- Added versioned context for audience, purpose, question, hypothesis, message, medium, delivery conditions, source notes, preservation rules, accessibility, brand, tooling, and output constraints. Each value records whether it came from the user, an inference, or remains unknown.
- Added configurable iteration, elapsed-time, token, cost, and no-progress stops; original/current/best artifact preservation; structured feedback checks; and per-stage usage telemetry.
- Added a local FastAPI case console for chart upload, context changes, feedback, manual candidate comparison, budgets, stop/resume, and history.
- Added an opt-in local Codex runner that performs one ephemeral creator pass and one separate blind reviewer pass per click against the checked-out skills. It cannot start an open-ended autonomous loop.
- Added measured cycle-token estimates and preflight budget checks. Completed artifacts and reviews are still preserved when one provider call crosses its estimate.
- Added regression tests for loop termination, duplicate artifacts, changed context, reviewer sequencing, budgets, telemetry state, file validation, artifact delivery, and the tester API.
- Added the staged roadmap for local testing, private deployment, and a possible public bring-your-own-key beta.

### Changed

- Changed the repair loop so an unchanged artifact cannot trigger another evaluation under the same context, repeated failures pause for human input, and every stop retains a useful next candidate.
- Changed user corrections from loose prompts into observable acceptance checks while preserving the original wording.
- Changed the local runner so the wrapper, rather than either model, records candidate and verdict transitions. This keeps telemetry attached before the transition and prevents the agents from advancing extra states.
- Tightened `dataviz-eval` after an accepted live repair: quantitative axes, ticks, gridlines, baselines, and reference lines must each perform distinct reading work. Direct values do not automatically ban a scale, but redundant default scaffolding can no longer pass as neutral decoration.

## 2026-08-10

### Added

- Added `dataviz-fix` as a public Codex/Claude skill for repairing pasted charts through repeated user feedback, preserving every revision, and routing reusable lessons back to the owning skill.
- Added `case_manager.py` to keep the original chart, revisions, feedback, accepted artifact, skill hashes, and post-acceptance diagnosis together as one case packet.
- Added `dataviz-eval` as a public Codex/Claude skill for deciding whether a rendered chart is ready to send or needs another inspect→revise cycle. It captures the repeated failure modes we kept seeing in chart repair: clipping, overlap, whitespace imbalance, export-vs-viewport mismatches, and thumbnail/chat legibility.
- Added human-facing docs for `dataviz-eval` and surfaced it in the documentation index.

### Changed

- Rebuilt `dataviz-eval` from a render-readiness checklist into a full artifact and creator-system evaluation framework. It now uses expert and audience blind reads, hard gates for evidence and intended meaning, `Send / Revise / Redesign / Not evaluable` verdicts, concrete chart-spec operations, a reusable failure taxonomy, and golden-set regression guidance.
- Added repair-session calibration cases and documented the framework's debt to Vikram Nayak's Fifth Elephant 2026 talk, *Measuring “good” when your agent's output is subjective*.
- Integrated the rebuilt evaluator into the full `dataviz-fix` pipeline. Every rendered iteration now receives a recorded evaluation scope, six gate results, verdict, failure codes, and minimum pass set before it is sent or revised.
- Tightened the repair pipeline after the first live run: media attachments are now mandatory, HTML cannot masquerade as the delivered artifact, every iteration must be evaluated, requested edits receive literal element checks, legend-to-mark colour mappings are verified, and skills cannot be edited before chart acceptance.
- Added stacked-form and colour rules from the same live case, then generalized them: precise component patterns require aligned baselines, direct labels support lookup rather than visual comparison, and every essential colour must remain perceptually distinct from its background and neighbouring encodings.
- Expanded the colour rules into a Tufte-compatible system: colour must have an analytical role, scale types must match the data, focal saturation must follow information hierarchy, mappings must remain stable, key distinctions need a second channel, and practical WCAG targets guide text and small-mark contrast without mechanically constraining large fills.
- Fixed `dataviz-fix` packaging so the referenced `case_manager.py` runtime ships in fresh clones and client installs. Validation now rejects missing or git-ignored referenced scripts.
- Updated root and skill-documentation indexes for the full thirteen-skill set.
- Updated `dataviz-fix` so the inspection step is explicit about the inspect→revise→render loop, and so the companion-skill list now includes `dataviz-eval` as the dedicated evaluation gate.
- Updated `karthik-data-visualization` and `dataviz-selector` to carry the latest non-overlap, geometry-first, and thumbnail-first guidance that came out of the repair loop.
- Separated chart creation from release review after a live repair loop self-approved three visibly broken exports. The workflow now sends each recorded artifact to a fresh independent reviewer, and `case_manager.py` accepts only a structured report tied to the artifact hash.
- Added five general release checks—visual integrity, relationship traceability, spatial economy, encoding semantics, and delivery robustness. These are chart-agnostic outcomes, not hard-coded layouts, palettes, margin thresholds, or fixes for one example.
- Changed the colour default from “always create one focal item” to neutral equal-status marks unless the question, evidence, or user establishes a focal item.

## 2026-08-03

### Added

- Added `chart-explainer` as a public Codex/Claude skill for writing the two-line note that travels with a finished chart or table into an email, notebook, or message. Enforces a claim with an anchored number plus one payoff, requires numbers to be computed from the data rather than read off the image, treats "nothing here" as a legitimate output, and refuses to smooth a batch of exploratory plots into a narrative. Ships a calibration example bank mined from Karthik's Mint columns and analysis notebooks. Also fires on requests to build an exploratory notebook, where the two-line notes go in markdown under every plot chunk as part of the deliverable.
- Added `chart-annotations` as a public Codex/Claude skill for deciding what a chart should mark, ranking competing annotation candidates, wording the label, and placing it.
- Added `karthik-r-analysis-style` to the repo as a public Codex/Claude skill. It previously existed only as installed files under `~/.claude/skills` and `~/.codex/skills`, with no source copy, so it could not be reviewed or versioned with the rest. Its `references/` folder ships inside each surface directory because the skill reads those files at runtime.
- Added human-facing docs and repository navigation entries for the new skills.

### Changed

- Cross-referenced `chart-explainer` from `karthik-r-analysis-style`, so a request to build an exploratory notebook produces an after-plot note under every plot. The existing note examples in that skill were all lead-ins; nothing covered what a plot turned out to show.
- Mirrored the live Claude description into `metadata.claude-description` on the Codex side for `chart-annotations`, `dataviz-orchestrator`, `dataviz-selector`, and `karthik-data-cleaning`, where the two had drifted apart. Documentation-only; no behaviour change.
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
- Added `karthik-r-analysis-style` to the repo as a public Codex/Claude skill. It previously existed only as installed files under `~/.claude/skills` and `~/.codex/skills`, with no source copy, so it could not be reviewed or versioned with the rest. Its `references/` folder ships inside each surface directory because the skill reads those files at runtime.
- Added human-facing docs and repository navigation entries for the new skills.
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

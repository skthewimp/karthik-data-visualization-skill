# Changelog

## Unreleased

### Repair flow restructured to forward design

- Restructured the `dataviz-fix` repair flow so it no longer starts by critiquing the source chart. Critique-first anchored every repair on the existing image, so the path of least resistance was always "re-render the source form, tidied" - which failed a many-series stacked chart three times in a row (dropped the categories, dropped them with a justification, then kept them but re-rendered the same stack). Prose guardrails could not overcome the ordering, so the fix is structural: extract intent and data first, then choose the form cold with the source form removed from the room.
- New order: (1) INTENT via `dataviz-brief`, (2) DATA via `dataviz-extract` in parallel, (3) SELECT via `dataviz-selector` run cold on intent+data, (4) BUILD, (5) CRITIQUE as a downstream checker, (6) one blind `dataviz-eval` subagent. The one-chat/one-spawn economics and the two-pass checker cap are unchanged.
- Added `dataviz-brief`: a new skill that opens a repair by extracting the intent - key messages and required content, explicit drops (in message terms), audience and medium, story, authoritative prompt constraints, thin keep-notes, and an explicit `bounded-edit` vs `redesign` mode. It now owns "preserve the message, not the form" for the repair. The edit-vs-redesign fork lives in its output: a bounded literal edit stays anchored to the source form and skips selection; everything else, and the default when unsure, reopens the form.
- Added `dataviz-extract`: a new vision skill that reads the full period-by-category table (a value for every period and every category/series/stack) out of the source image, so any chosen form can be built from data rather than traced from the picture. Difficulty of reading a value is never grounds to drop the category it belongs to.
- Promoted `dataviz-selector` to the forward-design engine at step 3, run cold: the source chart's form is not an input and gets no vote, and there is no "unless the source form is clearly correct" escape hatch in the redesign path. A many-series stack whose message is per-series comparison becomes small multiples or direct-labelled lines on the selector's own reasoning.
- Reduced `dataviz-critique` in the repair path to a downstream checker (step 5): it verifies the built candidate carries the brief's intent and is a good chart (mechanical + semantic), without re-deriving the key messages or reopening the form choice unless a message genuinely fails. Its standalone "what's wrong with this chart?" use is unchanged, and it keeps the key-messages reasoning for that path.
- Both new skills ship both surfaces (`codex` and `claude`, byte-identical). Rewrote `docs/design/dataviz-fix-repair-flow.md` for the new flow and added `docs/skills/dataviz-brief.md` and `docs/skills/dataviz-extract.md`; updated the skill docs, folder READMEs, and root README.
- De-overfit pass on the behavior files: removed the literal `a16z` / "ten models" / "model mix" references from `dataviz-brief`, `dataviz-extract`, and `dataviz-critique`, generalising them to N-series / multi-category language, and added non-stack examples (dual-axis, map-for-ranking, over-fine pie) so "preserving the message is not preserving the form" reads as a general principle rather than a stacked-bar rule. The a16z case history stays in DEVLOG and the design note, where it belongs.

### Chart-selection and reconstruction-honesty principles

- Added the Cleveland-McGill / Tufte channel-ranking principle to `dataviz-selector`: encode magnitude on the strongest channel the layout allows - position and length before angle, area, or colour lightness/saturation. Colour lightness answers "where are the hot and cold cells", never "how much" or "which way is it moving". Added the heatmap application (a category-by-time heatmap is a poor default for value or trajectory comparison, worse on a log colour scale; reserve it for presence/timing/gap/block patterns across many cells that position cannot lay out - otherwise small multiples, direct-labelled lines, or a ranked view, reducing to top-N plus "other" if crowded). This is a general encoding principle, not a chart-specific rule. Prompted by a repair that correctly abandoned the source stack but chose a log-colour heatmap for the per-model trajectories.
- Dialled back the "values are approximate" signalling across `dataviz-extract`, `dataviz-fix`, `dataviz-brief`, `dataviz-critique`, and `chart-explainer`. Reconstructing a chart from an image is self-evidently approximate; announcing it on the chart or repeating it through the brief adds no information. Kept the real rule - never fabricate precision (no unsupported digits, no rounding toward rounder-sounding numbers) - and removed the mandates to label every screenshot-derived value "approximate" and to stamp approximate-disclaimers as chart furniture. At most one plain source line, only where the medium expects one.

### Platform separation

- Made the public creator contract discover every top-level `<skill>/codex/SKILL.md` and assemble itself from the current repository without a per-skill allowlist. It exposes the core Git revision, discovered paths, fingerprint, and an explicit single-creator adapter. Editable public-site deployments now pick up added, renamed, removed, or revised skills after their normal restart instead of silently retaining an older handwritten prompt.
- Removed the embedded handwritten public-creator fallback. The contract now fails closed when the canonical repository skills are unavailable.
- Removed the client-specific release-guard plugin, installation surface, state paths, identity defaults, attachment syntax, deployment instructions, and host checks from this repository.
- Kept the reusable independent-review workflow, case state machine, Codex and Claude skill surfaces, and MCP server client-neutral.
- Moved the client adapter and host deployment workflow to the client repository that owns them.

### Repair flow redesign

- Rebuilt the `dataviz-fix` default flow around one chat and one spawn: a single-pass source critique and an in-context checker loop (capped at two passes) run in the current session, and exactly one blind `dataviz-eval` subagent runs once on the converged candidate. This removes the slow, unbounded independent-review loop while restoring a real blind read at bounded cost.
- Made the input image non-sacred but the prompt authoritative: reconstruction may redesign freely against the image and biases toward redesign, while every prompt instruction (chart type, annotations, what to fix, wording, style) must survive the process.
- Wired `dataviz-selector` (default-on unless the form is clearly correct) and `chart-annotations` into the reconstruction step; the annotation skill had been dropped from the flow. Annotation is a judgment call - the skill is invoked and decides whether any mark clears the bar, rather than annotating by default.
- Made headline and subhead authorship explicit in reconstruction: title claim from `chart-annotations`, style from `karthik-data-visualization`, voice from the installed writing skill. There is no dedicated headline skill and none is added.
- Scoped the eval brief to the rendered artifact plus prompt, inferred style, headings, and intended message - not the source image, maker diagnosis, or rendering code - to keep the read blind.
- Made the installed writing or brand-style skill a conditional dependency, invoked only when available.
- Strengthened data inference: step 1 must infer the full period-by-category table (a value for every period and every category/series/stack the chart encodes), not just totals or the envelope. Fixes charts where the category breakdown was silently dropped.
- Added a "key messages and required content" judgment to `dataviz-critique`: from the source it now names the one or few messages the chart must carry, the content each message requires, and - explicitly, with a reason - any information dropped as not key, plus whether the messages need one chart or several. Added to the reader-facing template and the audited JSON contract (`key_messages`, `dropped_as_not_key`, `chart_count_hint`).
- Added two guardrails on the key-messages judgment after a run dropped the model categories with a plausible-sounding reason ("many thin stacked segments and long legend", "without inventing unreadable category precision"): the source's form declares its messages (a stacked/multi-series/faceted chart has the category comparison as a key message, so collapsing it to a total drops a key message), and difficulty of recovery - approximate screenshot values, crowded legend, "unreadable precision" - is never grounds to drop a dimension, only to pick a better form (small multiples, direct-labelled lines, top-N plus "other"). Source illegibility triggers a redesign, not deletion.
- Added a third guardrail after a run kept every category but re-rendered the same many-series stacked bar (the form that makes model-by-model comparison illegible): preserving the message is not preserving the form. The data must survive; the encoding must not, and often should not. When the source form is the reason a key message is hard to read, changing the form is the repair - a many-series stack whose message is per-series comparison becomes small multiples or direct-labelled lines, not a tidier stack. Tightened the `dataviz-selector` trigger in `dataviz-fix` so a many-series stack is never treated as "clearly correct" enough to skip selection when the message is per-series comparison or trajectory.
- Reframed information preservation in `dataviz-fix` as that judgment rather than a keep-everything rule: reconstruction carries every key message with its required content (possibly across several charts - a whole-and-parts split) and honours the critique's explicit drop decisions. What must survive is the messages, not every mark; silent drops are the failure, reasoned drops are fine. Preservation is owned by the critique and the rebuild, not the later eval, which stays final-image-only. Retired the abstract "preservation mapping" framing.

### Repair reliability

- Removed mandatory chart-dimension selection and value-precision status reporting from the repair contract; renderer profiles and internal evidence safeguards remain available without adding user-facing ceremony.
- Removed repair-stack overfitting: fixed critique and redesign quotas, forced structural changes, chart-family-specific audit zones, and a Matplotlib-only creator prompt. Critique depth, renderer, chart regions, and change class now follow the evidence and delivery conditions.
- Added one bounded creator critique before building and one focused critique of the first export, with general checks for typography hierarchy and redundant identification or scale elements. These checks stay inside the creator stage and do not reopen the independent-review loop.
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

# Devlog

## 2026-08-12 - Scope-safe chart repairs from Hermes feedback

### User prompts

> "go through all the hermes conversations about different dataviz etc. and see what possibly needs fixing in these skills, this is based on my feedback to mistakes etc. for testing use local files ... not hermes."

### Work done

- Reviewed ten Hermes dataviz-repair cases and separated chart-design mistakes already covered by the skills from a remaining loop defect: narrow requests and preservation requirements were prose, not release checks.
- Added structured intake checks for additions, removals, relocations, and preservation. Later user feedback can now supersede a conflicting evaluator action without deleting the audit trail.
- Made the requested edit boundary authoritative in the fixer, evaluator, local runner, and tester. Untouched regions are regression checks; pre-existing out-of-scope defects are recorded as baseline concerns rather than added to the required work.
- Forward-tested the change on the local Zerodha VIX chart. The first cycle preserved the chart and removed the legend but found one label collision; the second moved only that label and received `Send`. Karthik then caught a missed requirement: the direct band labels belonged on both panels, not only the close-up. A third cycle added all three labels to the decade panel without changing anything else and received `Send`.
- Converted that miss into a panel-completeness rule: a shared legend replacement must enumerate and verify every applicable panel, facet, row, or series rather than passing after the easiest instance.
- Expanded the case-manager and tester regression suites and validated all 13 public skills.

## 2026-08-11 - Bounded repair loop and local tester

### User prompts

> "we need to loop engineer this properly so it doesn't go off into infinite loops"

> "we need the ability to give more prompts on maybe the audience, the purpose, the hypothesis, the message"

> "then to deploy a web app where people can use their own API keys and test this out"

### What changed

- Replaced the implicit prompt loop with explicit states, transition records, stopping reasons, configurable budgets, duplicate-artifact checks, no-progress detection, and best-candidate preservation.
- Made audience, purpose, question, hypothesis, message, medium, delivery details, and constraints editable and versioned. Evaluations now identify the exact context version they used, and changed context cancels or supersedes stale review work.
- Added token, cost, latency, and call telemetry without flattening gate results into one score.
- Converted each user correction into a structured acceptance check: target, current state, required state, and reader consequence.
- Added a localhost FastAPI case console with image paste/upload, context editing, feedback, manual candidate uploads, artifact comparison, limits, stop/resume, and history.
- Added an opt-in local Codex runner. Each user action starts exactly one creator process and one fresh blind-review process against the checked-out skills; the UI never starts the next revision automatically.
- Ran the first real local cycle on the problematic 30-sector chart. It produced one candidate and one independent `Send` verdict in 337 seconds. The candidate kept row labels beside their bar endpoints, removed the unexplained Banks emphasis, used one neutral categorical colour, and made the loss-gain asymmetry the title claim.
- The live run exposed two workflow defects before deployment: the initial prompt was swallowed by the CLI image argument, and the outer development sandbox blocked nested Codex startup. Both failures consumed zero model tokens and were retained as stopped/blocked transitions before the successful resume.
- The successful cycle reported 688,535 cumulative CLI tokens, including 590,592 cached input tokens. That showed that a cumulative token ceiling cannot interrupt one model call and that the tester needs a measured preflight estimate. Added the estimate, moved build checks before calls, and made the wrapper own artifact and verdict transitions.
- Karthik rejected the first `Send` because exact direct labels still sat beside a redundant x-axis and gridlines. The second cycle removed both, retained the meaningful zero baseline, and kept dense row labels at regular weight; Karthik accepted it.
- Classified the first `Send` as an ambiguous evaluator rule. `karthik-data-visualization` already required quantitative scales and references to add information, but `dataviz-eval` made duplicate categorical identity more explicit than duplicate quantitative scaffolding. Tightened only the evaluator rule and kept it conditional on the reading task rather than banning axes on directly labelled charts.
- Kept raw provider adapters, bring-your-own-key handling, stronger isolation, and private deployment as separate milestones.
- Added 26 regression tests across the case manager, tester API, and local-runner orchestration.

## 2026-08-10 - Dataviz eval framework rebuild

### User prompts

> "now let's fix the dataviz-eval skill. it was an adhoc thing built by hermes. need to build it up properly based on my principles and all the conversations on dataviz i'd had with hermes. also check out the 'measuring good' PDF"

### What changed

- Reconstructed the evaluation principles from four Hermes repair cases, 28 chart iterations, and the associated user feedback.
- Used Vikram Nayak's Fifth Elephant 2026 talk to separate creator, expert reviewer, and audience reviewer roles and add an offline benchmark method.
- Rebuilt `dataviz-eval` around blind reads, six hard gates, four verdicts, a minimum pass set, and chart-spec operations instead of vague feedback.
- Added a failure taxonomy, gate anchors, representative golden-set guidance, inter-rater calibration, regression reporting, and rules for when a repeated failure should change a skill.
- Forward-tested the skill on four raw Hermes artifacts. It caught a mistranscribed data row, lost provenance, thumbnail failures, and a broken slopegraph export; a second pass also learned to scope repair checks to source fidelity and not fail an accepted chart on an invented Telegram width.
- Made `dataviz-eval` a required gate inside `dataviz-fix` rather than an optional companion mention. Added deterministic evaluation records to every case packet and explicit routing for `Send`, `Revise`, `Redesign`, and `Not evaluable`.
- Audited the first live full-pipeline run. The evaluator falsely passed a floating FY20 label and a legend/mark colour mismatch, only the first of four iterations was evaluated, HTML was logged instead of the attached screenshot, skill files were changed mid-loop, and several replies omitted the chart. Added deterministic guards and literal edit checks for each failure.
- Added the missed visual diagnosis from that run: totals on stacked bars did not make the intermediate components readable, yellow against white was unacceptable, and distinct legend colours were useless when the plotted segments used a different mapping. Routed these rules to selector, implementation, and evaluation rather than the repair umbrella.
- Replaced the narrow yellow-on-white fix with a full colour system that keeps Tufte's hierarchy intact: focal colour plus grey context, data-type-aware scales, stable semantics, restrained saturation, colour-independent decoding, practical contrast targets, and export checks in grayscale, compressed, and colour-vision-deficiency views.
- Updated both Codex and Claude/Hermes surfaces, human docs, changelog, and packaging rules for the new runtime reference.
- Audited a later live run where the creator loaded `dataviz-eval` but gave all three of its own exports six `Pass` ratings. The final image still contained colliding text, uncertain label-to-mark pairing, large relationship-breaking gaps, and an unexplained focal colour.
- Replaced self-review with a fresh Hermes `delegate_task` reviewer and a structured, artifact-hashed report. `case_manager.py` now rejects `Send` unless all six gates and five evidence-backed release checks pass.
- Kept the repair generic: the reusable rules concern visual integrity, relationship traceability, spatial economy, encoding semantics, and delivery robustness. The failed sector chart remains a regression artifact; no sector name, chart type, colour, canvas size, or fixed threshold entered the skills.

## 2026-08-10 - Dataviz eval gate and documentation pass

### User prompts

> "document these new skills and today's changes explicitly as well and push them to the GitHub"

### What changed

- Added the `dataviz-fix` repair loop and its persistent case manager for originals, iterations, feedback, acceptance, and skill diagnosis.
- Fixed the pushed repair-loop bundle: `case_manager.py` had been hidden by the repo-wide private-script ignore rule even though `dataviz-fix` invokes it at runtime.
- Added validation for missing or ignored runtime scripts and repaired the thirteen-skill navigation indexes.
- Added the initial `dataviz-eval` inspection gate and documented it in the public skill index.
- Updated the dataviz skill stack with inspect-revise-render, geometry-before-type, and export-vs-viewport guidance.

## 2026-08-03 - Chart explainer skill

### User prompts

> "next i want to build a skill to explain a data exploration. like sometimes i tell claude / codex \"build a notebook to help explore this data\". and the thing is because i'm not running the explorations myself, i don't know what hte insight in the data is. rather - when someone else sees a dataviz i've made, i'ts difficult for htem to know what teh message in it is. this has nothing to do wtih the text on the dataviz itserlf - this is about accompanying / explaining. think about sending a graph along with an email (2 lines per graph only; not too long). it could also apply to a table etc. i need you to build a skill for this. there are 2 data sources for this. one is - my own Rmd files wehere i'e explored data and written notes. the seoncd are my Mint articles (in ../Mint) where i've written articles along with graphs etc . first gather material etc. and ask clarifiing questions, and then buikld the skill. don't build straight away."

> "5 verdict types is too narrow. i only need guidelines that the LLM caan then improvise upon"

> "ok do it"

### Where the material came from

Two corpora, and they turned out to teach different halves of the same skill.

**210 `.Rmd` files across `~/Documents/work`.** Ranked by prose volume outside code chunks, then the prose immediately following plot-producing chunks was extracted. Most of it is forward-looking - "Let's look at orders by date by commodity" - and useless. The valuable residue is the small set of terse verdicts he writes after seeing a plot:

```
No signal here.
No real correlation between rejects and routes.
Clusters seem very very similar. So not much information from them.
One is larger than the other, that's all.
Interesting that some commodities are not ordered much on Sundays.
In general, it seems like our prices are less volatile than BigBasket.
Or is this just a data collection issue?
```

These are the source of the null-verdict rule. In an exploratory notebook the honest answer is usually "nothing here", and the notebooks prove he writes it that way.

**614 files in `~/Documents/work/Mint`.** 145 sentences containing a figure or chart reference were extracted from the `.docx` files by unzipping `word/document.xml` and stripping tags. This is where the two-line contract came from. The consistent shape is a claim sentence with the figure reference welded on, followed by one payoff sentence:

```
Debit cards were swiped at points of sale 234 million times in November, nearly
twice the monthly average from the first nine months of the calendar year (Figure 2).

Figure 4, however, suggests otherwise - the number of wickets lost per innings has
come down over the years.

Until then, the average rate of scoring during the slog overs of the chase was just
over eight runs per over. In 2014, however, that average jumped up to over 9 runs
per over, and has stayed there.
```

Every number in the Mint corpus carries an anchor. "234 million" never appears without "nearly twice the monthly average". That observation became the hardest rule in the skill.

The corpus also showed a pattern worth encoding rather than banning: sentences like "Figure 1 shows a scatter plot of marginal and effective tax rates for different countries" are weak alone, but he always pairs them with a payload sentence immediately after. That is the orientation exception - line 1 may orient, but line 2 must then carry the claim.

### Decisions taken

- **Two lines, hard.** Line 1 is the claim with an anchored number; line 2 is exactly one of contrast, consequence, or caveat. Rejected: a flexible length that scales with the chart's complexity. The constraint is the point - it forces a decision about what the exhibit is for, and the request was explicitly "2 lines per graph only".
- **Guidelines, not a taxonomy.** The first draft classified every note into five verdict types (signal, reversal, regime change, no signal, plumbing). Karthik rejected this as too narrow. The five survive only as a non-exhaustive prompt list, explicitly flagged as "to loosen your thinking, not to classify into". The instruction that replaced them: say out loud what the chart is actually saying, then compress. Reason: a menu of five produces notes that fit the menu, and most real charts say something that is not on it.
- **Nulls are mandatory output.** "Nothing here" is a required capability, not a permitted one, with two sub-rules: say what you looked for and did not find, and never upgrade weak to moderate. This is the failure the skill exists to prevent - an agent-run notebook of dead ends being written up as a deck of findings.
- **Compute, never eyeball.** When data is available every number is computed from it. Rejected: allowing numbers read off a rendered chart when they are "clearly legible". See the test section below for why.
- **Register asked once, defaults to note-to-self.** Three registers - self, colleague, client. Register changes wording only; it never softens a null into a maybe. Rejected: inferring register silently from the folder or the presence of an email draft, which fails quietly and in the expensive direction.
- **Chart quality is out of scope.** A bad chart still gets a note, with no critique attached. `dataviz-critique` and `chart-improver` own that. Rejected: a one-line "this reads better as a slope chart" flag, on Karthik's call - keeping skills separate beats a helpful aside.
- **Batch mode refuses to build a narrative.** Twelve plots get twelve notes in figure order, no summary paragraph, no reordering, no dropping the nulls. This is the same failure as the null rule, one level up.
- **`examples.md` ships inside each surface directory**, not at the skill root. `sync-skills.py` only copies `<skill>/codex/` and `<skill>/claude/`, so a root-level `references/` folder is repo-only and invisible to the installed skill. The example bank has to be readable at runtime, so it is duplicated across both surfaces and the edit rule in the folder README says to update both.

### Testing the skill on real charts

Ran it against `india-ias-officers/ias-profile.csv`, a dataset not used to build the skill. Three quick charts: female share of allotments by year, median age at joining by year, domicile distribution.

The compute-don't-eyeball rule earned its place immediately. The first pass at chart 2 sampled the head and tail of the series:

```python
a = d.groupby('Allotment_Year').age.median()
print(a.head(3).to_dict(), a.tail(3).to_dict())
# {1970: 24.4, 1971: 24.0, 1972: 24.3} {2018: 28.1, 2019: 26.5}
```

which reads as a clean, publishable finding: median joining age crept up from 24 to 28. Forcing the full series out instead showed medians above 47 across the whole of the 1990s and 2000s, peaking at 52.5 in 2005-06. `Date_of_Joining` is not the entry date for most cohorts. The eyeballed version would have shipped as a finding; the computed version produced a plumbing note telling the reader not to use the field.

The three notes the skill produced:

```
1. Female share of IAS allotments rose from ~10% in the 1970s to 26% in the 2010s.
   The rise stopped around 2013 - it has bounced between 16% and 34% since, with no
   further trend.

2. Median age at joining reads 24 in 1970 but 47-52 through the 1990s and 2000s.
   Date_of_Joining is not the entry date for most cohorts - don't use this field
   until that's resolved.

3. Domicile is blank for 21% of the 12,134 officers - more rows than any state
   except Uttar Pradesh (1,471).
   Any domicile ranking off this is provisional.
```

Two of three are caveats rather than findings, which is the correct ratio for a cold dataset and the thing a narrative-building version of this skill would have hidden.

### Follow-up: firing on notebook-build requests

> "this chart explanation skill needs to be invoked whenever i ask an LLM to \"build an exploratory notebook for this data\" etc. as well"

The original description only matched requests that mention a chart. A notebook-build request mentions no charts and the plots do not exist yet, so the skill would have been invoked - if at all - as a cleanup pass after the notebook was written, which is too late: the notes have to come from each chunk's computed output, not from a later reading of the finished file.

Three changes:

- **Description widened** on both surfaces to name "build an exploratory notebook", "explore a dataset", and "produce analysis someone else will read" as triggers. The Claude description was rewritten too, and stays under the 200-character validator limit at 161.
- **New section, "Exploratory notebooks you are building"**, establishing that in this case the notes are the deliverable rather than a later pass. Five rules: note in markdown under every plot chunk; written after running the chunk, from its output; note-to-self register by default; nulls stay in with their plots; no findings summary unless asked.
- **Cross-reference added to `karthik-r-analysis-style`**, in the "Prose style inside notebooks" section. That skill's existing note examples are all lead-ins ("Let's only look at stores with enough days") - what you are about to look at. It had nothing about what a plot turned out to show. The new subsection marks `chart-explainer` as a required sub-skill for after-plot notes, and repeats the register constraint so the two-line note does not arrive as scaffolding in a skill that bans scaffolding headings.

`karthik-r-analysis-style` has no copy in this repo - it exists only as installed files under `~/.claude/skills` and `~/.codex/skills`, which differ slightly from each other. Both were patched by anchor rather than by overwrite. If it ever gets a source repo, that edit needs to move there.

### Follow-up: analysis-style skill into the repo, and a consistency pass

> "add that analytics style to the repo. and make sure all of this is consistent in boht claude and codex"

`karthik-r-analysis-style` is now `karthik-r-analysis-style/{codex,claude}/` in this repo, imported from the installed copies. Both `SKILL.md` bodies were already byte-identical - only the frontmatter differed, in exactly the way this repo's convention expects (Codex gets the long trigger-rich description plus `metadata.claude-description`; Claude gets the short one). The `references/` folder ships inside each surface directory rather than at the skill root, because `SKILL.md` reads `references/style-observations.md` and the two audit files at runtime, and `sync-skills.py` only copies `<skill>/codex/` and `<skill>/claude/`. Same reason `chart-explainer/examples.md` sits where it does.

One repair on the way in: the Claude description contains a colon (`Karthik-style R analysis: local-precedent...`), which is invalid as a bare YAML scalar. It had survived as a folded block scalar in the installed file. Now JSON-quoted on both surfaces.

Then an audit across all eleven skills, on two axes:

```
skill                            claude_desc_len  mirror_ok  body_identical
chart-annotations                       112         fixed         True
chart-explainer                         161         True          True
dataset-question-generator              100         True          True
dataviz-critique                         91         True          False   <- flagged
dataviz-orchestrator                    110         fixed         True
dataviz-selector                        122         fixed         True
karthik-analysis-planner                136         True          True
karthik-data-cleaning                   145         fixed         True
karthik-data-visualization              147         True          True
karthik-powerpoint-style                175         True          True
karthik-r-analysis-style                128         True          True
```

- **`mirror_ok`** - whether the Codex file's `metadata.claude-description` matches the description the Claude file actually ships. Four had drifted: two were missing the field entirely, and two carried superseded wording (`chart-annotations` still said "annotate" where the live description says "mark"; `dataviz-selector` carried an entirely different sentence). Mirrored the live Claude description in each case, since that is the one a running agent reads. Documentation-only.
- **`body_identical`** - whether the two surfaces teach the same thing. Ten of eleven match. `dataviz-critique` does not: the Claude body is a genuinely condensed rewrite, 122 lines against 186, with sections merged and the "Inputs to seek or infer" list dropped. That is a behavioural divergence, not drift, and reconciling it means choosing which version is correct. Left alone and raised with Karthik rather than resolved silently.

Also deleted the memory note saying this skill has no source repo. It does now.

### Wiring

`dataviz-orchestrator` was left alone. The orchestrator ends at a critiqued chart; narration for an absent reader is a separate job and Karthik did not ask for the loop to be extended. Worth revisiting if the orchestrator starts producing multi-chart outputs meant to travel.

## 2026-08-03 - Chart annotations skill

### User prompts

> "i want to build a \"chart annotations\" skill. how do we go about this? basically - i think wiht LLMs, now it's good practice to mention in a dataviz what the clear message is. actually mark it out and write a comment there. however, tehre is skill involved in this - how do you figure out hwat to hightlight? hwo do you figure out what is more significant? and then how do you figure out how to write the label concisely? i think tehre must be enough material on this c omputer (or in this folder) that will point you to how to build this. as a first step gather all of it, and summarise the insights. and then we can go about building the skill."

> "this should be a standalone skill. and the dataviz orchestrator in some sense needs to include this. let's also resovl the gaps you've mentioned (ask one by one) before you build the skill"

### Where the material came from

The gather step found existing material scattered across four places, and one of them turned out to be the whole spine of the skill:

- `bangalore/weather/fewshot_annotations/distilled_editorial_rules.md` and `fewshot_prompt_draft.md` - a reviewed bank of 12 historical weather windows where Karthik wrote the preferred lead framing for each and noted what the model should learn. This already contained a signal hierarchy, negative guidance, and headline templates. It is the source of the significance ladder and the concentration check.
- `bangalore/weather/bangalore_weather_update.R` (system prompt, ~line 610-625) - the production wording constraints: under 18 words, one claim, numbers tied to their named window, banned dramatic and bureaucratic registers, "observant resident not lab report".
- `dataviz-selector` - the geometric candidate list: knee-bends, inflections, local extrema, temporary peaks, thresholds, events.
- Zerodha workshop material (`what-makes-good-dataviz.md`, `insight-to-visual-brief.md`) - the eraser test's explicit carve-out that annotations needed for comparison must not be erased, and the evidence → claim → comparison → visual job chain.

Roughly 200 `annotate()` / `geom_text()` calls across 58 R files supplied the mechanics but no written rules, which is why placement and visual weight had to be decided fresh.

### Decisions taken (four gaps, resolved one at a time)

- **Title vs annotation.** Title states the claim in words; annotation locates it on the evidence. Rejected: neutral title with the claim living entirely in the annotation, and a medium-dependent rule. Reason: the same sentence appearing twice is the failure being prevented, and a single rule is easier to hold than a per-medium branch. A standalone-travelling chart is an explicit exception, not a second rule.
- **How many.** Hard cap of one primary plus at most two supporting; more surviving candidates means split the chart. Rejected: strictly one per chart (under-annotates real S-curves), and scaling with chart type (too soft to enforce).
- **Visual weight.** Two tiers - primary takes accent and bold, supporting stays grey and small. Rejected: annotation always quieter than data, which would have made the primary annotation too weak to lead the eye.
- **Connectors.** Proximity first, hairline segment only when the nearest free space is ambiguous, arrowhead only when the target is one point among similar points, never crossing data. Rejected: always connect (chartjunk), and never connect (forces dropping legitimate annotations).
- **Verification.** Rendering and inspecting the exported image is mandatory in the skill, not delegated to whichever skill is driving. Placement is the one thing that cannot be checked from code.

### Generalisation choices

The weather material is domain-specific and had to be lifted without dragging rainfall with it:

- "If most rainfall came from one burst, do not call the window wet" became the **concentration check**: before annotating any aggregate, test whether a small subset explains most of it. Given a rough threshold (<20% of observations carrying >50% of the effect) so it is actionable rather than a vibe.
- "Record clusters beat temperature departures beat rain bursts" became a five-rung **significance ladder** in domain-neutral terms, explicitly marked as a default that can be overridden with a stated reason.
- The six weather headline templates collapsed into **four label shapes** covering event+consequence, run+gap, sustained extreme, and aggregate+subset.
- The banned-word list kept its structure (dramatic register, bureaucratic register) but the examples were generalised past rainfall.

### Wiring

`dataviz-orchestrator` now lists `chart-annotations` as a companion skill and calls it at step 7, between choosing the visual and running the critique pass. Both the Codex and Claude variants were patched.

### Testing the skill on real charts

> "can you do that yourself? pick a few charts, run this and evaluate, and rewrite teh skill accordingly."

Three charts were built from real data in `data_work`, chosen to attack different weak points. Every revision below traces to a defect in a rendered image, not to a principle.

**Chart A - All-India annual rainfall, 1871-2011.** Chosen because the series has no trend at all: `lm` slope -0.07 mm/yr at p = 0.74, decade means bouncing in a 1031-1146 band. The skill had a candidate inventory full of knee-bends and extrema and no way to say "nothing here qualifies". Following it literally pushed toward marking the wettest year (1917) or the longest above-mean run (1942-49), both of which are noise. The first fix drew a +/- 1 SD band with decade averages over it and annotated the absence: "Every decade average falls inside the band". Karthik overruled this - "if there is no story there should be no annotation" - and he is right: that callout is the title said twice, spending chart space to restate what the band already shows. Re-rendered with no annotation at all and it reads better. The rule is now: no story, no annotation; the absence goes in the title; the band and decade line stay as **context layers**, which encode data or a stated baseline rather than pointing at a feature, and so sit outside the annotation cap. Added the "When nothing clears the bar" section and the would-this-survive-a-different-sample test.

The context-layer/annotation distinction was the real yield here. It was implicit and doing no work until the absence case forced it out.

**Chart B - Bangalore mean maximum temperature, 1901-2000.** Flat overall (-0.015C/decade) but V-shaped: a breakpoint scan put the knee at 1956, with -0.18C/decade before and +0.22C/decade after. The rendered chart was clean and the annotations were correctly capped, but two things were wrong in substance. The knee came from taking the minimum SSE over a scan of 61 candidate years, with no test that it was real, and it got a bare "1956" label implying single-year precision. And the two-segment fit was drawn in accent red over faint grey observations, so the loudest thing on the chart was a model rather than data. Added the observed/derived split to the candidate inventory and the "Annotating derived features" section.

**Chart C - state liquor revenue per capita, 2025-26 vs 2026-27.** The existing chart in `data_work` labels six of ten states; the skill's cap says one primary plus two supporting. The capped version was better, but produced two genuine defects. First, the annotation coordinates were hand-typed as `y = 8.6` and `y = 1.55`, and both landed on the wrong rows - "+Rs 147" appeared between Andhra Pradesh and Karnataka, and "+Rs 7" sat above Rajasthan rather than on Tamil Nadu. Rebuilding with an annotation frame filtered from the plotting data, positioned as `x = pc_2026 + 40` against `y = state_f`, fixed both. This is the single highest-value rule found by testing: a mislabelled row looks completely correct and states something false. Second, the first title read "Haryana drives almost all of the per-capita increase" - but Haryana is 418 of a 1,071 total, or 39%. The concentration check would have caught it, except the skill only applied it to annotations. Corrected to a rank claim, and the check now gates the title too.

Also found in both A and C: annotation text clipped at the right edge because scale limits were set for the data, not for the data plus its labels. And in C the period labels collided with the primary annotation, which raised the question of whether orienting labels count against the cap - they do not, but they must be collision-checked.

### Revisions made

- Derive annotation coordinates from the data, never hand-type them; worked R example included.
- New "When nothing clears the bar" section: absence as a legitimate annotation, with the band-and-inside device.
- New "Annotating derived features" section: validate before marking, word to the method's real precision, never let the fit outshout the data.
- Concentration check now gates the title as well as the annotation, with the rank-claim vs share-claim distinction spelled out.
- Orienting labels named as a class outside the cap, but still collision-checked.
- Reserve axis headroom for label text before rendering.
- Six new rows in the common-mistakes table, each from an observed defect.

Skill grew from 164 to 225 lines. Test charts were scratch work and are not committed.

### Second test round: three fresh charts

> "ok now test on 3 new charts before pushing"

New shapes, chosen to avoid repeating the first round: a scatter with a cluster rather than single-point outliers, a long time series with a takeoff, and a small state-level scatter with a metric that means two opposite things.

**Chart D - 495 Indian cities over 100,000 people, overall literacy against the male-minus-female literacy gap.** Two failures, both instructive. The label read "Rajasthan: 13 of the 20 widest gaps"; the number is 12. It was typed rather than computed, and the previous round's derive-from-the-data rule covered position only - it said the label text should be computed too, but as an aside inside the placement section, and that was not enough to stop it. Promoted to a hard rule of its own. Second, the label was anchored at the median of the Rajasthan points, which is the centroid of the cluster, which is the densest and least readable place on the chart. Deriving the coordinate was right; resting the text there was wrong. The rule is now anchor on the group, then offset to the outside edge of the cloud.

The deeper problem with D was that the title claimed one thing ("cities with low literacy are also the least equal", a statement about the whole cloud at r = -0.56) and the annotation marked another (a subgroup holding the tail). Both true, and the chart still failed - the reader is handed two findings and told which matters by neither. The "one dominant frame" filter only governed competing annotations, not title-annotation coherence. Rebuilt around the Rajasthan claim alone and it works.

**Chart E - share of women among IAS officers by allotment year, 13,571 rows.** The annotation read "share triples after 2005, flat for the 45 years before". The second half is false: the pre-2005 period runs from 5.7% in the 1960s to 13.9% in the early 2000s, a slope of 1.5 points per decade at p = 0.0002. The chart was inventing a plateau. This is a distinct failure from a wrong number, because no number appears in the phrase - "flat" is a quantitative claim in plain clothes, and so are unchanged, steady, doubled, tripled, halved. Added them by name to the wording constraints. The honest framing turned out to be better anyway: an acceleration from 1.5 to 12.1 points per decade beats a fabricated flat-then-takeoff.

E also exposed a hole in the derived-features rule. That rule was written for a breakpoint found by scanning. Here 2005 was picked by eye, which felt like observation and is actually worse - a split chosen after seeing the outcome, with no scan to point at. Extended the rule to cover analyst-chosen splits explicitly.

**Chart F - median age at marriage by state, women's age against the men-minus-women gap.** Built to test whether the skill stops a metric whose low values have two opposite meanings: Rajasthan has one of the narrowest gaps in India at 3.0 years, and also the earliest marriage for women at 18.6, so "narrowest gap" reads as equality and means the opposite. The skill did not prevent it - what prevented it was writing the title as the negative claim and marking both ends. That produced a new finding: the two labels are halves of one claim, and tiering them into primary and supporting would say one end matters more when the comparison is the whole point. Contrast pairs now count as one annotation and share weight.

F also clipped its Rajasthan label off the left edge, while the previous round's headroom rule only mentioned right-hand labels. Generalised to every edge the text can reach.

Skill now 252 lines. Verified the fixes by rebuilding chart D against the revised rules: single claim, all three numbers computed, label offset to clean whitespace, no clipping.

## 2026-07-19 - Slide-style fixes from the Zerodha workshop deck

Building a workshop deck surfaced repeated misses that fed back into `karthik-powerpoint-style` and `karthik-writing-style`:

- Kept producing clever aphoristic slide titles ("Analysis is never a straight line", "The machine does the work. You make the calls.") and "X, not Y" reveals. Karthik's real decks use plain labels and questions ("Normalisation", "What is average?", "Compared to what?"). The skill's old "make the title an analytical claim, not a topic label" line was actively pushing the wrong way; softened it and added explicit Slide-title do/don't guidance.
- Paraphrased Karthik's own "Smelling Bullshit" slides into fresh prose instead of lifting them verbatim. Added a "reuse own material verbatim" principle to both skills.
- Flattened real deck images into text stand-ins. Added guidance to pull real images from `.pptx` `ppt/media/`.
- Wrote out full instructions on hands-on slides that never get projected. Added the facilitator cue-card pattern.

`karthik-writing-style` lives only as installed Claude/Codex copies, not in this repo, so those were edited in place.

## 2026-06-19 - Dataviz selector skill session

### User prompts

> "i already have one data visualisatiohn skill. now i want to build one more to pick the right kind of visualisation for a given data set / problem statementt."

> "check out my old blog visualisations.substack.com where i've commented on various visualisations. both good and bad."

> "also mine my Mint articles (Mint folder here) to get more insgihts from there. also powerpoints in this folder with datavizs."

> "ok now put all this together to make a skill."

> "ok now put this skill as well into this git https://github.com/skthewimp/karthik-data-visualization-skill"

### Work done

- Built a new public `dataviz-selector` skill to choose chart forms from a dataset plus question/hypothesis/story.
- Calibrated the skill from Karthik's Mint articles, local PowerPoints, Substack visualisation critiques, and one-at-a-time user feedback on chart-choice scenarios.
- Added hard guardrails against pie, donut, 3D, animated, interactive-first, gauge, radar/spider, and decorative infographic recommendations.
- Red-teamed the selector with out-of-sample prompts and rendered local examples from fuel-price, small-airport, and management PBT-miss data.
- Added the skill to this public repo, updated `sync-skills.py` to build/install multiple skills, generated Codex and Claude distributions, and pushed commit `df5c507`.
- Added repo documentation, skill docs, this devlog, and a short blog-style writeup about the process.

## 2026-06-19 - Navigation docs preference

- Repo should be easy for a new person to navigate from GitHub alone.
- Keep README files in every public folder, including skill folders and `codex/` / `claude/` subfolders.
- Do not expose private `references/` or `scripts/`; those stay local-only and ignored.

## 2026-06-24 - PowerPoint style skill

- Added `karthik-powerpoint-style` as a third public skill, with both `codex/SKILL.md` and `claude/SKILL.md` to match the repository's per-skill surface layout.
- The skill captures reusable instructions for making analytical PowerPoint-style slides in Karthik's style: claim-first titles, sparse layouts, direct labels, chart-first evidence, minimal decoration, source notes, and management-ready slide patterns.
- Added folder-level READMEs for the new skill and a human guide at `docs/skills/karthik-powerpoint-style.md` so a new GitHub reader can navigate the skill without prior context.
- Updated the root README and docs index to describe how the PowerPoint skill relates to `dataviz-selector` and `karthik-data-visualization`.

## 2026-06-25 - Dataviz critique skill and documentation

### User prompts

> "Now I want to build a new skill on how to critique a visualization..."

> "Can it come up with two or three different new alternatives for visualization?"

> "you need to put a changelog /devlog / ... right now the documentation isveryvery weak"

### Work done

- Added `dataviz-critique` as a public Codex/Claude skill for reviewing existing charts, dashboards, slide visuals, and AI-generated plots.
- Based the critique workflow on Kaiser Fung's Question–Data–Visual trifecta and Karthik's clarity-first, intentional-design visualization philosophy.
- Extended the skill from critique-only to critique-plus-redesign: it now proposes minimal repair, better analytical redesign, and different story-lens alternatives where useful.
- Expanded `docs/skills/dataviz-critique.md` into a full human-facing guide with fit, inputs, output contract, redesign patterns, and example skeleton.
- Added `CHANGELOG.md` so public repository changes are easier to scan separately from session notes.



## 2026-06-30 - Analysis planner skill

### User prompts

> "Build the next unchecked skill from the TODO list as a Codex skill... let's start with analysis planner... go through a sample of [~/Documents/work]... pay special attention to ~/Documents/work/Mint..."

> "all skills that we're building in this session need to be built for both Claude and Codex and pushed to my data visualisation skills repo. see the format of that repo and build accordingly"

### Work done

- Added `karthik-analysis-planner` to the public data visualization skills repo with both `codex/SKILL.md` and `claude/SKILL.md`.
- Based the skill on Karthik's recurring notebook pattern: question, pulse check, row grain, denominator, comparison, sanity checks, falsifier, caveat, then prose.
- Included the Bangalore 4pm rain question as the mini-example and updated README/docs/changelog navigation.

## 2026-07-03 - Dataset question generator skill

### User prompts

> "do we already have a skill that, just given a raw dataset, figures out what questions to generate?"

> "ok do that. use all the analysis in my computer. including outside this folder. to get training data for htis."

> "ok and now produce both codex and claude versions of it, push it to karthik-data-visualisaiotn repo in the right format, etc. also update your memory..."

### Work done

- Added `dataset-question-generator` as a public skill with both Codex and Claude versions.
- Based the skill on Karthik's local analysis patterns: Bangalore weather normals, wind/rain mechanism questions, payments volume/value/ticket-size splits, election swings and corners, operations bottlenecks, survey subgroup comparisons, and urban morphology questions.
- Made the skill explicitly reject stale prompts and generic "trend of X" questions unless there is a clear comparison, denominator, or visual signal.
- Updated README, docs index, skill docs, changelog, and local memory workflow.

## 2026-07-03 - Contextual data cleaning skill and repo alignment

### User prompts

> "should we update teh orchestrator skill now that we have a contextual data cleaning skill as well?"

> "actually look through the repo and see what else needs updating based on everythign else that's there now"

### Work done

- Added `karthik-data-cleaning` to the public skill set and wired it into the rest of the repo navigation.
- Updated `dataviz-orchestrator` so the workflow is no longer “profile then analyse” in the abstract; it now explicitly includes contextual inspection, cleaning, reshaping, joins, and validation before charting.
- Updated `dataset-question-generator` and `karthik-analysis-planner` so messy data gets cleaned only when that is needed to make signals or metrics legible.
- Filled in missing README files for newer Codex/Claude skill subfolders and brought the docs indexes/changelog up to date.

<!-- codex-session:019f26a5-c9d8-7292-8734-869cb2992a60:start -->
## 2026-07-03 11:53 IST | Codex session `019f26a5-c9d`

### User prompts
> should we update teh orchestrator skill now that we have a contextual data cleaning skill as well?
> actually look through the repo and see what else needs updating based on everythign else that's there now
> is the repo clean now?

### Work done
- Need changelog mention README pass.
- Done. - Proper READMEs added/expanded across public skill folders, Codex/Claude folders, docs folders. - Kept private reference/script contents ignored, but allowed their README files. - Data-cleaning is public again,...
- Touched files: `.gitignore`, `CHANGELOG.md`, `README.md`, `dataset-question-generator/README.md`, `dataset-question-generator/claude/README.md`, `dataset-question-generator/claude/SKILL.md`, `dataset-question-generator/codex/README.md`, `dataset-question-generator/codex/SKILL.md`
- .gitignore | 8 +++-

<!-- codex-session:019f26a5-c9d8-7292-8734-869cb2992a60:end -->

<!-- codex-session:019ff565-7102-71d1-b38d-b03059979603:start -->
## 2026-08-12 15:24 IST | Codex session `019ff565-710`

### User prompts
> ok we need to audit all the skills again. using hte local zerodha images for testing. now in the last few iterations, the fixes seemm to be way too specific to the specific cases and feedback and not generic enough. s...
> ok can you clean up the stuff, putting things in the most important skill? so there is no overlap or contraciction?
> yeah just push and commit and deploy to hermes

### Work done
- Review `git diff --stat`; the ownership cleanup is complete. Step 4/4 done: 1. Consolidated responsibilities across all 13 skills. - `dataviz-selector`: form and encoding choice. - `karthik-data-visualization`: visual...
- Start a new Hermes session to load the updated skill text. Step 3/3 done: 1. Committed `b83b929 refactor(skills): clarify ownership boundaries` 2. Pushed `main` to GitHub. 3. Deployed and verified all 13 Hermes skills...

<!-- codex-session:019ff565-7102-71d1-b38d-b03059979603:end -->

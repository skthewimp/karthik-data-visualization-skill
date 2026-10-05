# What not to do

Between about 20 August and 30 September 2026 we spent six weeks making the chart skills and the repair website worse while believing we were making them better. This note records how that happened, so that the next round of changes (by a person or an agent) doesn't repeat it.

It covers three repos:

- this one, `karthik-data-visualization-skill`
- `dataviz-repair-site`, the first attempt at a public chart-repair website, now archived
- `chart-doctor`, the rebuild that replaced it on 29-30 September

## What happened, in numbers

On 15 August (`3694a0e`) the skills were in good shape: 13 skills and about 21,500 words of skill text.

On 19 August the repair site went live on GPT-5.6 Sol at about 20 US cents a chart. To bring the cost down we moved to cheaper models, and the cheaper models made mistakes. Every mistake became a fix, in one or both repos.

By 28 September:

- the skills were 20 skills and about 39,300 words. `dataviz-selector` alone went from 1,057 to 4,850 words, and the new `dataviz-construct` family was 10,000 words by itself
- the MCP server had 26 tools (`scaffold_chart`, `reserve_frame`, `place_on_marks`, `refit_chart`, `read_marks_from_anchors` ...)
- the site had 416 commits (311 in the last month), about 33,000 lines of Python with `runner.py` at 9,200 lines, and 12,000 lines of documentation whose main job was to stop the next change undoing the last one
- a chart took 3-5 minutes, 8-15 sequential model calls and around 200,000 input tokens
- by the site's own count, about 16% of its commits were `restore`, `preserve` or `revert` commits undoing an earlier fix

On 29 September canonical delivery on the site fell from 6/7 to 2/7 in one day. We stopped, wrote a redo plan and built Chart Doctor in two days: one read, a couple of decisions, a ggplot script on a small house theme, one look, at most two fixes. It runs in well under a minute at about 1.6 cents a chart.

On 4 October the four core chart skills were rolled back to their 15 August text, the construct family was deleted and the MCP went from 26 tools to 2 (`recommend_colours`, `recommend_precision`). On 5 October every borderline rule added after 15 August was also judged overfit and left out.

Six weeks of work, net negative. Everything below is about why.

## The loop

Almost every bad change followed the same loop:

1. One chart comes out wrong (usually one of the seven canonical cases, often on a cheap model)
2. We trace it to a cause and write a fix: a prose rule, a gate, a tool, a contract field
3. The fix is written to sound general ("no case-specific triggers, all general")
4. It changes behaviour for every chart, and some chart that was fine gets worse
5. The next session fixes that, often by partly undoing step 2
6. Go to 1

Each step was locally reasonable. That is what made it hard to see. Nobody made one bad decision; we made two hundred small ones that each looked fine in the DEVLOG.

## The rules that got us here

These are the working assumptions we held during that period. Each one sounds sensible. Each one, applied repeatedly, did damage.

### 1. "A failing chart means a missing rule"

What we did: a sparse five-bar chart came out horizontal with a redundant axis, so we added six rules and a tool (`place_bar_value_labels`). A mixed-unit table became a five-panel grid, so the same-unit rule was promoted to a standalone "hard gate" bullet. The OpenRouter chart was mis-drawn three times in a row, so three prose patches went in, each fixing the last symptom and exposing the next.

What happened: the rules accumulated, contradicted each other and buried the original good guidance. The 15 August text, without any of them, was better.

Don't: turn one failing chart into a rule. A failing chart is a test case, not a spec. The question to ask is "would this rule exist if this chart had never been made?" If the answer is no, it doesn't go in.

### 2. "I've written it generally, so it isn't overfit"

What we did: nearly every DEVLOG entry from that period says some version of "kept general, not overfit to the example". The redundant-axis check went from "every mark labelled" to "80% of marks labelled" to "key anchors labelled" in a week, each version described as the general principle.

What happened: phrasing a rule generally doesn't make it general. If it was written because of one chart, tuned against that chart and accepted because that chart now looked right, it is fitted to that chart however abstract the wording.

Don't: trust the author's (or the agent's) own claim of generality. The trigger, not the wording, decides whether a rule is overfit.

### 3. "If the cheap model gets it wrong, take the decision away from it"

What we did: when a weaker model misplaced labels, sized canvases badly or picked the wrong axis range, we built a tool or a code-owned contract so the model wouldn't have to decide. Plan in JSON, then colour, precision, layout and frame tool calls, then a scaffold, then the model fills a `chart_marks` slot, then `check_chart` restores regions.

What happened: the model ended up filling a slot inside a scaffold inside a frame inside a plan. Every bug now sat at a seam between two of those (units, aliases, panel scopes, frame weights, label anchors), and most late-September commits were about carrying a value across one handoff. The charts looked like what the scaffold could express rather than what a good chart needed.

Don't: answer a model's mistake with more machinery around the model. First ask whether a better model at that one step, or a better default, would do it.

### 4. "We should build the tool that does it correctly"

What we did: a percentage line chart drew on a 0-100 axis, so we built `recommend_axis_range` and a schema to carry its output. We rebuilt canvas sizing, frame reservation, text measurement and label placement in Python.

What happened: ggplot already fits an axis to the data. The 0-100 axis came from a sentence in our own skill pushing the model to override that default. The tool reimplemented the renderer's logic, got log, date and categorical scales wrong, and invited the very override that was the bug. We then spent weeks reconciling our geometry with ggplot's.

Don't: build a tool for something the renderer already does. When a renderer default is right and the output is wrong, look for what is pushing the model off the default and remove that.

### 5. "If the rule didn't bind, make it louder"

What we did: rules that a weaker model ignored were moved up the page, turned into standalone bullets, labelled "mandatory", "hard gate", "first-pass mandate", front-loaded as numbered steps, and then repeated in a second carrier (the builder skill and the stage-contract string) because one copy wasn't enough.

What happened: an emphasis arms race. Every rule shouted, so none stood out, and the skills got longer each round.

Don't: stack an instruction on top of one that isn't working. If a rule doesn't change the output, remove it or replace it. More capitals and more copies are not a fix.

### 6. "Add a gate to catch it"

What we did: idea-critique gates, an execution gate, an aesthetic composition gate, inspection flags (`REDUNDANT_VALUE_AXIS`, `REDUNDANT_COLOUR` ...), each able to route back to an earlier stage.

What happened: gates disagreed with each other and with the producer. A delivery audit said `fail` and the chart shipped anyway. A follow-up chart spawned four subagents and bounced a label nudge from the execution gate back to build. Ten minutes an image on a fast Mac.

Don't: add a checker to compensate for a weak decision upstream. Fix the stage that makes the decision. One review, at most one correction, then deliver the best candidate.

### 7. "More stages, each with the right context"

What we did: split the monolith into intent, data, select, build, critique, eval; then added planning, scaffolding and correction paths. Handoffs were strict JSON until cheap models broke on JSON, then markdown plus a routing block.

What happened: 8-15 sequential model calls, each re-reading long contexts, around 200k tokens a chart. A cheap model called fifteen times is neither cheap nor fast. Every new stage was also a new seam.

Don't: add a stage, a model call or a contract without stating its cost in calls, latency and tokens, and without an eval number showing it pays for itself. Measure cost per chart, not cost per token.

### 8. "Write down the decisions so they don't get reversed"

What we did: a locked-decisions table, a 3,600-line auto-generated change history, a "historical check" before any idea or bugfix, a pre-edit compatibility note, a guardrail script. The site's CLAUDE.md said in bold: "Fix the failure class, not the single case in front of you. Overfitting to one test case is the main source of the round-and-round regressions."

What happened: it regressed anyway. Every session re-read 12,000 lines of rationale before touching anything, iteration slowed down, and the rule against overfitting sat at the top of the file while the overfitting continued underneath it.

Don't: rely on rules documents to prevent regressions. A written warning against overfitting does not stop overfitting. A fixed eval set with a side-by-side page and a "worse means revert" rule does.

### 9. "The canonical cases are the target"

What we did: seven canonical charts were the test for every change, rerun after every fix, with case 07 eventually removed from the corpus.

What happened: the system got tuned to those seven charts. A fix that helped case 3 was judged on case 3. Chasing one input until it looked right was the normal mode of work.

Don't: treat a small eval set as the target. Check a change on an unlike case before calling it general. After one general hypothesis has been tried and the case still fails, record the fault and stop. Come back when there is broader evidence.

### 10. "The product pipeline can tune the shared skills"

What we did: the repair pipeline's needs leaked into the general skills. The selector picked up "a form that merely appears in a source image is not a request". Skills referred to private harness tools as if every reader had them. On 30 September Chart Doctor's own edits to the canonical skills had to be reverted.

What happened: the skills are published for other people, in other harnesses. Wording written for one pipeline confused everyone else and coupled the two repos so a change in either broke the other.

Don't: put workflow-specific wording (repair, source image, a stage name, a private tool) in a generic skill. It goes in the workflow's own skill or prompt wrapper. Product repos read the skills; they don't write them.

### 11. "Cheap model is the constraint"

What we did: treated "use a cheap model" as fixed, and compensated for its weaknesses with everything above.

What happened: the real constraint was cost per chart. Chart Doctor spends on a good vision model for the read (the one step nothing downstream can repair) and uses cheap models elsewhere, and comes in under two cents.

Don't: confuse the price of a token with the cost of a result. Spend where the error can't be fixed later.

## Warning signs

Any of these means the loop has started again. Stop and look before the next change.

- A commit message or DEVLOG entry names a specific chart, case number or dataset as the reason for a rule
- A skill gets noticeably longer in a week. Check word counts against the last version you were happy with
- A new rule carries a number (a count, a ratio, "roughly ten or more periods") that came from the chart that prompted it
- A rule is promoted, bolded, repeated or marked mandatory because it "isn't binding"
- A new MCP tool does something the renderer or a plotting library already does
- A new stage, gate or model call, with no before/after eval number
- Restore, revert and preserve commits are a growing share of the history
- An agent's work log says "kept general, not overfit" without saying what unlike case it was checked on
- A generic skill mentions repair, a source image, a pipeline stage or a private tool
- The process docs an agent must read before a bugfix are longer than the code it will change

## Before adding a rule, tool or stage

1. Would this exist if the chart that prompted it had never been made? If not, don't add it.
2. Is there an existing rule this replaces? Remove that one in the same change.
3. Does the renderer, the theme or an existing helper already do this? If so, find what is overriding it.
4. What does it cost in words, calls, latency or tokens?
5. Which unlike case did it help or leave unchanged? If none was checked, it isn't shown to be general.
6. If the eval page gets worse, revert. Don't patch the patch.

## What worked

For balance, the things that did hold up:

- **Taste in the theme, not the pipeline.** Chart Doctor's `kd.R` sets the house look globally, so a script that forgets the theme still looks right. A default a model never sees can't be got wrong.
- **Markdown between models.** Code parses only the few values it branches on.
- **Precision and colour as tools.** These are things the renderer genuinely has no built-in for, which is why they survived the cut to two tools.
- **An eval page you look at.** Side-by-side charts are harder to argue with than a locked-decisions table.
- **Delivering the best candidate, not the latest.** A fix is a gamble; the draft stays in the running.
- **Logging an open fault instead of tuning.** Chart Doctor's October entries record unresolved faults and leave them until there is broader evidence.

## Things to watch in Chart Doctor now

The rebuild is small, but some of the same patterns are already visible:

- `R/kd.R` went from 218 lines to 806 in its first three days, one helper per recurring bug. Each helper is defensible. Watch the total.
- `prompts/decisions.toml` gives the decision model numeric thresholds ("roughly ten or more periods", "roughly 5x or more", "up to about 12 categories"). These were added to fix specific coin-toss answers, which is exactly how rule 2 above started.
- The `total_and_breakdown` form came out of repeated work on the OpenRouter chart. The skills repo judged aggregate-plus-breakdown pairing overfit on 5 October; Chart Doctor still has it as one of twelve forms.
- On 4 October, the day of the skills rollback, about twenty one-line rules were "recovered" from the deleted work as general. The next day the borderline ones were judged overfit too. Recovering rules is the same activity as adding them, and needs the same test.

# Design note: the dataviz-fix repair flow

This note records *why* the repair flow is shaped the way it is. For the step-by-step
how-to, see [`../skills/dataviz-fix.md`](../skills/dataviz-fix.md).

## The problem we were fixing

An earlier version ran a full maker-checker loop on every repair:

```
critique → contract → build → render → independent dataviz-eval →
revise → render → independent dataviz-eval → ... → user review
```

It was correct but slow - iterations took ~15 minutes each - so the independent
`dataviz-eval` loop was removed for speed. That swung too far the other way: the fast
path did one self-critique and delivered, which regressed in some cases (misleading
charts slipping through, edits applied to one panel but not its siblings) and stayed
"too respectful of the input image" - repairing the given chart rather than redesigning
when redesign was the right answer.

This flow is the middle ground: fast by default, with independence recovered at a
bounded, one-time cost.

## The insight that unlocked it: a skill is not a session

Invoking a skill (the `Skill` tool) **loads its instructions into the current chat**. It is
the same model, same context window, same conversation - like opening a checklist, not
hiring a second person. Running `dataviz-critique` costs nothing beyond reading a markdown
file and following it.

A **subagent** (the `Agent`/`Task` tool) is a genuinely separate LLM session: cold start,
re-reads the skill, re-inspects the artifact from zero, returns a single report.

The 15-minute iterations were not caused by "having a checker". They were caused by
spawning an **independent `dataviz-eval` subagent on every loop turn**. Each turn re-paid
the cold-start cost. Kill the repeated spawn and the loop collapses to seconds.

## critique vs eval - two different tools

| | `dataviz-critique` | `dataviz-eval` |
| --- | --- | --- |
| Mechanism | instructions loaded into the current chat | separate subagent session |
| Independence | none (same context that built the chart) | true blind read (maker ≠ checker) |
| Cost | cheap, repeatable | expensive cold start |
| Role in this flow | source diagnosis + in-context checker loop | one blind read on the converged candidate |

The corollary that decides everything: **the value of eval's blind read exists only because
the reviewer is a separate context.** Running eval "in the same chat" to save the spawn cost
is pointless - the reviewer already knows the maker's intent, the claimed fixes, and the
code, so the blindness is gone and you are left with heavy ceremony and no independence.
So eval is only ever an independent subagent, and it is only worth spawning once.

A same-session checker catches **mechanical** regressions well (clipping, dropped labels,
wrong units) but **conceptual** blind spots poorly: if the maker misread the chart's message
while building, it will likely misread it the same way while checking. The single independent
eval is exactly what closes that gap.

## The rule: one chat, one spawn

- The default path runs entirely in one chat: source critique, reconstruction, and the
  export checker loop are all the same model reading different instruction files.
- Exactly **one** subagent is spawned per flow - a blind `dataviz-eval` on the converged
  candidate. Never in a loop, never re-spawned.
- The in-context checker loop is capped at **two passes** and exits as soon as no fatal or
  major defect remains. A hard cap is what makes "bounded" real; without it, loop-exit
  depends on the model deciding it is done, which is how the flow wandered before.

## Image not sacred, prompt authoritative

Two separate fidelity questions were being conflated:

- The **input image** is not sacred. If a different form serves the question better, redesign
  it. The critique step biases toward redesign rather than treating it as the exception.
- The **prompt** is authoritative. Anything the user states with the image - requested chart
  type, annotations, what to fix, wording, brand or style preferences - is a requirement that
  must survive the whole process. When a redesign impulse conflicts with the prompt, the
  prompt wins.

Preserving the source's *value* is separate from being faithful to its *form*, and it is a
judgment, not a keep-everything rule. The critique reads the source and decides the key
messages the chart must carry, the content each message requires, and - named explicitly, with
a reason - any information judged *not* key. The rebuild then carries those messages, which may
take more than one chart (a whole plus its parts). What must survive is the messages and their
required content, not every mark. This is owned by the critique and the rebuild step, not by a
later reviewer - which is also why the data inference must produce the full period-by-category
table: you cannot judge what is key without first reading all of it. The failure the flow
guards against (the ten-category stacked chart that came back as a single total) is a *silent*
drop - the breakdown carried a key message and no one decided to lose it. An explicit,
reasoned decision to drop non-key information is fine; silence is the bug.

But a reasoned drop can still use a bad reason, and a later run did exactly that: it dropped
the ten model categories and justified it - "many thin stacked segments and long legend do not
support reliable model-by-model comparison", "without inventing unreadable category precision".
That converted *hard to recover / hard to read* into *not key*. Two guardrails close it. First,
the source's form declares its messages: a stacked, multi-series, or faceted chart has the
category comparison as a key message, so collapsing it to a single total is dropping a key
message, not simplifying. Second, difficulty of recovery is never grounds to drop a dimension -
approximate screenshot values, a crowded legend, "unreadable precision" argue for a *better
form* (small multiples, direct-labelled lines, top-N plus an explicit "other", a share-of-total
view), never for deletion. Source illegibility triggers a redesign of the form; it does not
authorise removing the information.

A consequence of this split: the eval subagent is given the rendered artifact and a brief
(prompt, inferred style, inferred headings, intended message) but **not the source image**.
It judges "does this chart do its job, per the brief", not "does it faithfully match the
original". That also keeps the reviewer from anchoring on the original's choices.

## The flow

```
image + prompt
   │
   ▼
STEP 1  dataviz-critique  (in-context, one pass, no maker-checker)
   • right form? • trifecta • conveys message? (semantic scan)
   • style (installed writing/brand skill, if available)
   • repair vs redesign, biased to redesign
   • key messages + required content per message; drops named out loud
   ├─ parallel: infer full data table (every period × every category)
   ▼
STEP 2  reconstruct
   • carry every key message with its required content; may be
     several charts (whole + parts) - form/decomposition decided here
   • dataviz-selector (default-on unless form clearly right)
   • karthik-data-visualization
   • chart-annotations (invoke when a point may be worth marking;
     the skill judges whether any mark clears the bar)
   • headline + subhead: claim from chart-annotations, style from
     karthik-data-visualization, voice from writing skill (if any)
   • writing/brand skill (if available)
   • honour every prompt constraint; build one artifact
   ▼
STEP 3  in-context checker loop  (dataviz-critique, same chat)
   • ≤2 passes, exit on no fatal/major
   ▼
STEP 4  ONE eval subagent  ← the single spawn
   • blind: artifact + brief only, no source image / intent / code
   • one verdict + findings, never re-spawned
   • SKIP for a purely literal/cosmetic edit
   ▼
STEP 5  ≤1 final revision from eval findings (no re-spawn)
   • expensive redesign → deliver + surface concern to user
   ▼
DELIVER → iterate on real user feedback
```

## Design decisions at a glance

| Decision | Choice | Why |
| --- | --- | --- |
| Checker in the loop | `dataviz-critique`, in-context | cheap, repeatable, no cold start |
| Independent review | `dataviz-eval`, one subagent, once | recovers blindness at bounded cost |
| Loop bound | 2 passes, exit on no fatal/major | makes "bounded" real |
| Eval in-context? | never | in-context eval is ceremony without independence |
| Eval input | artifact + brief, no source image | blind read judged against the brief |
| Input image | redesign freely, bias to redesign | old flow was too faithful to a weak chart |
| Data inference | full period-by-category table, not totals | can't judge what's key without reading all of it |
| What survives | key messages + required content, a critique judgment | preserve value, not every mark; whole-and-parts may be several charts |
| Dropping information | allowed, but named explicitly with a reason | silent drops are the bug; a reasoned drop is fine |
| Who owns preservation | critique + rebuild, not eval | it's a judgment made upstream, not a backstop |
| Prompt | authoritative throughout | user constraints are requirements, not hints |
| Annotation | invoke `chart-annotations`; it judges if a mark is warranted | it had been dropped from the flow; over-annotating is as bad as none |
| Headline/subhead | no dedicated skill; claim ← chart-annotations, style ← karthik-data-viz, voice ← writing skill | the pieces already exist; a new skill would duplicate title-vs-annotation logic |
| Writing/brand skill | conditional, only if installed | not part of this public repo |

## Known tradeoffs

- The default path's checker is not independent, so a maker's conceptual misreading can
  survive the loop. The single eval is the mitigation, but it runs once - a determined
  blind spot the maker and one reviewer both share can still ship.
- Dropping the source image from the eval brief means eval no longer checks
  preservation-against-source. That is intentional here: fidelity is owed to the brief, not
  to the original image.
- A hard two-pass cap can deliver a chart with a known minor residual. That is the deliberate
  "deliver-first" bias; residuals are named in one sentence at delivery.

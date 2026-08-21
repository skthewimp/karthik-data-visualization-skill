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
   ├─ parallel: infer raw data from image
   ▼
STEP 2  reconstruct
   • dataviz-selector (default-on unless form clearly right)
   • karthik-data-visualization
   • chart-annotations (default-on for redesigns)
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
| Prompt | authoritative throughout | user constraints are requirements, not hints |
| Annotation | `chart-annotations` default-on for redesigns | it had been dropped from the flow |
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

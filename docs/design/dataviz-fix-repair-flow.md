# Design note: the dataviz-fix repair flow

This note records *why* the repair flow is shaped the way it is. For the step-by-step
how-to, see [`../skills/dataviz-fix.md`](../skills/dataviz-fix.md).

## The problem we were fixing

The repair flow used to **start by critiquing the source chart**. Critique produced a
diagnosis, the rebuild patched the diagnosed faults, and `dataviz-selector` was only a
conditional downstream helper with an "unless the source form is clearly correct" escape
hatch. That ordering had a gravity to it: everything was anchored on the existing image,
and the path of least resistance was always "re-render the source form, tidied".

For most charts that is fine. For one class it fails, and it failed the same way three
times. The test case was the a16z "Weekly usage of models across OpenRouter" chart - a
stacked bar with ~10 model categories by colour, whose real message is *how each model's
trajectory moves over time*, something no reader can follow through a ten-deep stack.
Three consecutive prose patches to `dataviz-critique` / `dataviz-fix` each fixed the last
symptom and exposed the next:

1. It dropped the 10 categories entirely and returned a single total.
2. It dropped them again, but *with a justification* ("legend crowded", "unreadable
   precision") - turning the mandatory reasoned-drop into a rationalisation.
3. It kept all 10 categories but **re-rendered the same stacked bar** - the exact form
   whose whole problem is that you cannot follow any single model over time.

Each patch was a better sentence. None of them changed the outcome, because all three
traced to one root cause: **the flow started from the source chart.** Prose guardrails
cannot overcome ordering. When the first thing you do is study the existing image, the
existing image wins.

## The fix: repair is forward design, not critique-plus-patch

Stop patching the sentences; change the order. The repair no longer begins with critique.
It begins by extracting *intent* and *data*, chooses a form *cold* from those, builds,
and only then checks.

```
image + prompt
   │
   ├─ STEP 1  INTENT   dataviz-brief   (in-context)
   │     key messages + required content, explicit drops, audience,
   │     story, authoritative constraints, thin keep-notes,
   │     and the edit-vs-redesign MODE
   │
   ├─ STEP 2  DATA     dataviz-extract (in-context, parallel to step 1)
   │     full period-by-category table - every period × every category
   │
   ▼   (mode = redesign)                        (mode = bounded-edit)
STEP 3  SELECT   dataviz-selector, COLD          skip select; stay anchored
   source form gets NO vote                       to the source form
   │
   ▼
STEP 4  BUILD    karthik-data-visualization,      apply the bounded edit to the
   chart-annotations, headline/subhead;           source form; re-render
   may be several charts (whole + parts)
   │
   ▼
STEP 5  CRITIQUE dataviz-critique, downstream CHECKER (in-context, ≤2 passes)
   does the candidate carry the step-1 intent? is it a good chart?
   │
   ▼
STEP 6  EVAL     one blind dataviz-eval subagent  ← the single spawn
   artifact + brief only, no source image; never re-spawned
   (skip for a purely literal/cosmetic edit)
   │
   ▼
STEP 7  ≤1 final revision from eval findings (no re-spawn)
   │
   ▼
DELIVER → iterate on real user feedback
```

The key structural move is **step 3 run cold**. For "10 series over time, compare
trajectories" the selector picks small multiples or direct-labelled lines on its own,
because that is what the data shape and the message want - the stack is not in the room to
argue for itself. The source form gets no vote, so there is nothing for the rebuild to
fall back to.

## Preserve the message, not the form

The principle that makes the cold selection safe: **preserving a message is not preserving
a form.** The data and the messages must survive; the encoding must not, and usually
should not when the source form was the weakness. Three ideas that used to be scattered
guardrails in the critique step are now owned, in order, by the right skill:

- **The source's form declares its messages** (owned by `dataviz-brief`). A stacked,
  multi-series, or faceted chart has the category comparison *as* a key message. This is
  how the brief reads intent *out of* the source - not a reason to keep the source's form.
- **Difficulty of recovery is never grounds to drop a message** (owned by `dataviz-brief`
  and `dataviz-extract`). "Approximate", "crowded legend", "unreadable precision" are facts
  about the source form's weakness; they argue for a better form downstream, never for
  deleting the data. Extraction pulls every cell, approximate-and-labelled where needed.
- **Changing the form is the repair** (owned by `dataviz-selector`, run cold). When the
  source form is the reason a message is hard to read, a tidier version of the same form is
  not a repair. The selector chooses the form the messages want, from scratch.

Because these are now *structural* - the source form is literally not an input to the form
choice - they no longer depend on a paragraph of prose winning an argument against the
image.

## What each skill owns now

| Skill | Old role | New role |
| --- | --- | --- |
| `dataviz-brief` | *(did not exist)* | STEP 1. Extract intent: key messages + required content, drops, audience, story, constraints, keep-notes, edit-vs-redesign mode. Owns "preserve message not form" for the repair. |
| `dataviz-extract` | *(inline in critique)* | STEP 2. Read the full period-by-category table from the image. Vision, not MCP. |
| `dataviz-selector` | conditional downstream helper, with a "clearly correct" escape hatch | STEP 3. The forward-design engine. Runs cold on intent + data; source form gets no vote; no escape hatch in the redesign path. |
| `dataviz-critique` | STEP 1 of repair (source diagnosis + design job) | STEP 5. Downstream checker only: does the candidate carry the brief's intent, and is it a good chart? Standalone "what's wrong with this chart?" use unchanged. |
| `dataviz-eval` | one blind subagent on the converged candidate | Unchanged. STEP 6, the single spawn, artifact + brief, no source image. |

`dataviz-critique` keeps its design *reasoning* (key messages, "form declares its messages",
the difficulty-is-not-a-drop rule) for its **standalone** review path - a user showing a
chart and asking what is wrong. What it loses is the job of being step 1 of a repair. In a
repair, that judgment is made once, up front, by `dataviz-brief`, and critique only checks
against it.

## The edit-vs-redesign fork lives at intent time

Not every repair should reopen the form. "Fix the axis labels", "recolour series 3",
"change the title" are bounded literal edits: the source form is intact and correct, and
redesigning it would be wrong. That fork is decided in **step 1**, as an explicit `mode`
the brief emits:

- **`bounded-edit`** - stay anchored. Skip the cold selection (step 3) and the full data
  extraction; apply the named edit to the source form and re-render. Eval is skipped for a
  purely literal or cosmetic edit.
- **`redesign`** - reopen the form. Run the full forward-design flow. This is the default
  when the request is anything more than a bounded edit, and when in doubt.

Putting the fork in the brief's output (rather than in the orchestrator, or inside the
selector) keeps it next to the signal that decides it: the intent read. A bounded edit that
turns out to need a form change can be widened; a redesign wrongly narrowed to an edit
reproduces the source's weakness.

## The unchanged machinery: one chat, one spawn

The economics that shaped the previous flow still hold, and still explain why five of the
steps run in the current chat and only one spawns.

Invoking a skill (the `Skill` tool) **loads its instructions into the current chat**. It is
the same model, same context window - like opening a checklist, not hiring a second person.
So `dataviz-brief`, `dataviz-extract`, `dataviz-selector`, the build, and the `dataviz-critique`
checker loop are all cheap: same session, different instruction files.

A **subagent** (the `Agent`/`Task` tool) is a genuinely separate LLM session: cold start,
re-reads the skill, re-inspects from zero, returns one report. Its value is *independence* -
a blind reader who does not share the maker's context or blind spots. That value exists only
because the reviewer is a separate context, so eval is only ever an independent subagent, run
**once**, on the converged candidate.

| | `dataviz-critique` (checker) | `dataviz-eval` |
| --- | --- | --- |
| Mechanism | instructions loaded into the current chat | separate subagent session |
| Independence | none (same context that built the chart) | true blind read (maker ≠ checker) |
| Cost | cheap, repeatable | expensive cold start |
| Role | STEP 5 in-context checker loop, ≤2 passes | STEP 6 one blind read on the converged candidate |

A same-session checker catches **mechanical** regressions well (clipping, dropped labels,
wrong units) but **conceptual** blind spots poorly: if the maker misread the message while
building, it will likely misread it the same way while checking. The single independent eval
is what closes that gap. The in-context checker loop is capped at **two passes** and exits as
soon as no fatal or major defect remains; a hard cap is what makes "bounded" real.

Eval is given the rendered artifact and a brief (prompt, inferred style, inferred headings,
intended message) but **not the source image**. It judges "does this chart do its job, per the
brief", not "does it faithfully match the original" - which also keeps it from anchoring on the
original's choices. Fidelity is owed to the brief, not to the source image.

## Image not sacred, prompt authoritative

Two fidelity questions that are easy to conflate:

- The **input image** is not sacred. In the new flow this is enforced structurally: the source
  form is not an input to the form choice at all.
- The **prompt** is authoritative. Anything the user states with the image - requested chart
  type, annotations, what to fix, wording, brand or style preferences - is a requirement that
  must survive the whole process. When a redesign impulse conflicts with the prompt, the prompt
  wins. The brief captures these constraints in step 1 and they are honoured through the build.

## Design decisions at a glance

| Decision | Choice | Why |
| --- | --- | --- |
| Where repair starts | intent + data, not critique | critique-first anchors on the source image; ordering beat prose |
| Form choice | `dataviz-selector`, run cold, source form no vote | removes the "re-render the stack, tidied" default structurally |
| Escape hatch | removed from the redesign path | "unless clearly correct" is how the stack kept coming back |
| Intent ownership | new `dataviz-brief` skill | intent extraction is not critique; cleaner ownership |
| Data ownership | new `dataviz-extract` skill | full period-by-category table, vision, feeds any chosen form |
| Edit-vs-redesign fork | in the brief's output (`mode`) | lives next to the intent read that decides it |
| Critique's role | downstream checker (step 5), standalone unchanged | it stops being step 1; it checks against the brief |
| Independent review | `dataviz-eval`, one subagent, once | recovers blindness at bounded cost |
| Loop bound | 2 passes, exit on no fatal/major | makes "bounded" real |
| Eval input | artifact + brief, no source image | blind read judged against the brief |
| Prompt | authoritative throughout | user constraints are requirements, not hints |

## Known tradeoffs

- The default path's checker is not independent, so a maker's conceptual misreading can
  survive the loop. The single eval is the mitigation, but it runs once.
- A cold form selection can, in principle, discard a source form that genuinely was correct.
  The `bounded-edit` mode and the brief's keep-notes are the guards: a correct form is kept
  when the request is a bounded edit, and reusable source ideas (a smart annotation, a good
  grouping) are carried forward as *ideas*, not as a reason to inherit the form.
- Two new skills add surface to maintain (both `codex` and `claude`). The alternative -
  more prose guardrails inside critique - is exactly what failed three times.
- A hard two-pass cap can deliver a chart with a known minor residual. That is the deliberate
  deliver-first bias; residuals are named in one sentence at delivery.

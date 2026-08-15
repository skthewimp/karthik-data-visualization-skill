# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be rebuilt, reviewed by Karthik, revised until accepted, and then used as evidence for improving the skill stack.

This is the repository's **repair and learning-loop** skill. The other skills choose, style, annotate, critique, or explain a chart. This skill coordinates those capabilities around a real artifact and preserves what Karthik corrected.

## User workflow

1. Paste or upload a chart and invoke `dataviz-fix` with any initial instruction.
2. The agent renders a real chart, sends the exact export to a fresh `dataviz-eval` reviewer, and autonomously fixes bounded failures before showing the candidate.
3. Receive a real regenerated chart, not a critique-only response.
4. Reply naturally with changes such as “keep the chart type”, “make the labels larger”, or “that title overstates the evidence”.
5. Repeat until the chart is right, then say “accept”, “final”, or an equivalent clear phrase.
6. The agent classifies why the first output missed and changes the owning skill only when the lesson generalizes.

Hermes is the first chat interface because Telegram and WhatsApp already support pasted images, session continuity, and returned chart files. The repository also includes a local tester for side-by-side artifacts, editable context, budgets, and one bounded creator/reviewer cycle. A private deployed tester, provider selection, and bring-your-own API keys remain later stages.

## Case packet

Each run is stored under the configured dataviz-fix root and contains:

- the original uploaded chart;
- every rendered iteration;
- the intake change contract, including requested changes and elements that must remain unchanged;
- every independent `dataviz-eval` report, blind read, gate result, release check, failure code, and minimum pass set;
- every context version, including whether each field was user-supplied, inferred, or unknown;
- every loop transition, stopping reason, usage event, configured budget, and preserved best candidate;
- user feedback verbatim;
- hashes of the skill files used at the start;
- the accepted artifact;
- a review packet and skill diagnosis.

The bundled `case_manager.py` script creates and updates these files without overwriting prior artifacts.

## Evaluation gate

`dataviz-eval` is required after every recorded render, and the chart creator cannot review its own work. Hermes first gives a fresh `delegate_task` reviewer only the source and exact export, saves that blind read, and then reveals the user request, audience, medium, and active acceptance checks. The creator's diagnosis, claimed fixes, preferred verdict, and code remain hidden. `Send` releases the candidate to the user. `Revise` applies only the minimum pass set. `Redesign` returns the case to critique or chart selection. `Not evaluable` requires the missing artifact, evidence, or delivery condition before the candidate can be presented as approved.

The repair loop is an explicit state machine. It defaults to three autonomous iterations and can also enforce elapsed-time, token, and dollar limits. It rejects unchanged artifacts under unchanged context, blocks when failure codes and gate results repeat without progress, and preserves the best independently evaluated candidate rather than assuming the last one is best. Every stop has a recorded reason and can resume only after its blocker or budget changes. User feedback can still reject a `Send`, and explicit user acceptance remains authoritative.

Audience, purpose, analytical question, hypothesis, intended message, medium, dimensions, source notes, preservation requirements, and output constraints are versioned inputs. The record distinguishes user-supplied, inferred, and unknown values. A material context change cancels an in-flight stale review or supersedes an old verdict; the same artifact may then be evaluated under the new context. The blind reviewer still sees only source and artifact before context is revealed.

The case manager enforces the sequence. Before the first build, concrete additions, removals, relocations, and preservation requirements become a structured change contract. `start --preserve` creates the preservation check automatically, while `check` records each positive edit. Repeated structures are expanded explicitly: if one key serves two panels, the check states what must appear in each panel rather than accepting one repaired instance. `build-check` stops an exhausted case before another model or renderer call; completed work is still recorded and reviewed when one call crosses its estimate. It accepts only real PNG, JPEG, SVG, or PDF iterations. A render bundle can preserve its chart spec and layout metadata, and `inspect` binds deterministic geometry evidence to the exact iteration before the blind packet is created. The intent reveal does not exist until the reviewer saves and submits its blind response; later changes invalidate the report. It checks different creator and reviewer identities, binds the report to the artifact, inspection, and blind-response hashes, and requires evidence for six gates plus a named worst-case stress test for each of five general release checks. It carries unresolved evaluator actions and every active user acceptance check into the next revealed review, requiring a direct result for each one. Later clarification can explicitly supersede an earlier user check or an evaluator action without deleting history. Evidence, visual reasoning, information fit, and delivery are always required. Question and insight can remain `Unknown` only when the declared scope genuinely does not require them. `Send` requires every required gate, all five checks, every carried action, and every active user check to pass. The checks prescribe outcomes, not chart types, palettes, fixed margins, or pixel thresholds.

Each iteration must be evaluated before another can be recorded. Acceptance normally requires `Send`; explicit user acceptance of a non-`Send` artifact is recorded separately as `accepted_with_override`, with the reason. HTML can generate a chart, but the browser source is not the delivered artifact.

During revision, the creator receives the source plus the latest candidate, continues from the latest generating code, and preserves earlier passes unless the evaluator requested a redesign. For narrow repairs, changed regions must meet the full release standard while untouched regions are checked for preservation and regression. Unchanged pre-existing defects outside the authorized scope are recorded as baseline concerns rather than silently expanding the required edit. The reviewer cannot retain or restore something the user explicitly asked to remove. The reviewer receives the exact export plus deterministic delivery-size and overlapping detail views, so local collisions and mapping errors cannot hide in a clean overview. During the active loop, the agent does not edit skills or send progress-only replies. Each response that claims a chart changed must attach the changed chart. Skill diagnosis and source edits happen only after acceptance.

## Skill-learning rule

Acceptance does not automatically mean “add another rule”. The workflow first classifies the miss:

- **execution miss** - the rule already existed but was not followed;
- **missing rule** - no reusable guidance covered the correction;
- **ambiguous rule** - existing wording allowed the wrong choice;
- **conflicting rule** - two skills pushed in different directions;
- **tooling** - image handling, rendering, inspection, or delivery failed;
- **input data** - the required evidence was absent.

Only missing, ambiguous, or conflicting reusable guidance normally warrants a prose edit. A repeated execution miss instead needs enforcement, observability, or a regression test. A long case is split into distinct failure episodes: each gets one owner, while one case may legitimately change the creator skill, evaluator, and runner for different reasons.

## Hermes installation

On a Hermes host with this repository checked out:

```bash
./sync.sh --no-pull --surface hermes
```

This installs the Claude-compatible skill directories under `~/.hermes/skills/data-science/`. The default `all` install remains Codex plus Claude so local users do not get a new Hermes directory unexpectedly.

# Dataviz repair loop and tester roadmap

The current Hermes workflow can repair a chart, evaluate it, take feedback, and revise it. The next problem is making that loop predictable enough to use repeatedly and safe enough to expose through a web app.

Three things need to be built together. A bounded loop without good context will stop safely but make poor charts. Better context without loop control can still waste tokens indefinitely. A web app without either will simply make the failure easier for more people to reproduce.

## 1. Loop-engineer the repair workflow

Turn the current prompt-driven cycle into an explicit state machine:

```text
intake -> build -> blind review -> context reveal -> verdict ->
revise | redesign | user review | accepted | blocked | stopped
```

TODO:

- [x] Record the current state, artifact hash, context version, verdict, failed gates, cost, and iteration number after every transition.
- [x] Add configurable limits for autonomous revisions, elapsed time, and token or dollar spend. Defaults should come from measured runs, not one arbitrary constant.
- [x] Stop evaluating unchanged artifacts. A reviewer must not create a new cycle when the artifact and context are identical.
- [x] Detect lack of progress: repeated failure codes with no gate movement should pause the loop and ask for human input rather than trigger another cosmetic rewrite.
- [x] Define clean terminal states: evaluator `Send`, explicit user acceptance, user stop, missing evidence or context, exhausted budget, and unrecoverable renderer failure.
- [x] Preserve the best candidate when a loop stops. Do not assume the last candidate is the best one.
- [x] Let the user interrupt at any point with a correction, new constraint, changed intent, or acceptance.
- [x] Persist enough telemetry to compare runs: calls, input/output/cache tokens, cost, latency, revisions, gate movement, and final outcome.

Definition of done:

- No session can loop indefinitely.
- Every stop has a visible reason and a useful next action.
- Repeated evaluation cannot occur without a changed artifact or changed context.
- A stopped run can resume without losing its artifacts, feedback, or best candidate.

## 2. Make purpose and audience first-class inputs

The fixer and evaluator should not treat context as a one-off opening prompt. Context needs to be editable, versioned, and attached to the exact iteration it influenced.

The intake should accept, but not require:

- audience and their likely chart literacy;
- purpose or decision the chart should support;
- analytical question;
- hypothesis;
- intended message, including an honest “no clear pattern” result;
- delivery medium, dimensions, and whether expansion is available;
- source data or source chart;
- facts, wording, ordering, colours, or conventions that must be preserved;
- accessibility, brand, tooling, and output constraints.

TODO:

- [x] Provide a compact structured intake plus an ordinary free-text prompt.
- [x] Show inferred context back to the user instead of silently treating it as fact.
- [x] Distinguish user-supplied, inferred, and unknown fields.
- [x] Allow context to be added or changed between revisions without restarting the case.
- [x] Version the context. An evaluation must identify which context version it used.
- [x] Invalidate an old verdict when a changed audience, purpose, hypothesis, message, or medium changes the pass condition.
- [x] Preserve evaluator blindness: the reviewer sees the source and artifact first, submits the blind read, and only then receives the relevant context version.
- [x] Convert each new user correction into an observable acceptance check while retaining the broader purpose and audience.

Definition of done:

- The same artifact can receive different defensible verdicts under different declared purposes or media, with the reason visible.
- Missing context becomes `Unknown` or a targeted question, not an invented requirement.
- The user can keep prompting naturally while the structured case record remains coherent.

## 3. Build a bring-your-own-key tester

Start locally, then deploy privately, then decide whether a public beta is sensible.

Current state: the local case console is working. It covers upload, context, feedback checks, budgets, state transitions, artifact comparison, stop/resume, and history. An opt-in local runner can execute one ephemeral creator pass and one fresh reviewer pass against the checked-out skills. It does not yet expose raw provider APIs or browser-supplied keys.

Core experience:

- paste, upload, or drag in a chart;
- add or edit audience, purpose, question, hypothesis, message, medium, and constraints;
- run the complete fixer plus independent evaluator loop;
- see the original, current, and best candidate side by side;
- add normal-language feedback and resume from the current state;
- inspect the verdict, failed gates, required changes, iteration history, tokens, and estimated cost;
- accept and download an artifact;
- optionally export a sanitised case packet for improving the skills.

TODO:

- [ ] Build provider adapters for OpenAI, Anthropic, and Google before adding more models.
- [ ] Let users set separate creator and reviewer models.
- [ ] Support bring-your-own API keys without writing keys to logs, analytics, case files, or the application database.
- [ ] Decide whether calls run directly from the browser or through a short-lived backend proxy after testing provider CORS, tool support, and secret-handling constraints.
- [ ] Show a cost estimate before running and enforce a user-set session budget.
- [ ] Isolate rendering and uploaded files per session; define deletion and retention behaviour.
- [ ] Add authentication, rate limiting, file validation, abuse controls, and a threat model before any public deployment.
- [ ] Keep chart data private by default. Sharing a case for skill improvement must be explicit and separable from ordinary use.
- [x] Add a local developer mode that can run against the checked-out skills before deployment.
- [x] Add a small regression suite covering loop termination, context changes, reviewer separation, key leakage, and artifact delivery.

Deployment stages:

1. **Local prototype:** one user, local storage, BYOK, complete state machine.
2. **Private server deployment:** authenticated users, isolated sessions, budgets, and retention controls.
3. **Public beta:** only after the security, abuse, privacy, and cost controls have been tested.

## Build order

1. State machine and stopping conditions.
2. Versioned context intake and mid-loop updates.
3. Telemetry and cost accounting.
4. Local tester UI.
5. Private Hermes deployment.
6. Public BYOK beta, if the private version behaves well.

Do not start with the public app. The loop and context contract are the product; the web interface is how people reach them.

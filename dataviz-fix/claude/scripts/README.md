# dataviz-fix case manager

`case_manager.py` records the original chart, versioned context, revisions, `dataviz-eval` gate results, feedback, state transitions, budgets, usage, best candidate, acceptance, and skill diagnosis for portable repair-loop cases.

Use `check` before the first build to turn each concrete addition, removal, relocation, or preservation requirement into an intake acceptance check. `start --preserve` creates the preservation check automatically. Use `review-request` after every recorded iteration. It creates only a blind packet for a fresh reviewer. Before reveal, the reviewer records narrative reads plus structured readings and uncertainties for all five semantic dimensions. After saving them, that reviewer runs the packet's `blind_submit_command`; `blind-submit` freezes the response and only then creates the intent reveal and final JSON template. Use `evaluate --report` to validate and store the result. The final report must copy the frozen semantic fields unchanged. It also records different creator and reviewer identities, the exact artifact hash, four always-required artifact gates, any other scope-required gates, five general release checks, mandatory colour-distinction and copy-style presentation checks, each check's most failure-prone stress test, failure codes, baseline concerns outside a narrow edit scope, and the minimum pass set. Unresolved evaluator actions and active user acceptance checks are carried into the next revealed review and remain open until that reviewer explicitly passes each named target with direct evidence. `feedback --supersedes` replaces an earlier, contradictory user check; `--supersedes-actions` retires an evaluator action that later user feedback overrides.

Run `semantic-preflight --report` before the first build under each context version. It records measure, time/context, universe/denominator, claim-strength, and audience-unit risks without prescribing a chart-specific solution. `build-check` then runs immediately before any creator or renderer call. It stops an exhausted case before more work starts. `iterate` then preserves the completed PNG, JPEG, SVG, or PDF even if that call crossed a budget; `--bundle-manifest` also preserves matching chart-spec and layout sidecars. Run `inspect --report` before `review-request` to bind deterministic inspection to the same artifact hash. The evaluator must return that inspection hash when it exists. Layout metadata must name that artifact internally, and `Send` cannot override a known high- or medium-severity deterministic defect. `iterate` rejects unchanged artifacts under unchanged context and refuses a new revision until the prior one is evaluated or cancelled by a context change. `context` separates user-supplied, inferred, and unknown audience/purpose fields and binds each iteration and review to one context version. Structured fields passed to `start` default to inferred provenance unless `--context-source user` is explicit. `evaluate` rejects `Send` unless every semantic dimension, required gate, release check, presentation check, carried evaluator action, and active user check passes. Iterations created before schema 13 remain reviewable under their original contract; every new iteration records and enforces the presentation checks.

The explicit states are `build`, `blind_review`, `context_reveal`, `revise`, `redesign`, `user_review`, `blocked`, `stopped`, `accepted`, and `accepted_with_override`. Iteration, elapsed-time, token, and cost budgets stop further builds. Reworded equivalent actions deduplicate under one durable action id, and recurring semantic action/failure signatures block the loop at the configured stall threshold. `status` reports the remaining budget and preserved best candidate. Reading limits or tightening them is unrestricted. Increasing any existing limit requires `limits --authorization GRANT_ID`, where the single-use grant was already recorded against this case from an explicit user turn and approves the exact increased values. A free-text reason cannot create a grant. Every change is audited in `limit_changes`; approved increases link to `limit_authorizations`. A budget stop remains stopped after the increase until a separate `resume`, and only an authorized increase recorded after that stop permits the resume. Recording `evaluate` or reading `status` never reopens a stopped case. `accept` normally requires `Send`; explicit user acceptance of a non-`Send` artifact requires `--override-reason` and produces `accepted_with_override`. `diagnose` also works on stopped or blocked cases so rejected workflows remain learnable without fake acceptance. An `execution-miss` diagnosis is invalid unless it records both a non-prose enforcement mechanism and a regression test.

Example after the active runtime records a user-turn grant:

```bash
python3 case_manager.py limits --case CASE_ID \
  --max-iterations 4 --authorization limit-grant-abc123
python3 case_manager.py resume --case CASE_ID \
  --reason "User approved the recorded bounded increase"
```

Client-specific delivery enforcement belongs in the client integration. This portable runtime records the case state, independent verdict, and exact artifact hash without assuming a particular attachment syntax.

Run the regression suite from the repository root:

```bash
python3 -m unittest discover -s dataviz-fix/tests -v
```

This runtime file is part of the public skill bundle and must remain tracked.

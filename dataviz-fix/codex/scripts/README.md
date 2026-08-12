# dataviz-fix case manager

`case_manager.py` records the original chart, versioned context, revisions, `dataviz-eval` gate results, feedback, state transitions, budgets, usage, best candidate, acceptance, and skill diagnosis for Claude and Hermes repair-loop cases.

Use `review-request` after every recorded iteration. It creates only a blind packet for a fresh reviewer. After saving the pre-intent read, that reviewer runs the packet's `blind_submit_command`; `blind-submit` freezes the response and only then creates the intent reveal and final JSON template. Use `evaluate --report` to validate and store the result. The report records different creator and reviewer identities, the exact artifact hash, the frozen blind response, four always-required artifact gates, any other scope-required gates, five general release checks, each check's most failure-prone stress test, failure codes, and the minimum pass set. Unresolved evaluator actions and active user acceptance checks are carried into the next revealed review and remain open until that reviewer explicitly passes each named target with direct evidence. `feedback --supersedes` replaces an earlier, contradictory check while retaining its history.

Run `build-check` immediately before any creator or renderer call. It stops an exhausted case before more work starts. `iterate` then preserves the completed PNG, JPEG, SVG, or PDF even if that call crossed a budget; it rejects unchanged artifacts under unchanged context and refuses a new revision until the prior one is evaluated or cancelled by a context change. `context` separates user-supplied, inferred, and unknown audience/purpose fields and binds each iteration and review to one context version. `evaluate` rejects `Send` unless every required gate, release check, carried evaluator action, and active user check passes.

The explicit states are `build`, `blind_review`, `context_reveal`, `revise`, `redesign`, `user_review`, `blocked`, `stopped`, `accepted`, and `accepted_with_override`. Iteration, elapsed-time, token, and cost budgets stop further builds. Repeated failure codes without gate movement block the loop. `status` reports the remaining budget and preserved best candidate; `limits`, `stop`, and `resume` make continuation explicit. `accept` normally requires `Send`; explicit user acceptance of a non-`Send` artifact requires `--override-reason` and produces `accepted_with_override`.

Run the regression suite from the repository root:

```bash
python3 -m unittest discover -s dataviz-fix/tests -v
```

This runtime file is part of the public skill bundle and must remain tracked.

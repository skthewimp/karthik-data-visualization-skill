# dataviz-fix case manager

`case_manager.py` records the original chart, revisions, `dataviz-eval` gate results, feedback, acceptance, and skill diagnosis for Claude and Hermes repair-loop cases.

Use `review-request` after every recorded iteration. It creates only a blind packet for a fresh reviewer. After saving the pre-intent read, that reviewer runs the packet's `blind_submit_command`; `blind-submit` freezes the response and only then creates the intent reveal and final JSON template. Use `evaluate --report` to validate and store the result. The report records different creator and reviewer identities, the exact artifact hash, the frozen blind response, four always-required artifact gates, any other scope-required gates, five general release checks, failure codes, and the minimum pass set.

`iterate` accepts only real PNG, JPEG, SVG, or PDF media and refuses a new revision until the prior one has an evaluation. `evaluate` rejects `Send` unless every required gate and release check passes. `accept` normally requires `Send`; explicit user acceptance of a non-`Send` artifact requires `--override-reason` and produces `accepted_with_override`.

This runtime file is part of the public skill bundle and must remain tracked.

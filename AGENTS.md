# Repository instructions

## Maintainer publish rule

Karthik has asked that completed changes in his maintained checkout of this repository be published and deployed without waiting for a separate instruction.

Apply this rule only when all of the following are true:

- the user is Karthik or is acting as the repository maintainer;
- `origin` is `skthewimp/karthik-data-visualization-skill`;
- the checkout is Karthik's maintained working copy.

Third-party clones and forks must not push to Karthik's repository. They should receive the equivalent commands for their own environment instead.

After a requested repository change is complete:

1. Run the relevant tests, `./sync.sh --no-pull --validate-only`, and `git diff --check`. Use the full pytest suite for workflow, runtime, packaging, or dependency changes.
2. Inspect the worktree and stage only the completed task. Preserve unrelated user changes.
3. Fetch before publishing. Do not force-push, reset, or overwrite remote work. Resolve or report divergence instead.
4. Write a conventional commit, push it to GitHub, and verify that the local branch matches its upstream.
Stop and report the concrete blocker if tests fail, the worktree contains ambiguous changes, or the remote cannot fast-forward.

An explicit instruction not to commit or push overrides this default for that task.

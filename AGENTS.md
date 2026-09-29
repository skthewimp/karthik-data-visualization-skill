# Repository instructions

## Keep development proportional

- Start with the affected code and tests. Read historical logs and plans only when needed.
- For prose or skill wording, validate metadata; do not run rendering tests or model evaluations.
- For a localized code fix, run the affected tests (file paths before `-k`, so unrelated modules
  are not collected). Include callers when a shared interface changes.
- Run the full core suite for cross-cutting rendering, inspection, pipeline, packaging, or
  dependency changes, or when the affected scope is unclear. Run optional case-manager/tester
  suites only when their code or dependencies change.
- After checks pass, rerun only if a subsequent edit affects what they checked. Do not add
  wording assertions, duplicate regressions, or live model evaluations to routine edits.
- Keep changes and reporting compact. Fix the general cause without building a new framework.

## Maintainer publish rule

Karthik has asked that completed changes in his maintained checkout of this repository be published without waiting for a separate instruction.

Apply this rule only when all of the following are true:

- the user is Karthik or is acting as the repository maintainer;
- `origin` is `skthewimp/karthik-data-visualization-skill`;
- the checkout is Karthik's maintained working copy.

Third-party clones and forks must not push to Karthik's repository. They should receive the equivalent commands for their own environment instead.

After a requested repository change is complete:

1. Run checks appropriate to the scope above, `./sync.sh --no-pull --validate-only`, and `git diff --check`.
2. Inspect the worktree and stage only the completed task. Preserve unrelated user changes.
3. Fetch before publishing. Do not force-push, reset, or overwrite remote work. Resolve or report divergence instead.
4. Write a conventional commit, push it to GitHub, and verify that the local branch matches its upstream.
Stop and report the concrete blocker if tests fail, the worktree contains ambiguous changes, or the remote cannot fast-forward.

An explicit instruction not to commit or push overrides this default for that task.

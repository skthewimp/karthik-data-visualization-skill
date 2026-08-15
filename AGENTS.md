# Repository instructions

## Maintainer publish and deployment rule

Karthik has asked that completed changes in his maintained checkout of this repository be published and deployed without waiting for a separate instruction.

Apply this rule only when all of the following are true:

- the user is Karthik or is acting as the repository maintainer;
- `origin` is `skthewimp/karthik-data-visualization-skill`;
- the checkout has access to the configured Hermes host through `ssh server`.

Third-party clones and forks must not push to Karthik's repository or attempt to access his Hermes host. They should receive the equivalent commands for their own environment instead.

After a requested repository change is complete:

1. Run the relevant tests, `./sync.sh --no-pull --validate-only`, and `git diff --check`. Use the full pytest suite for workflow, runtime, packaging, or dependency changes.
2. Inspect the worktree and stage only the completed task. Preserve unrelated user changes.
3. Fetch before publishing. Do not force-push, reset, or overwrite remote work. Resolve or report divergence instead.
4. Write a conventional commit, push it to GitHub, and verify that the local branch matches its upstream.
5. Deploy the pushed commit on Hermes with `ssh server`: fast-forward `/home/karthik/apps/karthik-data-visualization-skill`, install the editable package when code or dependencies changed, run `./sync.sh --no-pull --surface hermes`, and run the relevant host tests.
6. Restart `hermes-gateway.service` when MCP code, MCP configuration, skill text, or packaged skill runtime changed. Verify the service is active, the expected commit is checked out, and the `dataviz_mcp` process is running when applicable.

The deployment must use the exact pushed commit. Stop and report the concrete blocker if tests fail, the worktree contains ambiguous changes, the remote cannot fast-forward, or credentials are unavailable.

An explicit instruction not to commit, push, or deploy overrides this default for that task.

# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

The default workflow is output-first:

1. Inspect the source and requested change.
2. Build one real PNG, SVG, or PDF.
3. Inspect the exact export once for clipping, collisions, legibility, missing content, and obvious colour problems.
4. Return the best valid candidate.
5. Revise the latest candidate only while another pass has a concrete benefit.

There is no default candidate count or elapsed-time limit. Stop when the artifact is usable and another pass would be speculative, cosmetic, or unrelated to the request. Losing MCP access or lacking an independent reviewer does not suppress a valid artifact.

`render_and_inspect_chart` is the preferred mechanical path when available. If the MCP tool fails, the agent falls back to a direct local renderer and visual inspection. It must not fabricate metadata or describe incomplete checks as complete.

Independent `dataviz-eval` review is optional. It is a formal audit with a fresh reviewer, blind reads, structured gates, and a `Send`, `Revise`, `Redesign`, or `Not evaluable` verdict. That strictness is useful for high-consequence claims and benchmarks, but harmful as a default repair step: it can block `Send`, add model calls, and create revision loops after a usable artifact already exists.

Use it only when the user requests independent evaluation, when a materially misleading claim may survive visual polish, for consequential redesigns, or for system benchmarks. Its verdict may inform another revision, but it must not suppress the current valid artifact.

The detailed case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default user-facing repair path. It has no iteration limit unless the user supplies one.

User feedback is the main release signal. Continue from the latest candidate, change the smallest relevant part, inspect the named element, and return the changed artifact.

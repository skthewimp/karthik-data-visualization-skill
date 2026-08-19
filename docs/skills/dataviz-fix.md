# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

The default workflow is output-first:

1. Inspect the source and requested change.
2. Run one concise internal critique: comparison, consequential problems, and identification system. Do not fill a fixed issue quota.
3. Build one real PNG, SVG, or PDF.
4. Critique the exact export once for geometry, typography hierarchy, label relationships, and redundant scaffolding.
5. Consolidate the findings into one focused revision pass and return the best valid candidate.

The critique remains inside the creator stage. It does not call a fresh reviewer, create a structured contract, or recurse through approval gates. There is no default candidate count or elapsed-time limit for local rendering corrections. Stop when the artifact is usable and another pass would be speculative, cosmetic, or unrelated to the request. Losing MCP access or lacking an independent reviewer does not suppress a valid artifact.

Typography is judged by hierarchy at delivery size, not only minimum legibility. Secondary text should not compete with data or primary labels. Every identification or scale element must add a distinct reading task such as comparison, estimation, orientation, or context; duplicate scaffolding should be removed.

`render_and_inspect_chart` is the preferred mechanical path when available. The caller supplies dimensions chosen from the comparison, label geometry, and delivery conditions rather than inheriting an aspect ratio from a renderer profile. If the MCP tool fails, the agent falls back to a direct local renderer and visual inspection. It must not fabricate metadata or describe incomplete checks as complete.

Independent `dataviz-eval` review is optional. It is a formal audit with a fresh reviewer, blind reads, structured gates, and a `Send`, `Revise`, `Redesign`, or `Not evaluable` verdict. That strictness is useful for high-consequence claims and benchmarks, but harmful as a default repair step: it can block `Send`, add model calls, and create revision loops after a usable artifact already exists.

Use it only when the user requests independent evaluation, when a materially misleading claim may survive visual polish, for consequential redesigns, or for system benchmarks. Its verdict may inform another revision, but it must not suppress the current valid artifact.

The detailed case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default user-facing repair path. It has no iteration limit unless the user supplies one.

User feedback is the main release signal. Continue from the latest candidate, change the smallest relevant part, inspect the named element, and return the changed artifact.

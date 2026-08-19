# Dataviz Fix

Use `dataviz-fix` when an existing visualization needs to be repaired and returned as a real artifact.

The default workflow is output-first:

1. Inspect the source and requested change.
2. Build one real PNG, SVG, or PDF.
3. Inspect the exact export once for clipping, collisions, legibility, missing content, and obvious colour problems.
4. Return the best valid candidate.
5. Make one more autonomous build only when a major visible defect remains.

The default limit is two candidates or ten elapsed minutes. Reaching the limit, losing MCP access, or lacking an independent reviewer does not suppress a valid artifact. The agent sends the strongest candidate and states the limitation plainly.

`render_and_inspect_chart` is the preferred mechanical path when available. If the MCP tool fails, the agent falls back to a direct local renderer and visual inspection. It must not fabricate metadata or describe incomplete checks as complete.

Independent `dataviz-eval` review is optional. Use it when the user requests it, when a materially misleading claim may survive visual polish, for consequential redesigns, or for system benchmarks. Review informs another revision; it does not block delivery.

The detailed case manager remains available for audit trails, comparison history, benchmarks, and reusable learning records. It is not part of the default user-facing repair path. Its default autonomous iteration budget is two.

User feedback is the main release signal. Continue from the latest candidate, change the smallest relevant part, inspect the named element, and return the changed artifact.

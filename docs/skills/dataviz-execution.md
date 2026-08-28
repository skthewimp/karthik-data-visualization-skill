# Dataviz Execution

The **post-render gate** of the construct process. It receives the built candidate at its delivery size and checks the **rendering, not the idea**. The idea gate already decided the chart is the right chart saying the right thing; this stage decides whether the actual export is clean enough to hand a reader. Judgement here needs the pixels - which is exactly why it runs after build, where the idea gate ran before it.

## What it checks

- **Geometry** - clipping, elements off the canvas, misalignment, overlapping marks or text, label collisions.
- **Association** - every label, value, and annotation tied to the mark it belongs to; no legend round-trips where a direct label would read.
- **Hierarchy and scaffolding** - title/subtitle/emphasis read in order; no duplicated axes or leftover default furniture.
- **Colour** - contrast against the background, series distinguishable, palette surviving grayscale and common colour-vision deficiencies.
- **Precision as displayed** - digits shown match the decided plan; no fabricated or ragged precision.
- **Eraser test** - remove any ink that carries no data, label, or necessary context.

## Flow check, loop, and delivery

Before judging a **redesign** candidate it confirms the build carries a recorded cold form decision; a tidied re-render of the source form with no form choice behind it routes back to `select`. Defects are consolidated into one focused revision and re-inspected; **how many passes to run is the driver's budget, not a fixed number**. If the render reveals the idea is wrong, it routes back to the idea gate rather than patching pixels. It leans on `render_and_inspect_chart` for deterministic geometry, discloses when deterministic inspection is unavailable, and delivers the best valid candidate - reserving `blocked` for a genuine inability to produce any valid artifact. Distinct from `dataviz-critique`, which reviews a chart standalone. The exact fields are `dataviz_mcp/stage_contracts.py:EXECUTION_SCHEMA`.

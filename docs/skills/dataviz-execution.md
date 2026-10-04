# Dataviz Execution

The **post-render gate** of the construct process. It receives the built candidate at its delivery size and checks the **rendering, not the idea**. The idea gate already decided the chart is the right chart saying the right thing; this stage decides whether the actual export is clean enough to hand a reader. Judgement here needs the pixels - which is exactly why it runs after build, where the idea gate ran before it. It looks at the export two ways in the same review: element by element for rendering defects, and stepped back as a whole picture for composition.

## What it checks

- **Geometry** - clipping, elements off the canvas, misalignment, overlapping marks or text, label collisions. A clipping title/subtitle wraps to the frame; crowded axis tick labels are thinned/rotated/reformatted (equal-spaced on an ordered axis), not left overlapping; a category-label band eating an outsized share of the plot width (long horizontal-bar y-axis names pushing the marks into a thin strip) is wrapped to a capped band (`str_wrap` to `wrap_y_labels_chars`, overflow stacking into taller rows) so the panel keeps the width - all build fixes, not canvas growth. An inverted value/ordered axis (marks reading opposite to the data) is a graphical-integrity defect: route back, don't polish.
- **Association** - every label, value, and annotation tied to the mark it belongs to; no legend round-trips where a direct label would read.
- **Hierarchy and scaffolding** - title/subtitle/emphasis read in order; no duplicated axes or leftover default furniture. A subtitle earns its place only by adding a fact the title doesn't carry. Any note about the chart's making ("approximate", "reconstructed", "not shown in the source") is removed from every reader-facing text block; limitations go in `residual_limitations`, the run report. Qualifications about the data's world (projected, provisional, excludes X, the source's own caveat) are content and stay.
- **Colour** - contrast against the background, series distinguishable, palette surviving grayscale and common colour-vision deficiencies. Judged by what the reader must read and tell apart at delivery size, not by preferred styling.
- **Precision as displayed** - digits shown match the decided plan; no fabricated or ragged precision.
- **Eraser test** - remove any ink that carries no data, label, or necessary context.

## Composition

Five questions about the whole image at delivery size, walked in order:

- **What is seen first?** The eye should land on the focal mark or claim, not a gridline, a legend, a box, or nothing in particular.
- **Is anything competing with it?** Exactly one thing pops; everything else is demoted to quiet context.
- **Does every box, rule, colour, and bold phrase earn its place?** Styling that does not encode, separate, group, or emphasise comes off.
- **Is whitespace grouping information, or merely filling the frame?**
- **Does it look composed at delivery size, rather than styled default output?** A boxed corner legend, a full grid, equal weight across series, a mechanical title, and the stock palette are the tells.

A composition fix is required only when it changes what reads first or removes something competing with the subject; a restyle that leaves the first read unchanged is optional polish. There is no fixed emphasis count or banned-furniture list.

## Flags are evidence

A finding is fatal or major only when it names the reading it breaks - a misread, text unreadable at delivery size, a comparison made needlessly hard. A preferred colour, a contrast that already passes or an uncontested emphasis is minor polish and stays out of the correction.

## One review, one correction, one verification

The gate runs once through, not two loops back to back. Before judging a **redesign** candidate it confirms the build carries a recorded cold form decision; a tidied re-render of the source form with no form choice behind it routes back to `select`. Then **one review** looks at the export both element-by-element for rendering defects and stepped-back for composition (the five questions above, in that same review, not after the defects are clean), naming every consequential rendering defect and composition problem together in `findings`; **one correction** makes those fixes directly in the chart code as a short numbered list, touching nothing else; and one **verification** look confirms each fix landed, nothing nearby broke, picks the better version, and stops. Folding composition into the one review is what stops the old two-loop ping-pong (a composition fix reopening a geometry defect after the defect budget was already spent). The budget is fixed: one review, at most one correction and re-render, then deliver. If the render reveals the idea is wrong, it routes back to the idea gate rather than patching pixels. It checks the export by eye at delivery size and delivers the best valid candidate - reserving `blocked` for a genuine inability to produce any valid artifact. Distinct from `dataviz-critique`, which reviews a chart standalone.

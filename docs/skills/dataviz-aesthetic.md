# Dataviz Aesthetic

The **composition gate** of the construct process. It runs after the chart is built and after the execution gate has cleared the rendering defects, and it asks a different question with a different lens: not "is any element wrong" but "does the whole thing read as one composed, premium image, or like styled default output with the finding buried in it".

## Not the same as `dataviz-execution`

`dataviz-execution` hunts defects element by element - clipping, overlap, label-to-mark association, precision, colour contrast, CVD and grayscale survival. This gate does the opposite move: step back and look at the whole export at delivery size as a picture, before reading any single label. Most of what makes a chart look cheap is invisible up close and obvious from a step back. The two gates do not re-check each other's territory: aesthetic assumes the defects are already clean and never re-runs the geometry or colour checks.

## The five questions

- **What is seen first?** The eye should land on the thing the chart is about - the focal mark, the claim, the span that carries the finding - not on a gridline, a legend, a box, or nothing in particular.
- **Is anything competing with it?** A premium chart has exactly one thing that pops. Demote everything that is not the subject to quiet context.
- **Does every box, rule, colour, and bold phrase earn its place?** The eraser test at the composition level: styling that does not encode, separate, group, or emphasise comes off.
- **Is whitespace grouping information, or merely filling the frame?** Whitespace should bind related elements, separate unrelated ones, or create emphasis - not sit as even gaps or an unused margin.
- **Does it look composed at delivery size, rather than styled default output?** A boxed corner legend, a full grid, equal weight across every series, a mechanical title, the stock palette and typeface are the tells of a defaulted chart.

## Verdict and handoff

Returns a short composition read - the intended subject, what actually reads first, the elements competing or unearned, and the whitespace verb for each region - and routes concrete composition fixes back to build, the same way the execution gate routes defects. It does not re-plot; it names what a re-plot must change to look premium. There is no required emphasis count, banned-furniture list, or universal palette - the principle is one held emphasis and no unearned ink, applied to what the chart is trying to do.

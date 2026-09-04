---
name: dataviz-aesthetic
description: Post-render composition gate - does the finished chart read as one premium, composed image (first read, single emphasis, earned ink, intentional whitespace) rather than styled default output.
---

# Dataviz Aesthetic

The **composition gate**. It runs after the chart is built and the execution gate has cleared the defects, asking a different question with a different lens: not "is any element wrong" but "does the whole thing read as one composed, premium image, or like styled default output with the finding buried in it".

Execution hunts element by element. This gate does the opposite: **step back and look at the whole export at delivery size as a picture**, before reading any single label. Most of what makes a chart look cheap is invisible up close and obvious from a step back.

## Keep the roles separate

- `dataviz-execution` owns rendering **defects**: clipping, overlap, label-to-mark association,
  precision as displayed, colour contrast, CVD and grayscale survival. This gate never re-checks
  those - it assumes they are already clean.
- `dataviz-eval` owns the **send / revise / redesign** decision and semantic meaning.
- `dataviz-critique` reviews a chart standalone and proposes alternative forms.
- This gate owns **composition**: what the reader sees first, whether anything competes with it,
  whether every mark of decoration earns its place, whether whitespace is doing a job, and
  whether the result looks composed rather than defaulted. It sends composition fixes back to
  build; it does not rebuild the chart itself.

## The one move

Look at the finished export at its real delivery size - a thumbnail, a squint, or a grayscale
copy all force the same thing: they strip the detail and leave only the composition. Then walk
the five questions in order. Each is a judgement about the whole image, not a measurement.

## The five questions

1. **What is seen first?** Track where the eye actually lands on the first glance. It should land
   on the thing the chart is about - the focal mark, the claim, the one span that carries the
   finding. If the eye lands on a gridline, a legend, a box, the title bar, or nothing in
   particular, the composition has no subject and reads as generic. Name the intended focal
   element; if it is not what you saw first, the fix is contrast, size, position, or colour on
   that element - not more labels elsewhere.

2. **Is anything competing with it?** A premium chart has exactly one thing that pops. If two
   marks, two colours, two bold phrases, or a loud gridline and the focal mark all fight to be
   seen first, the reader searches instead of seeing, and the image reads as busy. Demote
   everything that is not the subject to quiet context (grey, thin, small). One emphasis, held.

3. **Does every box, rule, colour, and bold phrase earn its place?** This is the eraser test at
   the composition level, not the ink level: not "is this pixel data" but "does this styling
   decision carry meaning or just fill the design". A border around the plot, a coloured header
   band, a second accent colour, a bold subtitle, a drop shadow, alternating row fills - each
   must do a job (encode, separate, group, or emphasise) or come off. Decoration that is only
   there to look designed is what makes a chart look undesigned.

4. **Is whitespace grouping information, or merely filling the frame?** Whitespace should do one
   of three jobs: bind related elements, separate unrelated ones, or create emphasis around the
   subject. Even gaps everywhere, or a large blank margin no element uses, or a title floating
   far from its plot - these are whitespace that fills rather than composes. Tighten related
   elements together and open space deliberately around the one thing that matters.

5. **Does it look composed at delivery size, rather than styled default output?** The tells of a
   defaulted chart: a boxed legend in the corner, a full grid behind every mark, equal visual
   weight across every series, a mechanical title describing the axes, evenly-spaced everything,
   the library's stock palette and typeface. A composed chart looks like a decision was made
   about where the reader's attention goes. If the export could be any chart from any dataset,
   it has not been composed for this one.

## Verdict and handoff

Return a short composition read: the intended subject, what actually reads first, the specific
elements competing or unearned, and the whitespace verb (grouping / separating / emphasising /
merely filling) for each region that matters. Route concrete fixes back to build - "demote the
second series to grey", "drop the plot border and the gridlines", "move the claim onto the focal
mark", "pull the subtitle up under the title" - the same way the execution gate routes defects.
This gate does not re-plot; it names what a re-plot must change to look premium.

If the composition is already clean - one clear subject, nothing competing, no unearned
decoration, whitespace working, looks composed - say so and pass. A restrained chart that reads
in one glance is the target, not a busier one.

## No fixed recipe

There is no required number of emphasis elements, no banned list of chart furniture, no universal
palette. A dense small-multiples grid, a single big number, and a slopegraph each compose
differently. Apply the five questions to what this chart is trying to do; the principle is one
held emphasis and no unearned ink, not a fixed count.

# Karthik R Code Style Skill

`karthik-r-code-style` governs the *layout* of R code - line breaks, indentation, bracket expansion, assignment direction, spacing. It is the skill that makes generated R look hand-written rather than machine-packed.

Most LLM R comes out on long horizontal lines: a whole pipeline on one line, a `summarise()` with six arguments crammed between one pair of parentheses. Karthik's R breaks vertically. Each step is its own line, so a chain can be selected and run top to bottom while exploring. This skill encodes that break pattern.

It is deliberately narrow. It does not choose idioms (tidyverse over base R), does not sequence an analysis, does not design a chart. Those are `karthik-r-analysis-style` and `karthik-data-visualization`. Layout is all this one does.

## Trigger examples

```text
Write me the R for this in my style.
```

```text
Format this R the way I like it.
```

```text
Build a notebook to explore this data.   (with karthik-r-analysis-style)
```

## What it is strict about

**One pipe per line.** Every `%>%` or `|>` ends its line; the next verb is indented two spaces under the source object.

**Right-assigned pipelines.** A chain that builds a named object ends in `-> name`, dropping the arrow to its own line when the last line is long. `<-` is kept for short non-pipeline assignments.

**Expanded multi-argument calls.** A call with a real argument list opens `(` at line end, one argument per line, closing `)` on its own line. Trivial calls (`n()`, `select(a, b)`) stay inline.

**`+` per line in ggplot.** Each layer ends with `+`; the next layer is a new indented line.

**Two-space nested indentation and modern spacing.** Space after commas, spaces around `=` and operators. The cramped no-space style of the pre-2016 base-R files on disk is not copied.

**New code only.** It shapes R you generate now. It does not rewrite Karthik's existing hand-written files into a house style.

## Boundaries

`karthik-r-analysis-style` owns idiom and notebook structure - use both together for a notebook. `karthik-data-visualization` takes over when an exploratory plot becomes a finished chart.

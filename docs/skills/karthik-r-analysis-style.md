# Karthik R Analysis Style Skill

`karthik-r-analysis-style` governs how an R analysis file is written - the exploratory scratchpad, the RMarkdown or Quarto notebook, the thing you open when a dataset lands and you want to know what is in it.

Most of the other skills in this repo act on a chart or a question. This one acts on the file. It decides how probes are sequenced, what the working notes sound like, which idioms to reach for, and what the notebook must not turn into.

## Trigger examples

```text
Build a notebook to explore this dataset.
```

```text
Make me a scratchpad for the ticketing data.
```

```text
Why does this analysis read like a generated report?
```

## What it is strict about

**Analyst posture, not software engineering.** The notebook is a thinking surface. It does not get a config section, a pipeline abstraction, or reusable functions written before there is a second use.

**Local precedent first.** Before writing a new scratchpad, the skill searches the notebooks already on disk and inherits their shape. This is what keeps twenty notebooks looking like one person wrote them.

**Rough working notes.** `Too messy. Try the recent period.` and `This is probably a dead end` are the register. `Executive Summary`, `Key Takeaways`, `Data Quality Assessment` and any standing framework are banned outright unless asked for.

**A note after every plot, not just before it.** The skill's own note examples are all lead-ins - what you are about to look at. Since whoever reads the notebook did not run it, every plot also needs a note saying what it showed. That wording is delegated to `chart-explainer` rather than duplicated here, including its rule that most exploratory plots show nothing and the note should say so.

**tidyverse/tidytable, not base R.** With explicit routing to dbplyr, Arrow, or DuckDB when the data will not sit in memory.

**No raw SQL.** Database and large-data access goes through dplyr backends - `dbplyr`, `duckplyr`/DuckDB, `arrow` - never hand-written `SELECT`/`GROUP BY`/join strings. The only exception is an unavoidable one-off DDL/config statement with no dplyr equivalent.

**Right assignment in long chains.** New long pipes end in `->` so they can be run partially, line by line, while exploring. Old notebooks' assignment style is left untouched.

**For running, never knitting.** The notebook assumes every chunk is executed one at a time in the console. Nothing that only serves a knitted output - `knitr::opts_chunk$set`, figure sizing/captions, cross-references, knit-ready structure - is added.

## References

`references/` ships inside each surface directory because `SKILL.md` reads it at runtime:

- `empirical-posterior.md` and `style-observations.md` - what the 2018-onward notebooks actually do, distilled.
- `iterative-learning-20.md` - the sequential twenty-step audit behind the current rules.
- `behavioral-forward-tests-20.md` - forward tests against twenty unseen notebooks.

## Boundaries

`karthik-data-cleaning` runs inside these notebooks when the source needs work. `karthik-analysis-planner` runs before them when the question is still fuzzy. `karthik-data-visualization` takes over when a quick exploratory plot has to become a finished chart. `chart-explainer` owns the note under each plot.

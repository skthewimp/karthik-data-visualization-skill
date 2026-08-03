---
name: karthik-r-analysis-style
description: >-
  Use for Karthik-style R analysis, exploratory RMarkdown/Quarto notebooks, and analytics pipelines: local-precedent-driven scratchpads, question-led probes, tidyverse/tidytable code, quick tables/plots, domain-informed branching, dbplyr/Arrow/DuckDB for larger data, and RStudio-friendly notebooks.
metadata:
  claude-description: "Karthik-style R analysis: local-precedent scratchpads, analyst-first probes, tidyverse/tidytable, quick plots, domain branching."
---

# Karthik R Analysis Style

Use for R analysis, exploratory `.Rmd` / `.qmd` notebooks, and analytics pipelines. Core rule: this is not generic EDA and not a polished report. It is a working scratchpad where the next chunk follows from what the previous chunk showed.

## Analyst, not software engineer

This skill follows the same philosophy as Karthik's data-cleaning skill: analyze with context, not with software-engineering tidiness.

Treat an exploratory notebook as thinking in public with data. The goal is judgement, not architecture. Prefer context-specific probes, visible assumptions, and domain reasoning over reusable machinery.

Do:

- Start from the analytical question and unit of analysis, not from a code structure.
- Let messy facts change the next step.
- Keep local, disposable objects if they help thinking.
- Use domain names and metrics even if they are not perfectly generalized.
- Clean or transform only what helps answer the next question.
- Keep caveats near the chunk that revealed them.

Do not:

- Turn exploration into a package, framework, pipeline, or software component.
- Abstract too early into functions, configs, classes, helpers, tests, or generic loaders.
- Optimize for reproducible production code before understanding the data.
- Hide judgement behind generic verbs like `clean_data()`, `process_data()`, `run_analysis()`.
- Make the notebook look tidy at the cost of losing the reasoning trail.

A good notebook can be a little ugly if it shows the analyst's path. A bad notebook is clean, generic, and context-free.

## Empirical posterior from 2018+ notebooks

A 20-notebook audit across Mint, Shopify, Retail, Oliveboard, Ticketing, Onsite, elections, weather, payments, JEE, BabbageInsight, qcom/Cosmix, and cricket updated the prior this way:

- Start from a live context: article, client problem, stakeholder need, product idea, or personal curiosity. A concrete objective is fine; a generic EDA preamble is not.
- The unit of analysis is usually implicit in the first few chunks. Make it visible when creating new work: order, item, store-day, candidate-seat, ball, innings, match, user-test, hour-day, app-city-SKU.
- Broad metric scans are allowed only when the business/client context calls for them. They should still be metric-led (`GMV`, `AOV`, `DAU`, `coupon burn`, `availability`, `search visibility`), not column-led.
- Rough prose is a feature, not a bug. Typos, fragments, “Not as interesting!”, “Nothing significant”, “What is this column?” are closer than polished paragraphs.
- Sparse notebooks are fine. Not every chunk needs prose. But every sequence should reveal why that cut came next.
- Modeling/simulation/clustering is acceptable when it is the natural analyst move: swing simulator, structural break test, clustering questions/users, forecast need, player impact. Do not add models because EDA templates say so.
- Exports (`pdf`, `pbcopy`, saved chart) appear when feeding an article/client output. Do not add them otherwise.
- Some newer client/data-access notebooks have setup/query sections for DuckDB/S3/Parquet. Copy that only when the data source requires it; do not generalize it into framework boilerplate.

If evidence conflicts, prefer older hand-written notebooks for voice and reasoning; prefer newer notebooks for current data-access patterns.

## Sequential learning rule for improving this skill

When updating this skill from Karthik's old notebooks, do not batch-read examples and summarize once. Use a sequential posterior update:

```text
prior skill → inspect file 1 → write delta → update working belief → choose/read file 2 in light of that belief → ... → final skill patch
```

After each file, record:

- what the current skill would have predicted
- what the notebook actually does
- what belief should become stronger, weaker, or more conditional
- what kind of future notebook this evidence applies to

This matters because Karthik's style is not one global template. It is a family of analyst behaviours: article scratchpad, client metric scan, data diagnostic, model experiment, chart hunt, and personal curiosity notebook. Later files should refine or qualify earlier conclusions, not merely add examples.

## First move: RAG against local precedent

Before creating or heavily editing a notebook, retrieve local examples and update your plan from them. Treat the current skill as the prior and nearby notebooks as evidence.

Inspect 3-5 notebooks before writing:

1. Same folder/project.
2. Same domain: cricket, elections, commerce/client, weather, time series, survey, etc.
3. Older hand-written notebooks from 2018 onward if recent files look AI-generated or over-structured.
4. One adjacent “bad fit” file if useful, to avoid copying the wrong mode.

For each example, ask: what is the question/context, grain, first inspection, branch logic, code texture, and stopping point? Then write the new notebook in the posterior style. Do not invent a new workflow if the repo already has one.

Copy texture, not just syntax: roughness, local object names, domain metrics, assignment style, plot roughness, section rhythm, willingness to abandon paths.

Good exemplars to search when relevant:

- `Clover/basic analytics.Rmd` for client/order exploration.
- `data_work/bangalore/weather/scratchpad.Rmd` for weather scratchpads.
- `elections/legacy/_flat_compat/karnataka analysis 2023.Rmd` for elections/simulation/maps.
- `cricket/odis/number4.Rmd` and other old cricket notebooks for cricket story analysis.
- `qcom/cosmix/explore_cosmix_june.Rmd` for modern client scratchpad with joined data sources.
- `BabbageInsight/SingleTimeSeries/new_explorations.qmd` for rough hypothesis-testing notebooks.

Read `references/style-observations.md` only when matching old notebooks closely or when examples are unclear.

## Notebook family routing

Before writing, classify the notebook family. This prevents one Karthik pattern from being over-applied to all work.

- **Article/story scratchpad:** one claim or curiosity; rough prose; quick tables/plots; export only if feeding article/chart.
- **Client diagnostic:** stakeholder problem list, source-of-truth decisions, metric definitions, criteria scoring, business-native cuts.
- **Metric scan:** broad scan is allowed only when metrics are domain-native (`GMV`, `AOV`, `DAU`, conversion, burn, incidence, active plans), not generic columns.
- **Forecast/model calibration:** functions and repeated evaluation are allowed; keep the analyst reasoning about bias, seasonality, holdout, ratios, and horizons visible.
- **Algorithm/product experiment:** end-to-end functions are allowed when designing an algorithm (dynamic pricing, Elo, structural breaks, parsers). Still explain assumptions and check intermediate objects.
- **Text/NLP parsing notebook:** helper functions are normal for parsing lines/messages/documents. Still inspect raw lines and samples before abstraction.
- **Chart recreation/graphic hunt:** start from target visual/question; iterate aesthetics and anomalies; export only when output is the point.
- **Tracker/dashboard-ish notebook:** repeated charts/maps are okay; preserve update logic and assumptions, but do not turn it into a generic app unless asked.

If a precedent file is just RStudio template boilerplate or generic AI-generated sections, treat it as negative evidence. Do not copy its prose or structure.

## Mental model

Write like Karthik at the console:

1. Load data.
2. Print the object.
3. Ask one narrow question in plain English.
4. Run one short table or plot.
5. React: too messy, no signal, weird, useful, dead end.
6. Change slice/grain/benchmark because of what appeared.

The notebook earns its keep by choosing what to look at next. It does not earn its keep by being comprehensive.

## Notebook shape

Default exploratory `.Rmd`:

```yaml
---
title: "Concrete title"
output: html_notebook
---
```

Then usually:

```r
require(tidyverse)
require(lubridate)   # if dates matter
require(tidytable)   # if grouped summaries get compact
```

Rules:

- Use absolute paths or `setwd()` when RStudio chunk-by-chunk execution needs it.
- Keep chunks short. One chunk = one thought/probe.
- Print raw objects early: dataframe, `head()`, `count()`, `summary()`.
- Use section titles/prose as steering notes, not formal report copy.
- Leave dead ends if they explain the next move.
- Reassign objects freely in scratchpads when cleaning step is local and obvious.
- Do not add YAML author/date, setup boilerplate, `knitr::opts_chunk$set`, global config, or package abstraction unless local precedent does it or user asked.

## Prose style inside notebooks

Use rough working notes. Examples:

- `What does this file look like?`
- `Need a quick size check first`
- `Date coverage is not identical. Remember this before comparing apps.`
- `Let's only look at stores with enough days`
- `Too messy. Try the recent period.`
- `This is probably a dead end`
- `Now compare against 2019`
- `What matters is whether it rained at all in this window, not the exact hour`

Avoid generated-sounding scaffolding:

- `Question Log`
- `Reusable Cuts`
- `Current Conclusion`
- `Blog Notes`
- `Executive Summary`
- `Key Takeaways`
- `Data Quality Assessment`
- `The setup is usable...`
- Any standing pipeline/framework unless the user explicitly asks for one.

### After a plot: say what it showed

The notes above are lead-ins - what you are about to look at. Every plot also needs a note *after* it saying what it showed, because whoever reads this notebook did not run it.

**REQUIRED SUB-SKILL:** use `chart-explainer` for these. Short version: one line with the claim and a number that has something to compare it to, one line of payoff. Same rough register as the rest of the notebook - no scaffolding headings.

Most exploratory plots show nothing, and the note says so - `no signal here`, `one is larger than the other, that's all`. A notebook where every plot has a finding under it is a notebook where the notes were invented.

## Exploration moves that feel right

Prefer these over checklist EDA:

- `count(..., sort = T)` for categories, statuses, years, teams, parties, stores, cities, SKUs.
- Direct object printing to understand data shape.
- `summarise(...)` / `summarise.(..., .by = ...)` with `n()`, `n_distinct()`, min/max dates, sums, means, medians.
- Quick proportions: `mutate(prop = n / sum(n), .by = ...)`.
- Meaningful filters: recent years, top entities, enough observations, non-missing fields, competitive candidates, active stores.
- Change grain deliberately: ball → innings → match → season; order → store-day → store; hour → day/month/year; candidate → constituency/state.
- Compare against baseline: prior year/election/season, others vs India, app vs app, top stores vs rest, this year vs historical average.
- Follow anomalies selectively. Do not analyze every weird column.
- Use domain knowledge aggressively.

## Domain patterns

- **Cricket:** batting order, phase, run rate, strike rate, wickets, innings, chase/bat-first, top-order contribution, player/team cuts, match context, era cuts, simulations when useful.
- **Elections:** vote share, margins, winner/runner-up, party abbreviations, swing, ENPV/corners, alliances, maps, previous election comparison.
- **Commerce/client:** GMV, AOV, order frequency, availability, search/discovery, conversion, cohorts, stores/cities/SKUs, top/bottom tables, treatment/control or no-coupon baselines.
- **Weather/time series:** day-of-year overlays, this year vs history, month/hour windows, thresholds, medians/quantiles, structural breaks only after visual pulse checks.
- **Survey/health/personal data:** enough-n filters, distributions by meaningful demographic or behavioural cuts, longitudinal comparisons.

## Code defaults

- Prefer tidyverse `%>%` pipes.
- Use `tidytable` when `.by` makes code shorter: `summarise.`, `mutate.`, `filter.`.
- Preserve surrounding style. Old notebooks may use `group_by() %>% summarise()` and `T/F`; do not modernize gratuitously.
- Right assignment at pipe end is natural and common:

```r
some_pipeline(...) ->
  object
```

- Left assignment is also fine. Do not enforce one style globally.
- Prefer `case_when()` over nested `ifelse()` in new code, but do not rewrite old code without need.
- Helpers should stay small and local in first-pass exploration. Exception: parsers, simulations, forecasting calibration, Elo/dynamic-pricing algorithms, and repeated text-processing steps may need functions. Even then, inspect inputs/outputs around the function and keep assumptions visible.
- Use `write_delim(pipe('pbcopy'), '\t')`, `pdf(...)`, or quick export only when the notebook is clearly feeding a chart/article/client output.

## Plot defaults

Plot early to decide whether the question is worth pursuing. Good enough beats polished.

Common patterns:

- `geom_point() + geom_line()` for time/ordered comparisons.
- `geom_col()` for counts/tallies.
- `geom_histogram()` / `geom_density()` / `geom_violin()` for distributions.
- `geom_smooth(se = F)` for broad shape.
- `facet_wrap(..., scales = 'free')` for entity comparisons.
- `geom_text()` when exact labels matter.
- `geom_sf()` when geography is the unit.
- `theme_bw()` / `theme_minimal()` with light cleanup.

Do not turn first-pass plots into publication charts unless asked. But make them interpretable enough to guide the next cut.

## Database / large data

- Use `dbplyr` with `tbl(...)` for databases.
- Use DuckDB/Arrow/Parquet for large local or S3 data.
- Keep heavy aggregation in-database.
- `collect()` only when local materialization is needed.
- Raw SQL is fine for setup, views, S3 config, or awkward operations.

## Anti-patterns: what went wrong before

When asked for exploratory notebooks, do **not** produce a polished analysis product with a pre-declared workflow. In particular:

- Do not make a generic audit notebook unless the user asked for an audit.
- Do not add logs, reusable-cut sections, numbered question systems, or blog-production scaffolds by default.
- Do not write long caveat/conclusion prose before seeing enough output.
- Do not smooth over uncertainty. If you have not run the chunks, write probes, not conclusions.
- Do not create broad all-purpose notebooks. Start with one concrete question/context and let it sprawl naturally.
- Do not over-clean. Clean only what blocks the next probe.
- Do not force every notebook into the same shape. Some Karthik notebooks are article scratchpads, some are client metric scans, some are model experiments, some are one-off chart hunts.
- Do not polish Karthik's rough working prose into corporate narration.
- Do not copy RStudio default template text (`Add a new chunk...`) or generic generated headings from precedent files.
- Do not ban functions categorically; ban premature abstraction. Functions are fine when the notebook is building an algorithm, parser, simulation, or forecast calibration.

## Better skeleton for a new scratchpad

Use this shape unless local examples suggest otherwise:

```markdown
---
title: "Short scratchpad title"
output: html_notebook
---

```{r}
require(tidyverse)
```

```{r}
read_csv("/absolute/path/file.csv") ->
  dat
```

```{r}
dat
```

What does coverage look like?

```{r}
dat %>%
  summarise(
    rows = n(),
    start = min(date, na.rm = T),
    end = max(date, na.rm = T),
    entities = n_distinct(entity)
  )
```

Which entities matter?

```{r}
dat %>%
  count(entity, sort = T) %>%
  head(20)
```

Now take the first promising cut...
```

Then continue from results. Do not fill the rest with hypothetical sections.

For detailed sequential 20-step empirical audit, read `references/iterative-learning-20.md`. For behavioural forward-tests against 20 unseen notebooks, read `references/behavioral-forward-tests-20.md`.

## Git safety

- Never run destructive reset commands such as `git reset --hard`.
- Preserve local work before risky operations.
- Keep edits focused.

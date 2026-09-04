---
name: karthik-r-analysis-style
description: >-
  Use for Karthik-style R analysis, exploratory RMarkdown/Quarto notebooks, and analytics pipelines: local-precedent-driven scratchpads, question-led probes, tidyverse/tidytable code, quick tables/plots, domain-informed branching, dbplyr/Arrow/DuckDB for larger data, and RStudio-friendly notebooks.
metadata:
  claude-description: "Karthik-style R analysis: local-precedent scratchpads, analyst-first probes, tidyverse/tidytable, quick plots, domain branching."
---

# Karthik R Analysis Style

Use for R analysis, exploratory `.Rmd`/`.qmd` notebooks, and analytics pipelines. Core rule: this is not generic EDA and not a polished report - it is a working scratchpad where the next chunk follows from what the previous chunk showed.

Own R notebook texture, local precedent, exploratory branching, and R code conventions. `karthik-analysis-planner` owns the analysis contract, `karthik-data-cleaning` owns substantive data preparation and validation, `dataviz-selector` owns final chart choice, `karthik-data-visualization` owns publication chart design, and `chart-explainer` owns notes attached to plots.

## Analyst, not software engineer

Treat an exploratory notebook as thinking in public with data. The goal is judgement, not architecture - context-specific probes, visible assumptions, and domain reasoning over reusable machinery.

Do:

- Start from the analytical question and unit of analysis, not a code structure.
- Let messy facts change the next step; keep local, disposable objects if they help thinking.
- Use domain names and metrics supported by the current question and data; don't treat one notebook family's examples as universal defaults.
- Clean or transform only what helps answer the next question; keep caveats near the chunk that revealed them.

Don't:

- Turn exploration into a package, framework, pipeline, or component, or abstract early into functions/configs/classes/helpers/tests/generic loaders.
- Optimize for reproducible production code before understanding the data.
- Hide judgement behind generic verbs like `clean_data()`, `process_data()`, `run_analysis()`.
- Make the notebook tidy at the cost of the reasoning trail.

A good notebook can be a little ugly if it shows the analyst's path. A bad notebook is clean, generic, and context-free.

## What the 2018+ notebooks show

A 20-notebook audit (Mint, Shopify, Retail, Oliveboard, Ticketing, Onsite, elections, weather, payments, JEE, BabbageInsight, qcom/Cosmix, cricket) fixes the priors:

- Start from a live context: article, client problem, stakeholder need, product idea, or personal curiosity. A concrete objective is fine; a generic EDA preamble is not.
- The unit of analysis is usually implicit in the first few chunks - make it visible in new work (order, item, store-day, candidate-seat, ball, innings, match, user-test, hour-day, app-city-SKU).
- Broad metric scans are allowed only when the business/client context calls for them, and stay metric-led (`GMV`, `AOV`, `DAU`, coupon burn, availability, search visibility), not column-led.
- Rough prose is a feature: typos, fragments, "Not as interesting!", "Nothing significant", "What is this column?" are closer than polished paragraphs. Sparse is fine - not every chunk needs prose, but every sequence should reveal why that cut came next.
- Modeling/simulation/clustering is acceptable when it's the natural analyst move (swing simulator, structural break test, clustering, forecast, player impact), not because a template says so.
- Exports (`pdf`, `pbcopy`, saved chart) and DuckDB/S3/Parquet setup appear only when the output or data source requires them - don't generalize either into boilerplate.

If evidence conflicts, prefer older hand-written notebooks for voice and reasoning, newer ones for current data-access patterns.

## Improving this skill: sequential posterior update

When updating this skill from old notebooks, don't batch-read and summarize once. Go file by file (`prior → inspect file 1 → write delta → update belief → choose file 2 in that light → ... → final patch`), and after each file record what the skill would have predicted, what the notebook does, which belief should strengthen/weaken/become conditional, and which future notebooks the evidence applies to. Karthik's style is a family of behaviours (article scratchpad, client metric scan, data diagnostic, model experiment, chart hunt, personal curiosity), not one global template, so later files refine earlier conclusions rather than just adding examples.

## First move: RAG against local precedent

Before creating or heavily editing a notebook, retrieve local examples and update your plan from them - the skill is the prior, nearby notebooks the evidence. Inspect 3-5 before writing:

1. Same folder/project.
2. Same domain (cricket, elections, commerce/client, weather, time series, survey, etc.).
3. Older hand-written notebooks (2018 onward) if recent files look AI-generated or over-structured.
4. One adjacent "bad fit" file if useful, to avoid copying the wrong mode.

For each, ask: question/context, grain, first inspection, branch logic, code texture, stopping point. Then write in the posterior style - don't invent a new workflow if the repo has one. Copy texture, not just syntax: roughness, local object names, domain metrics, assignment style, plot roughness, section rhythm, willingness to abandon paths. Read `references/style-observations.md` only when matching old notebooks closely.

## Notebook family routing

Classify the family before writing, so one Karthik pattern isn't over-applied to all work:

- **Article/story scratchpad:** one claim or curiosity; rough prose; quick tables/plots; export only if feeding article/chart.
- **Client diagnostic:** stakeholder problem list, source-of-truth decisions, metric definitions, criteria scoring, business-native cuts.
- **Metric scan:** broad scan only when metrics are domain-native (`GMV`, `AOV`, `DAU`, conversion, burn, incidence, active plans), not generic columns.
- **Forecast/model calibration:** functions and repeated evaluation allowed; keep reasoning about bias, seasonality, holdout, ratios, horizons visible.
- **Algorithm/product experiment:** end-to-end functions allowed (dynamic pricing, Elo, structural breaks, parsers); still explain assumptions and check intermediate objects.
- **Text/NLP parsing:** helper functions are normal; still inspect raw lines and samples before abstraction.
- **Chart recreation/graphic hunt:** start from target visual/question; iterate aesthetics and anomalies; export only when the output is the point.
- **Tracker/dashboard-ish:** repeated charts/maps okay; preserve update logic and assumptions, don't make a generic app unless asked.

If a precedent file is just RStudio template boilerplate or generic AI-generated sections, treat it as negative evidence - don't copy its prose or structure.

## Mental model

Write like Karthik at the console: load data → print the object → ask one narrow question in plain English → run one short table or plot → react (too messy, no signal, weird, useful, dead end) → change slice/grain/benchmark from what appeared. The notebook earns its keep by choosing what to look at next, not by being comprehensive.

## Notebook shape

Default exploratory `.Rmd`:

```yaml
---
title: "Concrete title"
output: html_notebook
---
```

```r
require(tidyverse)
require(lubridate)   # if dates matter
require(tidytable)   # if grouped summaries get compact
```

- The notebook is for running chunk by chunk while exploring, never for knitting. Add nothing that only serves a knitted output (figure sizing/captions, `knitr::opts_chunk$set`, cross-references, run-all/knit-ready structure, YAML author/date, global config, package abstraction) unless local precedent does it or the user asked. Assume every chunk runs one at a time in the console.
- Use absolute paths or `setwd()` when chunk-by-chunk execution needs it.
- Keep chunks short - one chunk = one thought/probe. Print raw objects early (`head()`, `count()`, `summary()`).
- Use section titles/prose as steering notes, not report copy. Leave dead ends if they explain the next move. Reassign objects freely when the cleaning step is local and obvious.

## Prose style inside notebooks

Rough working notes, e.g. `What does this file look like?`, `Need a quick size check first`, `Date coverage is not identical. Remember this before comparing apps.`, `Let's only look at stores with enough days`, `Too messy. Try the recent period.`, `This is probably a dead end`, `What matters is whether it rained at all in this window, not the exact hour`.

Avoid generated-sounding scaffolding: `Question Log`, `Reusable Cuts`, `Current Conclusion`, `Blog Notes`, `Executive Summary`, `Key Takeaways`, `Data Quality Assessment`, "The setup is usable...", or any standing pipeline/framework unless explicitly asked.

**After a plot: say what it showed.** The notes above are lead-ins; every plot also needs a note *after* it saying what it showed, because whoever reads this notebook didn't run it. Use `chart-explainer` for these (don't restate its contract here), kept in the same rough register as the surrounding notebook.

## Exploration moves that feel right

Prefer these over checklist EDA:

- `count(..., sort = T)` for categories, statuses, years, teams, parties, stores, cities, SKUs.
- Direct object printing to understand shape.
- `summarise(...)` / `summarise.(..., .by = ...)` with `n()`, `n_distinct()`, min/max dates, sums, means, medians.
- Quick proportions: `mutate(prop = n / sum(n), .by = ...)`.
- Meaningful filters: recent years, top entities, enough observations, non-missing fields, competitive candidates, active stores.
- Change grain deliberately: ball → innings → match → season; order → store-day → store; hour → day/month/year; candidate → constituency/state.
- Compare against a baseline: prior year/election/season, others vs India, app vs app, top stores vs rest, this year vs historical average.
- Follow anomalies selectively; don't analyze every weird column. Use domain knowledge aggressively.

## Domain patterns

- **Cricket:** batting order, phase, run rate, strike rate, wickets, innings, chase/bat-first, top-order contribution, player/team cuts, match context, era cuts, simulations when useful.
- **Elections:** vote share, margins, winner/runner-up, party abbreviations, swing, ENPV/corners, alliances, maps, previous-election comparison.
- **Commerce/client:** GMV, AOV, order frequency, availability, search/discovery, conversion, cohorts, stores/cities/SKUs, top/bottom tables, treatment/control or no-coupon baselines.
- **Weather/time series:** day-of-year overlays, this year vs history, month/hour windows, thresholds, medians/quantiles, structural breaks only after visual pulse checks.
- **Survey/health/personal data:** enough-n filters, distributions by meaningful demographic or behavioural cuts, longitudinal comparisons.

## Code defaults

- Prefer tidyverse `%>%` pipes. Use `tidytable` (`summarise.`, `mutate.`, `filter.`) when `.by` makes code shorter.
- Preserve surrounding style - old notebooks may use `group_by() %>% summarise()` and `T/F`; don't modernize gratuitously.
- Default to right assignment (`->`) at the end of any long chain, so a pipe can run partially, line by line, in the console; the target is named once, at the bottom:

```r
some_pipeline(...) %>%
  more_steps(...) ->
  object
```

- Left assignment is fine for short one-liners and where surrounding code uses it; new long chains end in `->`.
- Prefer `case_when()` over nested `ifelse()` in new code; don't rewrite old code without need.
- Helpers stay small and local in first-pass exploration. Exception: parsers, simulations, forecasting calibration, Elo/dynamic-pricing algorithms, and repeated text processing may need functions - even then, inspect inputs/outputs around the function and keep assumptions visible.
- Use `write_delim(pipe('pbcopy'), '\t')`, `pdf(...)`, or quick export only when the notebook is clearly feeding a chart/article/client output.

## Plot defaults

Plot early to decide whether the question is worth pursuing; good enough beats polished. Common patterns: `geom_point() + geom_line()` for time/ordered comparisons; `geom_col()` for counts; `geom_histogram()`/`geom_density()`/`geom_violin()` for distributions; `geom_smooth(se = F)` for broad shape; `facet_wrap(..., scales = 'free')` for entity comparisons; `geom_text()` when exact labels matter; `geom_sf()` when geography is the unit; `theme_bw()`/`theme_minimal()` with light cleanup.

Don't turn first-pass plots into publication charts unless asked, but make them interpretable enough to guide the next cut. When a plot becomes a deliverable rather than a probe, hand chart-form choice to `dataviz-selector` and visual execution to `karthik-data-visualization`; don't extend these rough defaults into a second publication style.

## Database / large data

- Don't write raw SQL. Reach for a dplyr backend: `dbplyr` with `tbl(...)` for databases, `duckplyr`/DuckDB for local analytical queries, `arrow` for Parquet/S3. Express filters, joins, and aggregation as dplyr verbs and let the backend translate.
- Keep heavy aggregation in-backend; `collect()` only when local materialization is needed.
- Only exception: an unavoidable one-off DDL/config statement (create view, attach, S3 credentials) with no dplyr equivalent. Never hand-write query logic (`SELECT`/`GROUP BY`/joins) as SQL strings.

## Anti-patterns

Beyond the Don'ts above, when asked for exploratory notebooks specifically don't:

- make a generic audit notebook unless an audit was asked for;
- add logs, reusable-cut sections, numbered question systems, or blog-production scaffolds by default;
- write long caveat/conclusion prose before seeing enough output, or smooth over uncertainty (if you haven't run the chunks, write probes, not conclusions);
- create broad all-purpose notebooks - start with one concrete question and let it sprawl;
- polish Karthik's rough working prose into corporate narration, or copy RStudio default template text (`Add a new chunk...`) and generic headings from precedent files.

Ban premature abstraction, not functions categorically - functions are fine when building an algorithm, parser, simulation, or forecast calibration.

## Skeleton for a new scratchpad

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

Then continue from results; don't fill the rest with hypothetical sections.

For the detailed sequential 20-step empirical audit, read `references/iterative-learning-20.md`. For behavioural forward-tests against 20 unseen notebooks, read `references/behavioral-forward-tests-20.md`.

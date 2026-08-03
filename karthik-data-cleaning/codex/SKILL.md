---
name: karthik-data-cleaning
description: >-
  Use when cleaning, profiling, importing, reshaping, joining, validating, or preparing
  tabular data for Karthik-style analysis in R/Rmd, Quarto, notebooks, Python, SQL, or
  analytics repos. Especially use before charting, modelling, data stories, dashboards, and
  exploratory analysis when the task needs context-sensitive, human-supervised cleaning:
  inspect data, define the unit of analysis, apply domain rules visibly, avoid unsupervised
  generic fixes, and keep raw/canonical files untouched.
---

# Karthik Data Cleaning

Clean data like an analyst, not like an automated janitor. Cleaning is part of the analysis. It depends on the question, the unit of analysis, the source quirks, and the domain rules.

Default stack: R/Rmd/Quarto with tidyverse-style pipelines. Use Python/SQL when the project already does, but keep the same judgement pattern.

## Core rule

Use this loop:

```text
question/context → inspect → clean one layer → inspect again → encode visible rule → sanity check → proceed
```

Do not do one-shot unsupervised cleaning. Do not silently standardize, impute, drop, dedupe, or recode because a generic rule says so.

## Workflow

1. Start by identifying the analytical context:
   - question or intended chart/model/story
   - unit of analysis: row, event, transaction, person, match ball, order item, day, hour, constituency, etc.
   - required denominator/numerator/metric if known
   - canonical raw/source files
2. Inspect before changing:
   - `names()`, `glimpse()`/`str()`, `summary()`
   - `count()`/`table()` for categories
   - date ranges and duplicate keys
   - missingness by important dimensions
   - impossible values and obvious source sentinels
3. Clean in small visible steps, preferably in an Rmd/qmd/notebook when exploring.
4. After each non-trivial step, inspect again. Compare counts before/after.
5. Convert types deliberately: dates, times, numerics, booleans, factors/categories.
6. Normalize strings only when needed for joins, grouping, or parsing. Preserve original values if useful.
7. Reshape to the useful grain:
   - wide repeated fields → long entity/event table
   - JSON/list columns → unnested rows
   - timestamp pairs → event intervals or start/end rows
   - monthly columns → `date, value`
8. Apply domain rules explicitly:
   - known bad IDs/files
   - category collapses
   - spelling/name/location mappings
   - exclusion rules
   - parser hacks
   - impossible-value rules
9. Join carefully:
   - check join keys and grain first
   - use `anti_join()`/unmatched counts where mismatches matter
   - make one-to-many expansion intentional
   - build small lookup/default tables when the data/domain supports it
10. Treat missingness contextually:
    - drop only when row cannot answer the question
    - infer/default only with a visible reason
    - use `coalesce()`/modal defaults only when defensible
    - mark impossible values as missing rather than pretending they are real
11. Validate before using cleaned data:
    - row counts before/after
    - key uniqueness at intended grain
    - date coverage
    - missingness of analysis fields
    - impossible values after cleaning
    - denominator sanity
    - spot checks of suspicious rows
12. Preserve raw/canonical files. Never overwrite source data unless explicitly asked.

## Working-file rule

Do not create working/intermediate files by default.

Create/cache a working file only when the canonical/raw source is too huge, slow, remote, unstable, expensive to parse, or annoying enough that repeated inspection becomes impractical. If you create one, say why and keep its contents clearly derived from canonical data.

## R/Rmd style

Prefer this exploratory shape:

```r
raw <- readr::read_csv(path)

raw %>%
  count(category, sort = TRUE)

cleaned <- raw %>%
  mutate(
    date = lubridate::ymd(date),
    amount = readr::parse_number(amount),
    city = stringr::str_to_title(city),
    city = dplyr::case_when(
      city == "Bengaluru" ~ "Bangalore",
      city == "Thiruvananthapuram" ~ "Trivandrum",
      TRUE ~ city
    )
  )

cleaned %>%
  summarise(
    rows = n(),
    start = min(date, na.rm = TRUE),
    end = max(date, na.rm = TRUE),
    missing_amount = sum(is.na(amount))
  )
```

Use scripts/functions only after the cleaning loop stabilizes or when the same parsing logic repeats.

## What to avoid

- Do not invent generic cleaning rules unrelated to the analysis.
- Do not drop rows merely because they contain some missing values.
- Do not impute without a domain reason.
- Do not normalize strings if the raw distinction may matter later.
- Do not dedupe without checking the intended grain.
- Do not make polished pipeline code before understanding the mess.
- Do not create `*_working`, `cleaned.csv`, or `.RData` intermediates unless the working-file rule is met.
- Do not regenerate derived artifacts unless asked.

## Output expectations

When asked to clean data, produce or edit code that includes:

- the inspection checks
- the cleaning transformations
- the domain assumptions as short comments
- the validation checks
- any remaining caveats

When giving a summary, state:

- raw rows and cleaned rows
- unit of analysis
- key filters/exclusions
- important recodes/mappings
- missingness decisions
- join mismatches, if any
- what still needs human judgement

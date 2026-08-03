# karthik-data-cleaning

Use this skill when preparing messy data for analysis, charting, modelling, or data stories.

The core pattern is simple: inspect the raw data, clean one layer, inspect again, and make judgement calls visible. It is deliberately not an automated cleaning skill. It should not silently drop rows, impute values, dedupe records, or standardize strings unless the current question and unit of analysis justify it.

## Defaults

- Prefer Rmd/qmd/notebook cleaning for exploratory work.
- Use tidyverse-style pipelines.
- Preserve raw/canonical files.
- Do not create working files unless canonical files are too large, slow, remote, or painful to reparse.
- Encode domain rules as short comments near the transformation.
- Validate with counts, missingness, date ranges, key uniqueness, and unmatched joins.

## Relationship to other skills

This skill sits upstream of the dataviz skills. It is useful when the data has to be made analysable before question generation, planning, chart selection, or visual storytelling.

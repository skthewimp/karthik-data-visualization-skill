---
name: karthik-r-code-style
description: >-
  Use whenever you write or edit R for Karthik - scripts, RMarkdown/Quarto chunks, ggplot code - to lay it out in his style: one pipe (%>% or |>) per line, right-assigned pipelines ending in ->, multi-argument calls expanded one arg per line with the closing bracket on its own line, ggplot layers with + at end of line, 2-space nested indentation, and modern comma/operator spacing. Layout only; idiom and workflow live in karthik-r-analysis-style.
metadata:
  claude-description: "Karthik's R code layout: one pipe per line, right-assigned pipelines, expanded multi-arg calls, +-per-line ggplot, 2-space indent."
---

# Karthik R Code Style

Use whenever you write or edit R for Karthik - scripts, `.Rmd`/`.qmd` chunks, ggplot code, anything. This skill governs **layout**: line breaks, indentation, bracket expansion, assignment direction, spacing. It does not govern which idioms or which analysis to write - that is `karthik-r-analysis-style`. Apply both together when generating a notebook; apply this one alone when the request is just "format this" or "write this in my R style".

LLM-generated R packs everything onto long horizontal lines. Karthik's R breaks vertically so each step reads as its own line and a pipeline can be run line by line while exploring. Default to the expanded layout below; don't wait to be asked for it.

## The rules

### 1. One pipe per line

Every `%>%` or `|>` ends its line. The source object sits at the pipeline's base indent; each following verb goes on a new line, indented one step (2 spaces) under it.

```r
movie_shows %>%
  arrange(show_id, desc(start_at)) %>%
  distinct(show_id, .keep_all = TRUE) %>%
  mutate(show_date = as_date(start_at))
```

Never chain two verbs on one line (`x %>% filter(...) %>% select(...)` on a single line is wrong for anything beyond a throwaway one-liner).

### 2. Right-assign pipelines

A pipeline that builds a named object ends with `-> name`, so the chain can be selected and run top-down. Put `-> name` at the end of the final line; if that line is already long, drop the arrow and the name onto their own line.

```r
shows %>%
  summarise(
    first_show_date = min(show_date),
    .by = movie_id
  ) -> movie_show_dates

movie_show_dates %>%
  left_join(selected_releases, by = "movie_id", relationship = "one-to-one") ->
  movie_releases
```

Reserve `<-` for short, single-line assignments that are not pipelines (`outdir <- "report_assets"`, `emph <- "#C6462F"`). Reading a file into a name is itself a one-line right-assign: `read_parquet(path) -> movie_shows`.

### 3. Expand multi-argument calls

When a call carries several arguments, or won't sit comfortably on one line, put `(` at the end of the line, one argument (or one logical group) per line indented one step, and the closing `)` on its own line at the call's base indent. The next `%>%` or the `-> name` follows the `)`.

```r
screens_raw %>%
  summarise(
    rows = n(),
    seat_values = n_distinct(seats),
    .by = screen_id
  ) -> screen_capacity
```

Don't expand trivial calls. `n()`, `select(chat_id, year)`, `count(uuid)` stay inline - the rule is for calls with real argument lists, not every set of parentheses.

### 4. ggplot: `+` per line

Each layer ends with `+`; the next `geom_*`, `scale_*`, `labs()`, `annotate()`, `theme()` goes on its own line indented one step under `ggplot(...)`. A single layer with many arguments expands by rule 3.

```r
ggplot(arc, aes(year)) +
  geom_line(aes(y = affection), colour = emph, linewidth = 1.3) +
  geom_point(aes(y = affection), colour = emph, size = 2.4) +
  labs(
    title = "The relationship, in two lines",
    subtitle = "Mean coded affection and tension per chat, by year"
  ) +
  base_theme
```

### 5. Indent is 2 spaces, and it nests

One step is two spaces. A bracket opened inside an already-indented line adds another two. Align the closing bracket with the line that opened it.

### 6. Spacing

Space after every comma. Spaces around `=` in named arguments and around operators (`year >= 2008`, `by = "movie_id"`). This is the modern-notebook convention; ignore the cramped no-space style of the pre-2016 base-R files on disk.

## What this is not

Not a linter to run over Karthik's old code - old hand-written files keep their own style, including base-R Allman braces and cramped spacing. This skill shapes **new** R you generate. Idiom choice (tidyverse over base R, `cummean` over index loops, no raw SQL) and notebook structure live in `karthik-r-analysis-style`; final chart design lives in `karthik-data-visualization`.

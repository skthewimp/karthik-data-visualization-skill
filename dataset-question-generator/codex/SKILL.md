---
name: dataset-question-generator
description: Generate fresh, visualisable analysis questions from a raw tabular dataset. Use when Codex is given a CSV/XLSX/Parquet/database extract and asked what to ask, what to explore, what charts to make, what visualisation workshop prompts to use, or what data stories might be interesting; especially for Karthik-style exploratory analysis where obvious/stale questions should be filtered out before charting.
metadata:
  short-description: Find fresh questions from raw data
  claude-description: Generate fresh, visualisable data questions from raw datasets; reject stale prompts before charting.
---

# Dataset Question Generator

Use this before analysis planning or charting. The job is to turn a raw dataset into a short ranked set of good questions.

Core sequence:

```text
raw dataset → profile → signals → candidate questions → freshness filter → ranked prompts
```

This skill is deliberately upstream of `karthik-analysis-planner`, `dataviz-selector`, and `karthik-data-visualization`. If the source needs parsing, reshaping, joins, or domain cleaning before its signals are legible, use `karthik-data-cleaning` first. Do not start with chart forms. Start with what the data makes worth asking.

## Workflow

1. Inspect the data first. Do not brainstorm from the filename alone.
2. Profile the dataset: row count, row grain, date range, entities, measures, categories, missingness, and format breaks.
   - If profiling exposes messy types, repeated wide columns, broken joins, sentinels, or ambiguous duplicates, pause and do only the minimal contextual cleaning needed to inspect real signals.
3. Identify visible signals: slope change, crossing, plateau, rebound, spike, seasonality, outlier, cluster, concentration, substitution, divergence, or denominator trap.
4. Generate 8-15 rough candidate questions.
5. Reject questions that are stale, obvious, non-measurable, or only restate column names.
6. Return the best 3-7 questions, ranked. Fewer is fine if only a few are good.

## What to inspect

Minimum profile:

- Unit: what does one row represent?
- Coverage: time range, geography, entities, cohorts, currentness.
- Measures: counts, totals, shares, rates, rankings, amounts, durations, text fields.
- Dimensions: entity, segment, region, channel, cohort, status, category.
- Missingness: columns/periods/entities with suspicious gaps.
- Format breaks: old/new schemas, changed definitions, renamed categories, one-off shocks.
- Derived metrics: share, per-capita/per-unit, average size, rate, gap, index, concentration, volatility.

## Karthik-style question patterns

Prefer questions with a visible comparison or mechanism:

- Has X actually changed, or has denominator Y changed?
- Is growth coming from more events, bigger events, or a change in mix?
- Which series has become boring/mature, and is that the interesting fact?
- Where is the gap widening or narrowing?
- Which entities are exceptions to the overall trend?
- Did an event or format break change the level, slope, or composition?
- Is the latest period unusual versus history, or only versus memory?
- Are totals driven by a few big entities or broad participation?
- Does the same story hold in value, volume, share, and average size?
- Where are things stuck, delayed, concentrated, or leaking?

Local analysis priors behind this:

- Bangalore weather: test lived disputes against historical normals and records.
- Bangalore wind/rain: abandon obvious but useless charts; ask a simpler mechanism question.
- Payments/demonetisation: separate volume, value, average size, and counterfactual trend.
- Elections: look for swings, regions, margins, corners, and seat-vote conversion - not just winners.
- Operations data: find bottlenecks, time-in-stage, delay cost, and peer benchmarks.
- Survey data: use ordered subgroup comparisons, concentration, and correlation structure.
- Urban morphology: compare measured features against terrain, history, or periphery - do not just map them.

## Freshness filter

Before final output, test each candidate:

| Criterion | Reject if weak |
|---|---|
| Visual contrast | no likely crossing, gap, slope change, outlier, distribution, or cluster |
| Freshness | obvious, dated, or already answered by the public narrative |
| Dataset support | needs external causal story not in the data |
| Denominator clarity | no clear unit or denominator |
| Karthik fit | dashboard-y, generic, or corporate-slop phrasing |
| Teachability | no useful lesson in chart choice or metric design |

If a question sounds like "trend of X over time", rewrite it around the comparison: compared to what, split by whom, measured how, and why now?

## Output modes

### Questions only

Return only short questions, one per line. No chart notes.

### Workshop seeds

```markdown
### <question>
Use: <fields/entities>
Chart idea: <simple visual>
Why useful: <one sentence>
Watch out: <denominator/caveat>
```

### Analysis-ready

```markdown
- Question:
- Unit:
- Metric:
- Comparison:
- Visual:
- Caveat/falsifier:
```

## Hard rules

- Do not answer questions before profiling.
- Do not overfit to column names; inspect values and ranges.
- Do not include stale defaults just because the domain suggests them.
- Do not recommend dashboards as the output. Recommend interpreted questions.
- Do not use causal words unless the comparison design supports them.
- Prefer fewer, sharper questions over a long generic list.

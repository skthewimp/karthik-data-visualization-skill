---
name: dataset-question-generator
description: Generate fresh, visualisable analysis questions from raw datasets and filter them for evidence and purpose.
metadata:
  short-description: Find fresh questions from raw data
  claude-description: Generate fresh, visualisable data questions from raw datasets; reject stale prompts before charting.
---

# Dataset Question Generator

Use this before analysis planning or charting. The job is to turn a raw dataset into a short ranked set of good questions.

Own question discovery and ranking only. `karthik-analysis-planner` turns one selected question into an executable contract; `karthik-data-cleaning` owns substantive preparation; `dataviz-selector` chooses a chart only after the question is fixed.

Core sequence:

```text
raw dataset → profile → signals → candidate questions → freshness filter → ranked prompts
```

This skill is deliberately upstream of `karthik-analysis-planner`, `dataviz-selector`, and `karthik-data-visualization`. If the source needs parsing, reshaping, joins, or domain cleaning before its signals are legible, use `karthik-data-cleaning` first. Do not start with chart forms. Start with what the data makes worth asking.

## Workflow

1. Inspect the data first. Do not brainstorm from the filename alone.
2. Profile the dataset: row count, row grain, date range, entities, measures, categories, missingness, and format breaks.
   - If profiling exposes messy types, repeated wide columns, broken joins, sentinels, or ambiguous duplicates, pause and do only the minimal contextual cleaning needed to inspect real signals.
3. Identify candidate signals and questions from the values, structure, coverage, measurement properties, uncertainty, and user objective. Visible patterns are useful but not required; diagnostic questions about data quality, definitions, missingness, or absence can be valuable.
4. Generate enough materially different candidate questions to cover the useful signals without padding.
5. Reject questions that are non-measurable, redundant, unsupported by the data, or irrelevant to the stated purpose.
6. Return a small ranked set sized to the evidence and user's need.

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

Derive domain lenses from the observed fields, measurement properties, and user objective. Keep domain-specific priors as optional calibration material, not as default questions.

## Freshness filter

Before final output, test each candidate:

| Criterion | Reject if weak |
|---|---|
| Analytical value | reject if it does not clarify a decision, mechanism, comparison, uncertainty, quality issue, or useful absence |
| Evidence support | reject if required fields, comparisons, or definitions are unavailable |
| Measurability | reject if the unit, metric, or comparison cannot be operationalized |
| Distinctiveness | reject if it merely repeats another question without adding a useful lens |
| Fit to purpose | reject if it does not serve the stated audience or decision |

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
- Defer presentation-form decisions to `dataviz-selector`; note whether the question is for monitoring, exploration, comparison, or narrative use.
- Do not use causal words unless the comparison design supports them.
- Prefer fewer, sharper questions over a long generic list.

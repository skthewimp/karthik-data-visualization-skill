# Dataset Question Generator

`dataset-question-generator` turns a raw dataset into a ranked set of fresh, visualisable questions.

Use it before analysis planning or charting, especially when the dataset has arrived before the question.

## What it does

The skill asks the assistant to inspect:

- row grain;
- date range and currentness;
- entities and categories;
- numeric measures;
- missingness and format breaks;
- derived metrics such as shares, average size, rates, gaps, and concentration;
- visible signals such as slope changes, crossings, plateaus, outliers, clusters, seasonality, and denominator traps.

It then generates candidate questions and rejects the stale ones.

## Good question shapes

Typical outputs sound like:

```text
Is growth coming from more events, bigger events, or a change in mix?
Which series has become boring, and is that the interesting fact?
Is the latest period unusual versus history, or only versus memory?
Are totals driven by a few big entities or broad participation?
Does the story hold in value, volume, share, and average size?
```

The point is to avoid "trend of X over time" unless the comparison is clear.

## How it fits with the other skills

Recommended workflow:

1. Use `dataset-question-generator` to find promising questions.
2. Use `karthik-analysis-planner` to make one question operational.
3. Use `dataviz-selector` to choose the chart form.
4. Use `karthik-data-visualization` to style and critique the chart.
5. Use writing or slide skills only after computed facts exist.

## Output modes

The skill can return questions only, workshop seeds, or analysis-ready prompts with unit, metric, comparison, visual, and caveat.

For workshops, prefer 3-5 short questions that teach a useful chart or metric decision.

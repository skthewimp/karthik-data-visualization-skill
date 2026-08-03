# Karthik Analysis Planner

`karthik-analysis-planner` turns a natural-language data question into a defensible analysis contract.

Use it before coding, charting, or writing when the main risk is a fuzzy question rather than a missing chart style.

## What it forces

The skill asks the assistant to define:

- operational definition;
- unit of analysis;
- denominator;
- numerator/event/quantity;
- metric;
- comparison and baseline;
- data profile checks;
- cleaning or reshape rules that affect the claim;
- sanity checks;
- falsification conditions;
- caveats that must survive into the final post or deck.

## Typical prompts

```text
Use karthik-analysis-planner for: Does Bangalore rain around 4pm?
```

```text
Plan the analysis before we chart whether coupons increase conversion.
```

```text
Turn this cricket question into an analysis contract before touching the ball-by-ball data.
```

## How it fits with the other skills

Recommended workflow:

1. Use `karthik-analysis-planner` to define the measurable question.
2. Use `karthik-data-cleaning` if parsing, reshaping, joins, recodes, or validation affect the metric.
3. Use an evidence-building workflow to profile data and compute facts.
4. Use `dataviz-selector` to choose the visual form.
5. Use `karthik-data-visualization` to style the chart.
6. Use writing/post skills only after computed facts exist.

## Output contract

The skill outputs an analysis contract with sections for measurable claim, definitions, unit/denominator/numerator, metrics, comparisons, data requirements, cleaning rules, sanity checks, falsifiers, caveats, and execution plan.

The output should not answer the question from memory. It should define what evidence would answer the question.

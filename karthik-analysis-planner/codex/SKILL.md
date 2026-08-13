---
name: karthik-analysis-planner
description: Turn a natural-language analytical question into Karthik-style analysis contract before coding, charting, or prose. Use when a user asks a data question, blog/data-story question, exploratory analysis question, or asks to plan an analysis; especially when the answer needs explicit operational definitions, unit of analysis, denominator, comparison, metric, caveats, and falsification conditions rather than generic LLM priors.
metadata:
  short-description: Turn questions into analysis contracts
  claude-description: Turn data questions into Karthik-style analysis contracts with definitions, denominators, comparisons, metrics, caveats, and falsifiers.
---

# Karthik Analysis Planner

Use this before evidence-building. Do not answer the question yet. Convert it into an analysis contract that another agent/notebook can execute.

Own operational definitions, grain, denominator, metric, comparison, evidence requirements, caveats, and falsifiers. Do not perform data cleaning, choose chart forms, or prescribe notebook style; hand those stages to `karthik-data-cleaning`, `dataviz-selector`, and `karthik-r-analysis-style`.

Core sequence:

```text
question → definition → unit → denominator → comparison → metric → evidence plan → falsifier → caveat
```

This skill encodes Karthik's common analysis pattern from notebooks and Mint-style work: start with the live question, inspect what the data can actually measure, choose the row grain, make denominators visible, compare against a baseline, keep sanity checks near the analysis, and preserve the caveat before writing a claim.

If the data itself needs contextual parsing, reshaping, joins, recodes, or validation before evidence-building, pair this with `karthik-data-cleaning`. Treat those cleaning rules as part of the contract, not housekeeping.

## Workflow

1. Restate the question as a measurable claim, not a topic.
2. List ambiguous words that need operational definitions.
3. Pick the unit of analysis appropriate to the question.
4. Define the denominator explicitly. If there are multiple plausible denominators, keep the main one and one sensitivity denominator.
5. Define the numerator/event/quantity being measured.
6. Choose the metric: probability, rate, share, average, total, gap, lift, percentile, swing, etc.
7. Choose the comparison that makes the claim meaningful:
   - versus other hours/periods/groups
   - versus season/era/baseline
   - before/after event
   - exposed vs matched/control group
   - observed vs simulated/counterfactual
8. Specify filters and exclusions before analysis starts.
9. Add a minimum data profile: expected schema, grain check, missingness check, date/coverage range, and source caveats.
10. Define sanity checks that would make you stop or narrow the claim.
11. Define what would falsify or weaken the suspected claim.
12. End with a compact execution plan and output artifacts.

## Output template

```markdown
# Analysis contract: <question>

## 1. Question as measurable claim
- Plain question:
- Measurable version:
- Do not claim yet:

## 2. Operational definitions
| Term | Main definition | Sensitivity / alternative | Why it matters |
|---|---|---|---|

## 3. Unit, denominator, numerator
- Unit of analysis:
- Main denominator:
- Sensitivity denominator:
- Numerator/event/quantity:
- Exclusions:

## 4. Metric
- Main metric:
- Secondary metric(s):
- Required sample-size columns:

## 5. Comparison
- Primary comparison:
- Secondary comparisons:
- Baseline/reference group:

## 6. Data requirements and profile checks
- Required fields:
- Grain check:
- Coverage check:
- Missingness check:
- Cleaning/reshape rules:
- Source caveats:

## 7. Sanity checks
- Check 1:
- Check 2:
- Stop/narrow if:

## 8. Falsification / weakening conditions
- The claim is supported if:
- The claim is weakened if:
- The claim is falsified if:

## 9. Caveats that must survive to final output
- Caveat 1:
- Caveat 2:

## 10. Execution plan
1. Profile data.
2. Clean/reshape only what the question needs, with visible rules.
3. Build analysis table at the chosen grain.
4. Compute denominator/numerator/metric.
5. Compare against baseline and sensitivity definitions.
6. Produce facts table before any prose.
```

## Karthik defaults

- Prefer one sharp question over a broad dashboard.
- Prefer a small facts table before a clever chart.
- Treat data cleaning mismatches as part of analysis, not housekeeping.
- Use plain-English notebook headings like “What doesn't work?”, “First, pulse check”, “Now compare”.
- Keep alternate definitions alive when wording is fuzzy.
- Never let prose get ahead of computed evidence.
- If the data cannot answer the question, say that in the contract.

## Common denominator traps

- “At 4pm” can mean all 4pm hours, all days, rainy days only, or rain events starting near 4pm.
- “Most” can mean highest probability, highest total amount, highest intensity, or most events.
- “Better” can mean higher average, higher conversion, better risk-adjusted outcome, or higher incremental lift.
- “Effect” needs comparison/control; otherwise call it association or difference.
- “Typical” should specify median/mean and distribution spread.

## Calibration note

The contract is domain-neutral. Any domain example should be treated as optional calibration, not as a required definition, metric, threshold, timezone, source, or chart form. Substitute the actual domain's evidence and conventions.

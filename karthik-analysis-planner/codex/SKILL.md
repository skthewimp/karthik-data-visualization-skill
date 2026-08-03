---
name: karthik-analysis-planner
description: Turn a natural-language analytical question into Karthik-style analysis contract before coding, charting, or prose. Use when a user asks a data question, blog/data-story question, exploratory analysis question, or asks to plan an analysis; especially when the answer needs explicit operational definitions, unit of analysis, denominator, comparison, metric, caveats, and falsification conditions rather than generic LLM priors.
metadata:
  short-description: Turn questions into analysis contracts
  claude-description: Turn data questions into Karthik-style analysis contracts with definitions, denominators, comparisons, metrics, caveats, and falsifiers.
---

# Karthik Analysis Planner

Use this before evidence-building. Do not answer the question yet. Convert it into an analysis contract that another agent/notebook can execute.

Core sequence:

```text
question → definition → unit → denominator → comparison → metric → evidence plan → falsifier → caveat
```

This skill encodes Karthik's common analysis pattern from notebooks and Mint-style work: start with the live question, inspect what the data can actually measure, choose the row grain, make denominators visible, compare against a baseline, keep sanity checks near the analysis, and preserve the caveat before writing a claim.

If the data itself needs contextual parsing, reshaping, joins, recodes, or validation before evidence-building, pair this with `karthik-data-cleaning`. Treat those cleaning rules as part of the contract, not housekeeping.

## Workflow

1. Restate the question as a measurable claim, not a topic.
2. List ambiguous words that need operational definitions.
3. Pick the unit of analysis: row/event/hour/day/person/constituency/session/match/etc.
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

## Mini-example: Bangalore 4pm rain

```markdown
# Analysis contract: Does Bangalore rain around 4pm?

## 1. Question as measurable claim
- Plain question: Does Bangalore rain around 4pm?
- Measurable version: Is the probability or amount of rain during the 16:00-16:59 IST hour higher than nearby/other hours?
- Do not claim yet: “Bangalore gets most rain at 4pm.”

## 2. Operational definitions
| Term | Main definition | Sensitivity / alternative | Why it matters |
|---|---|---|---|
| rain | measurable hourly precipitation > 0 mm | >= 0.1 mm threshold | ERA5/drizzle noise can change rainy-hour counts |
| around 4pm | 16:00-16:59 IST | 15:00-17:59 window | colloquial “around” may not mean one exact hour |
| Bangalore | station/grid cell used in source | city average if available | spatial source changes interpretation |

## 3. Unit, denominator, numerator
- Unit of analysis: one observed local hour.
- Main denominator: all observed 16:00 IST hours in the data period.
- Sensitivity denominator: all observed hours by hour-of-day; all days with complete hourly coverage.
- Numerator/event/quantity: hours with rain > 0 mm; also sum/mean rainfall amount.
- Exclusions: missing precipitation, duplicate hours, incomplete days for hourly comparison.

## 4. Metric
- Main metric: rainy-hour probability by hour = rainy hours / observed hours.
- Secondary metric(s): mean rainfall mm/hour; share of daily rainfall by hour; rainy-day-only version.
- Required sample-size columns: observed_hours, rainy_hours, complete_days.

## 5. Comparison
- Primary comparison: 16:00 vs all other hours of day.
- Secondary comparisons: 16:00 vs 15:00/17:00; monsoon vs pre-monsoon vs dry months; recent decade vs earlier period.
- Baseline/reference group: average hour-of-day probability across all complete days.

## 6. Data requirements and profile checks
- Required fields: timestamp in IST or convertible timezone, precipitation amount, source, coverage period.
- Grain check: exactly one record per hour or documented aggregation.
- Coverage check: first/last date, missing hours by year/month/hour.
- Missingness check: precipitation missingness by hour and season.
- Source caveats: reanalysis/grid rainfall may not equal a gauge at one neighbourhood.

## 7. Sanity checks
- Compare >0 mm and >=0.1 mm thresholds.
- Verify 16:00 is local IST, not UTC.
- Stop/narrow if missingness is hour-dependent or coverage is too short.

## 8. Falsification / weakening conditions
- Supported if: 16:00 is clearly above most hours with adequate sample size and survives thresholds/seasons.
- Weakened if: 16:00 is only high in one season or only for trace rain.
- Falsified if: several other hours have equal/higher probability or amount.

## 9. Caveats that must survive to final output
- Probability of any rain is not the same as total rainfall amount.
- “Around 4pm” depends on chosen hour/window and local timezone.

## 10. Execution plan
1. Profile hourly rain data coverage and timezone.
2. Build complete hourly table with hour, date, month/season, year/decade.
3. Compute rainy-hour probability and rainfall amount by hour.
4. Repeat by season and threshold.
5. Export computed facts before writing title/chart/prose.
```

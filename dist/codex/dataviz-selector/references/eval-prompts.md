# Out-of-sample evaluation prompts

Use these to test `dataviz-selector`. Do not use the user-calibration examples as tests.

## Fuel price transmission
Dataset columns: month, petrol_price, diesel_price, food_cpi, headline_cpi, policy_period.
Question: did fuel prices transmit into food inflation?
Good answer: indexed time lines plus lag/relationship view; warns against dual axes and causality from co-movement.

## Regional airport viability
Dataset columns: airport, state, monthly_passengers, monthly_flights, route_count, subsidy_eligible.
Question: are small airports viable under subsidised regional connectivity?
Good answer: traffic-vs-service scatter with labels/highlights; map only if spatial clustering is the claim.

## Management PBT miss
Dataset columns: division, actual_revenue, budget_revenue, py_revenue, actual_gm, budget_gm, actual_pbt, budget_pbt, cost_bucket.
Question: what drove the PBT budget miss and what should management do?
Good answer: scorecard first, then PBT bridge/waterfall or ranked driver bars, with action annotations.

## Sanitation adoption factors
Dataset columns: household_feature, feature_value, toilet_ownership_rate, n_households, district.
Question: which household characteristics best explain toilet ownership?
Good answer: factor profile charts/category-rate panels; avoid coefficient table first.

## Portfolio downside risk
Dataset columns: scenario_id, portfolio, return_3m, return_12m, drawdown, risk_profile.
Question: which portfolio is safer for a conservative investor?
Good answer: downside distribution/threshold probability/utility curve; avoid mean-vol-only scatter.

## Public red-team prompts

Use these before publishing or after major edits. Good answers should be static, explanatory, and should not select pie/donut/3D/interactive/animated/radar/gauge forms as the recommendation.

1. Customer acquisition by channel and month; which channel is getting less efficient?
2. Current market share by 8 brands; user asks for a pie chart.
3. Sales by region/product/month; user asks for an interactive dashboard.
4. App funnel counts by step; where do users drop off?
5. Treatment/control conversion by day around launch; did launch work?
6. Feature importance and coefficients from churn model; what drives churn?
7. NPS responses 0–10 by segment; which segment is polarised?
8. SKU profit and cumulative share; is profit concentrated?
9. Daily temperature across 30 years plus current year; is this summer unusual?
10. Bootstrap returns for 5 portfolios; safest for conservative client?
11. City locations and sales volume; which cities sell most?
12. Ward boundaries with odd shapes; show gerrymandered wards.
13. Two metrics with different scales over time; user suggests dual-axis chart.
14. Actual vs budget by department/month; why did costs overshoot?
15. Product-purchase correlation matrix; what products go together?
16. Campaign ROI by spend decile; diminishing returns?
17. GDP, population, GDP per capita over decades; what changed after reforms?
18. Budget allocation parts; user asks for 3D donut.

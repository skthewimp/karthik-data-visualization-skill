# Dataviz Critique

Use `dataviz-critique` when reviewing an existing chart or dashboard and asking what works, what fails, how to improve it, and what alternative visualizations could tell the story better.

The skill evaluates three things together:

1. **Question** — what the visual is trying to answer.
2. **Data** — whether the data can support that question.
3. **Visual** — whether the encoding lets the viewer see the answer clearly.

It then applies Karthik's stricter style: clarity first, deliberate design choices, data fundamentals before polish, claim-led narrative, and robust/repeatable improvements.


It now also asks for redesign alternatives, usually:

1. **Minimal repair** — preserve the current chart but fix execution.
2. **Better analytical redesign** — change the chart type to answer the stated question more clearly.
3. **Different story lens** — reframe the visual around a more useful comparison, such as rates instead of totals, distributions instead of averages, or trends instead of snapshots.

Each alternative must explain when to use it, the chart form, encoding, what it fixes or reveals, and the tradeoff.

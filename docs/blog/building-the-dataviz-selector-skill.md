# Building a skill for choosing charts

I started today with a slightly odd problem. I already had a data visualisation skill, but it was mostly about style. It knew things like "avoid legends", "use direct labels", "make small multiples", "don't let default matplotlib leak through", and so on. Useful stuff. But it didn't really answer the prior question: given this dataset and this story, what chart should I make in the first place?

This is a surprisingly under-specified problem. Most chart taxonomies are written as if the data type determines the chart. Time series means line chart. Category means bar chart. Geography means map. Useful, and also often wrong. State-level diversity scores may look pretty on a map, but a sorted bar chart is usually clearer. A growth slowdown may be mathematically visible in YoY, but a raw line with a dotted counterfactual might tell the story better.

So we built the skill backwards from examples. First, Codex mined my old Mint articles and the charts that went with them. Elections produced vote-share versus seat-share scatters, swing-to-seat curves, and maps only when constituency shape mattered. Cricket produced win-probability trajectories rather than scorecards. Payments pieces produced simple time-series panels with event markers. Then we looked at old decks, where the answer is often not a chart at all, but a scorecard followed by a bridge or action table.

The useful bit was the calibration round. Codex asked me one situation at a time, and I answered with what I would actually do. For UPI growth slowing, the pure answer might have been a growth-rate chart. I rejected that. Too much reader effort. Show the raw line, mark the slowdown, and draw a dotted projection of the old growth path. That judgement is exactly what I wanted captured.

We also added negative taste. No pie charts, no 3D charts, no animated nonsense, no interactive dashboard as the first answer, no gauges, no radar charts. If the user asks for a 3D donut, the skill should politely refuse the form and offer sorted bars or a table. Taste is partly knowing what not to do.

The final version has two parts. `dataviz-selector` chooses the chart. `karthik-data-visualization` makes it look right. This separation feels important. Bad styling can weaken a good chart, but the wrong chart is usually dead on arrival.

PS: the most important lesson from the testing was boring but important - first check whether the dataset can actually answer the question. A beautiful chart of unavailable evidence is still a hallucination, only with axis labels.

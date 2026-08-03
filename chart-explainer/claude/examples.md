# Chart Explainer - worked examples

Real notes from Karthik's Mint columns and analysis notebooks, paired with the generic version each one would have become. Read this before writing the first note of a run.

The point of this file is calibration, not templates. Do not lift the sentence shapes. Notice what the good ones are doing: they say a thing, with a number, and then land one punch.

---

## 1. The number carries its anchor

**Generic**
> This chart shows the number of debit card transactions at points of sale by month. There is a noticeable increase in November 2016.

**Karthik, Mint**
> Debit cards were swiped at points of sale 234 million times in November, nearly twice the monthly average from the first nine months of the calendar year.
> Credit card usage did not rise nearly as much - the substitution was out of cash and into debit.

234 million means nothing on its own. "Nearly twice the monthly average from the first nine months" is what makes it a finding.

---

## 2. The data kills a stated expectation

**Generic**
> Figure 4 shows wickets lost per innings across IPL seasons, which has decreased over time.

**Karthik, Mint**
> Amit Varma hypothesised that teams would get more attacking as they realised they have ten wickets to spend. Figure 4 suggests otherwise - wickets lost per innings has come down over the years.
> Unless pitches have got flatter, teams have become more conservative, which is rather baffling.

The chart is only interesting because somebody expected the opposite. Name the expectation, then break it.

---

## 3. A break point, not a trend

**Generic**
> The average scoring rate in the slog overs has generally increased over the seasons.

**Karthik, Mint**
> Until 2014 the average slog-overs scoring rate in a chase sat just over eight runs an over. In 2014 it jumped past nine and has stayed there.
> This is a regime change, not a trend - nothing has moved since.

"Increased over time" and "stepped up once in 2014 and then stopped" are different claims and lead to different decisions.

---

## 4. Nothing here

**Karthik, Clover notebook**
> No real correlation between rejects and routes.

**Karthik, Clover notebook**
> Clusters seem very very similar. So not much information from them.

**Karthik, Clover notebook**
> One is larger than the other, that's all.

**Karthik, Clover notebook**
> No signal here.

Four charts, four nulls, four notes. None of them were dressed up. In an exploratory notebook this is the majority case, and the note is allowed to be one line when there is only one line to say.

For a colleague or client, add what was tested:

> No real correlation between rejects and routes.
> Checked whether rejection rate clusters by delivery route - it does not, at any route size.

---

## 5. Weak is stated as weak

**Generic**
> Figure 3 shows a relationship between spectrum quantity and reserve price.

**Karthik, Mint**
> The broad relationship exists, but it is weak - a lot of other factors have gone into setting the reserve price.
> Nobody expects it to be perfectly linear, but this much scatter is too much for comfort.

The finding is the weakness. Do not round a weak relationship up to a relationship.

---

## 6. Orientation in line 1, claim in line 2

Use only when the reader cannot tell what is plotted.

**Karthik, Mint**
> Figure 3 plots constituency-wise BJP lead over Congress in 2017 against the same figure in 2012.
> The story is in the top-left and bottom-right quadrants - the seats that changed hands, and there are a lot of them.

**Karthik, Mint**
> Each bar shows the number of towns or villages in that population bucket, for six states.
> Kerala does not look like any of the other five.

What makes both of these work is that line 2 is a finding. Two lines of orientation is the failure mode.

---

## 7. The caveat as the payoff

**Karthik, Mint**
> The total number of cheques written has been falling steadily for years, but saw a small revival after demonetisation.
> The March spikes are financial year-end, not behaviour.

**Karthik, Mint**
> Holkar Stadium in Indore is the highest-scoring of the secondary venues.
> Small sample - the ground has hosted five IPL games.

One caveat, stated flatly, then stop. No paragraph of limitations.

---

## 8. The note that points at a decision

**Karthik, Clover notebook**
> Stores whose median order value in the first two weeks is above Rs 500 are very likely to stick.
> This is the acquisition filter - the first fortnight tells you most of what the second month will.

**Karthik, Clover notebook**
> 111 stores have ordered at least 30 times, and 41 of them are now lost.
> Worth finding out when we lost them before spending on more acquisition.

---

## 9. Plumbing, not a finding

Some exploratory charts exist to check the data. Say that.

**Karthik, Clover notebook**
> Until the pandemic this wasn't an issue; after that it shows up constantly.
> Or is this just a data collection issue? Worth checking before reading anything into it.

Note-to-self register keeps the open question. Do not launder it into a finding for a client.

---

## 10. Tables

**Generic**
> The table shows batting average and median score for India's top run scorers.

**Karthik, Mint**
> Dhoni's shape parameter is far ahead of every other Indian batsman in the table.
> He converts starts into big innings at a rate nobody else here matches.

Name the cell that carries the point.

---

## Banned constructions, seen in the wild

| Bad | Why |
|---|---|
| "This chart shows the distribution of order values by store." | Restates the axes. Says nothing. |
| "As we can see, there is an interesting pattern here." | Which pattern. |
| "The data appears to suggest there may be some correlation." | Claiming a finding without owning it. Say weak, or say no. |
| "Sales grew 12%." | No anchor. Grew from what, against what. |
| "The November spike was driven by the currency withdrawal." | Causal verb on observational data. "coincided with" unless you have the design. |
| "Three things stand out: X, Y and Z." | Rule of three, and it is three findings in a two-line note. |

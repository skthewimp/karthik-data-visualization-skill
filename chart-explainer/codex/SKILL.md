---
name: chart-explainer
description: Write the short note that travels with a chart or table - the two lines in an email above the graph, the line under a figure in a notebook, the sentence in a Slack message. Use when asked to build an exploratory notebook, explore a dataset, or produce analysis someone else will read, since every plot in that notebook needs its note. Also use when a chart is finished and someone else has to be told what it says, when handing analysis to a client or colleague, when the reader will see the visual without the analyst in the room, or when a draft note says "this chart shows the distribution of X", quotes a number with nothing to compare it to, or manufactures a finding out of a chart that shows nothing.
metadata:
  short-description: Write the two-line note that accompanies a chart or table
  claude-description: Explain what a chart or table says in two lines - for an email, a message, or under every plot in an exploratory notebook. Includes saying when it shows nothing.
---

# Chart Explainer

Own the short prose placed beside or below a finished chart or table. Do not write text on the chart, redesign it, critique it, or decide whether it passes release; those belong to `chart-annotations`, `karthik-data-visualization`, `dataviz-critique`, and `dataviz-eval`.

Use this when a chart or table has to be understood by someone who was not in the analysis. The output is the text that sits **next to** the exhibit: the two lines in an email body, the note under a figure in a notebook, the message that carries a screenshot.

Two situations trigger it. Either an exhibit already exists and needs narrating, or you are being asked to build an exploratory notebook - in which case the notes are part of what you are building, and the rules in "Exploratory notebooks you are building" below apply from the first plot.

This is not text on the chart. This is not a critique of the chart. It is the narration that makes a finished exhibit legible to someone reading it cold.

## The two-line contract

Use the shortest explanation that makes the exhibit understandable in its delivery context. Two lines can be a useful compact default, but it is not a universal limit.

**Lead - the finding or orientation.** State what the exhibit is about and what it supports. Include a quantitative anchor when it improves understanding, but use a qualitative structure, ordering, pattern, or null result when that is more informative.

**Follow-up - one useful qualification or implication when needed.** Choose what prevents over-reading or helps the reader act; combine points only when separating them would reduce clarity.

| Payoff | Use when | Example |
|---|---|---|
| Contrast | the data kills an expectation someone holds | "Kohli said India bats slower in the middle overs; the data says India outscores everyone there." |
| Consequence | it points at a decision | "If the median first-fortnight order is above Rs 500, the store is very likely to stick." |
| Caveat | the reader will over-read it otherwise | "March is an aberration - financial year-end." |

Two payoffs is one too many. Choose.

```text
Bad
  This chart shows debit card transactions at points of sale from January to December,
  and we can see there is a clear increase in November which continues into December.
  The data comes from the RBI payment systems indicators dataset.

Good
  Debit cards were swiped 234 million times in November, nearly twice the monthly
  average of the first nine months.
  Credit cards barely moved - the substitution was cash to debit, not cash to card.
```

### The orientation exception

If the reader cannot tell what is plotted, line 1 may orient instead of claim - but **line 2 must then carry the claim.** The payoff is never optional.

```text
Figure 1 plots constituency-wise BJP vote share in 2017 against 2012.
The interesting quadrants are top-left and bottom-right: the seats that changed hands.
```

Orienting in line 1 *and* line 2 is the most common failure of this skill. Two lines of setup and no finding is worse than no note.

## Before writing: say what it is saying

Do not start from a template. Say out loud, in plain words, what this chart is actually saying. Then compress that into line 1.

Charts often turn out to be saying things like: something moved; two groups differ; the data kills a stated expectation; there is a break point after which behaviour is different; a relationship is real but too weak to lean on; nothing is here; this chart is a data check rather than a finding.

**That list is to loosen your thinking, not to classify into.** Most real charts say something that is not on it. Write what this one says.

## Every number carries its anchor

A bare magnitude is a failed note. The reader has no idea whether 234 million is a lot.

Anchors, in rough order of usefulness: the prior period, the other group, the control or no-treatment baseline, the number someone expected, the total it is a share of.

```text
Fail   Average ticket size on credit cards was Rs 2,700 in November.
Pass   Average ticket size on credit cards fell to Rs 2,700 in November, from over
       Rs 3,000 across the first nine months.
```

**With data in hand, compute the number.** Never read it off the image and never round toward a rounder-sounding figure. If only the image is available, say so in the note and keep the precision coarse.

## "Nothing here" is a real answer

If the chart shows nothing, the note says so. This is a legitimate, frequently correct output.

```text
No real correlation between rejects and routes.
Checked whether rejection rate clusters by delivery route - it does not.
```

```text
The clusters are near-identical on every dimension. Nothing to act on here.
```

Rules:

- Say what you looked for and did not find. "No signal" alone is not enough; the reader needs to know which signal was tested.
- Preserve the distinction between description, exploration, and inference. Match language to evidence strength and uncertainty: avoid inflated claims, but distinguish null, weak, suggestive, inconclusive, and heterogeneous findings when supported.
- A weak-but-real relationship is stated as weak, with the strength quantified: "the relationship exists but it is weak - reserve price explains little of the variation."
- Never manufacture. If you find yourself hunting the chart for something quotable, the note is "nothing here".

## Register

Ask once at the start of the run which register applies. Default to note-to-self if the answer is not obvious from context.

| Register | Keeps | Adds |
|---|---|---|
| Note to self, later | jargon, column names, open questions ("is this a data collection issue?") | - |
| Colleague | blunt nulls, assumed shared context on the dataset | - |
| Client / external | - | what the metric means, and the caveat line where the data is thin |

Register changes the wording. It never changes the finding, and it never softens a null into a maybe.

## Input modes

| What you have | How to write the note |
|---|---|
| Rendered chart + the data | Read the image for the shape, compute every number from the data, verify the claim against the data before writing. |
| Chart code + the data, no render | Infer the shape from the geoms and the grouping, compute the claim from the data. |
| Image only | Describe conservatively. No invented precision. Flag in the note that numbers are read off the chart. |

The verification step is not optional when data is available. A note that states a number the data does not support is worse than no note.

## Exploratory notebooks you are building

When the request is "build a notebook to explore this data" rather than "explain this chart", this skill is part of the deliverable, not a later pass. The person asking will read the notebook without having run it, and an unnarrated plot hands them the analyst's job.

Rules for that case:

1. **Every plot chunk is followed by its note.** Two lines, in the markdown immediately below the chunk. Not a comment inside the chunk, not a batch of notes at the end.
2. **Write the note after running the chunk, from the computed output.** A note written from the code you are about to run is a guess.
3. **Notes are written in the note-to-self register by default** - this is exploration, so open questions and column names belong in them.
4. **The nulls stay in.** An exploratory notebook is mostly dead ends. A notebook where every plot has a finding under it is a notebook where the notes were invented. If a plot shows nothing, its note says so and the plot stays.
5. **Do not add a findings summary at the top or bottom unless asked.** Ranking and narrative are a separate request, made once the reader has seen which probes came back empty.

The reason this matters most here: when an agent both runs the exploration and writes it up, nobody checks whether the write-up matches what the charts show. The two-line contract and the compute-don't-eyeball rule are the only things standing between an exploratory notebook and a confident deck of artefacts.

## Tables

Same contract. Line 1 names the row, column, or cell that carries the point - not the table's contents.

```text
Bad    The table shows revenue, margin and order count by city for the last quarter.
Good   Hyderabad is the only city where margin fell while revenue grew - down 4 points
       on 18% more revenue.
```

## Batches

A notebook with twelve plots gets twelve notes, numbered to match the figure order.

**Do not smooth them into a narrative.** Exploratory notebooks mostly contain dead ends, and the reason this skill exists is that the dead ends get written up as findings. If nine of twelve show nothing, nine notes say nothing.

Do not add a summary paragraph unless asked. Do not reorder to build an arc. Do not drop the null charts - the reader needs to know they were checked.

## Banned

- "This chart shows", "The graph illustrates", "As we can see", "It is evident that", "Here we visualise"
- Restating the axis labels as prose
- Repeating the chart title
- Hedge-mush: "appears to indicate a possible trend", "suggests there may be some relationship"
- Rule-of-three parallelism, and "not X; it just Y"
- Em dashes - use hyphens
- A third sentence
- Causal verbs without causal evidence: "drove", "caused", "led to" on observational data. Use "coincided with", "is associated with", or restructure.

## Self-check before output

1. Does line 1 contain a number, and does that number have an anchor?
2. Did the number come from the data, or from looking at the picture?
3. Is line 2 exactly one of contrast, consequence, caveat?
4. Would this note survive if the chart were removed - does it say something, or only point at something?
5. If the chart shows nothing, does the note say nothing, or did I find something to fill the space?

Any failure: rewrite. Do not ship the note with a caveat about itself.

## Calibration

`examples.md` holds real notes from Karthik's Mint columns and analysis notebooks, with the weak versions alongside. Read it before writing the first note of a run. The failure mode this skill guards against is generic caption prose, and worked examples are the only reliable correction.

## Not this skill

- Text placed **on** the chart - `chart-annotations`
- Whether the chart is any good - `dataviz-critique`
- Fixing a chart that hides its message - `dataviz-fix`
- Longer prose around the analysis - `karthik-writing-style`

If the chart is bad, still write the note. Do not critique it here.

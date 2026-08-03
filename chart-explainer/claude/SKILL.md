---
name: chart-explainer
description: Explain what a chart or table says in two lines for an email, notebook, or message - including when it says nothing.
---

# Chart Explainer

Use this when a chart or table exists and someone who was not in the analysis has to understand what it says. The output is the text that sits **next to** the exhibit: the two lines in an email body, the note under a figure in a notebook, the message that carries a screenshot.

This is not text on the chart. This is not a critique of the chart. It is the narration that makes a finished exhibit legible to someone reading it cold.

## The two-line contract

Every exhibit gets **two lines. Not three.**

**Line 1 - the claim.** A sentence with a subject and a verb, carrying at least one concrete number with its anchor.

**Line 2 - one payoff.** Pick exactly one:

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
- Never upgrade weak to moderate. "There is some indication of a possible trend" is a way of claiming a finding without owning it. Either it is there or it is not.
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
- Fixing a chart that hides its message - `chart-improver`
- Longer prose around the analysis - `karthik-writing-style`

If the chart is bad, still write the note. Do not critique it here.

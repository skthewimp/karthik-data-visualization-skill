# Chart Explainer Skill

`chart-explainer` writes the short note that travels with a chart or table.

It exists because of an asymmetry: the person who ran the analysis knows what the chart says, and nobody else does. A graph pasted into an email without narration makes the reader do the analyst's work. Worse, when the analysis was run by an agent rather than by hand, the analyst does not know what the chart says either.

The output is two lines per exhibit. Line 1 is the claim, carrying a number and the comparison that makes the number mean something. Line 2 is exactly one payoff: the expectation the data kills, the decision it points at, or the caveat that stops the reader over-reading it.

## When it fires

Two situations. The first is obvious: a chart exists and needs narrating. The second matters more - a request to **build an exploratory notebook**. Those requests never mention charts, and the plots do not exist yet, but the person asking will read the notebook without running it. In that case the notes are part of the deliverable: two lines in markdown under every plot chunk, written from the chunk's computed output rather than from the code about to run.

`karthik-r-analysis-style` cross-references this skill for exactly that reason, so it fires on "build me a scratchpad for this data" even when nothing in the request sounds like charting.

## Trigger examples

Use it for prompts like:

```text
I'm sending these six charts to the client. Two lines each.
```

```text
Ran the notebook, twelve plots came out. What does each one actually say?
```

```text
What do I write above this graph in the email?
```

```text
Does this chart say anything at all, or am I looking at noise?
```

```text
Build a notebook to explore this dataset.
```

## What it is strict about

**Anchored numbers.** "Sales grew 12%" is not a note. Twelve percent against what, over what period, compared to whom. A bare magnitude is treated as a failure and rewritten.

**Computed numbers.** When the data is available, every number in the note is computed from it. Reading a value off the picture and writing it down as fact is the fastest way to put a wrong number in a client email.

**Nulls stay null.** Exploratory notebooks are mostly dead ends. The skill is explicitly permitted - and required - to write "no real correlation between rejects and routes" and stop. It will not upgrade a weak relationship to a moderate one, and it will not hunt a flat chart for something quotable. In batch mode it refuses to reorder or summarise the exhibits into a narrative arc, because that is exactly how a notebook of dead ends becomes a deck of findings.

**Two lines.** Not three. The constraint is the point - it forces a choice about what the exhibit is for.

## Register

The skill asks once which register applies and defaults to note-to-self:

- **Note to self, later** keeps jargon, column names, and open questions.
- **Colleague** keeps blunt nulls and assumes shared context on the dataset.
- **Client** adds what the metric means and a caveat line where the data is thin.

Register changes the wording only. It never changes the finding and never softens a null into a maybe.

## Input modes

The skill works from a rendered chart plus the underlying data (preferred - it reads the shape from the image and computes the numbers from the data), from chart code plus data with no render, or from an image alone. In the image-only case it stays coarse and flags that the numbers were read off the chart.

## Calibration

`examples.md` ships inside each surface directory and is loaded at runtime. It holds real notes from Karthik's Mint columns and Clover/Onsite analysis notebooks, each paired with the generic caption it would otherwise have been. Generic AI chart prose is the dominant failure mode here, and worked examples are the only correction that reliably holds.

## Boundaries

`chart-annotations` owns text placed on the chart. `dataviz-critique` and `chart-improver` own chart quality - `chart-explainer` narrates a bad chart without commenting on it. `karthik-writing-style` owns anything longer than a note.

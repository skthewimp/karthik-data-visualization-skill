# chart-explainer

Use this skill when the question is: what do I write *next to* this chart so the reader knows what it says? It produces the two lines that go in an email above a graph, the note under a figure in a notebook, or the sentence carrying a screenshot into a chat.

This is not on-chart text and not chart critique. It assumes the exhibit is finished and the reader will see it without the analyst in the room.

## What it does

- Enforces a two-line contract: line 1 is the claim with a number, line 2 is exactly one of contrast, consequence, or caveat.
- Handles the orientation case, where line 1 says what is plotted - and requires line 2 to carry the finding anyway.
- Requires every number to be anchored to a comparison, and computed from the data rather than read off the image.
- Treats "nothing here" as a legitimate output, and requires the note to say what was looked for and not found.
- Refuses to upgrade a weak relationship into a relationship, or to manufacture a finding to fill space.
- Switches register between note-to-self, colleague, and client without softening the finding.
- Degrades across three input modes: chart plus data, code plus data, and image only.
- Applies the same contract to tables, naming the cell that carries the point.
- In batch mode over an exploratory notebook, writes one note per exhibit and refuses to smooth the dead ends into a narrative.
- Ships a worked-example bank drawn from Karthik's Mint columns and analysis notebooks, since generic caption prose is the failure mode and examples are the correction.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/examples.md`](codex/examples.md) and [`claude/examples.md`](claude/examples.md) - the calibration example bank, shipped inside each surface so the installed skill can read it at runtime.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `chart-annotations` for text placed on the chart itself - that skill decides what the chart marks, this one decides what the accompanying message says. Use `dataviz-critique` or `chart-improver` when the chart is the problem; `chart-explainer` narrates whatever it is given without critiquing it. Use `karthik-writing-style` when the output is prose rather than a two-line note.

## Edit rule

If note-writing behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md`, and both copies of `examples.md`, unless the change is surface-specific.

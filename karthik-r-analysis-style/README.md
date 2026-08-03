# karthik-r-analysis-style

Use this skill when the question is: how should this R analysis actually be written? It governs exploratory scratchpads and RMarkdown/Quarto notebooks - how the file is structured, how probes are sequenced, what the working notes sound like, and which idioms to reach for.

This is not a charting skill and not a cleaning skill. It is the register and shape of the analysis file itself.

## What it does

- Sets the analyst-first posture: probes that answer a question, not checklist EDA or software-engineering scaffolding.
- Starts every new scratchpad with a RAG pass against local precedent, so a new notebook inherits the shape of the ones already on disk.
- Routes between notebook families and gives a skeleton for a fresh scratchpad.
- Fixes the prose register inside notebooks: rough working notes, and an explicit ban on generated-sounding headings like "Key Takeaways" or "Data Quality Assessment".
- Requires an after-plot note on every plot, delegating the wording to `chart-explainer`, because a lead-in note says what you were about to look at and the reader also needs to know what it showed.
- Sets tidyverse/tidytable code defaults, quick-plot defaults, and the dbplyr/Arrow/DuckDB routing for data too large to hold.
- Records anti-patterns from earlier notebooks that went wrong, and a sequential rule for folding new observations back into the skill.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/references/`](codex/references/) and [`claude/references/`](claude/references/) - the empirical posterior, style observations, and the two audit files, shipped inside each surface because `SKILL.md` reads them at runtime.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

`karthik-data-cleaning` runs inside these notebooks when the source needs work. `chart-explainer` writes the note under each plot - this skill requires it rather than duplicating its rules. `karthik-data-visualization` takes over when a quick exploratory plot has to become a finished chart. `karthik-analysis-planner` runs before the notebook when the question itself is still fuzzy.

## Edit rule

The two `SKILL.md` bodies are identical and only the frontmatter differs. Change both, and both copies of `references/`, unless the change is surface-specific.

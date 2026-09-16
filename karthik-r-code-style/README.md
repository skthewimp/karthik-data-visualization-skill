# karthik-r-code-style

The layout skill for R. It decides where the line breaks go, how brackets expand, which way assignment points, and how things indent - so generated R reads the way Karthik writes it by hand instead of the long horizontal lines an LLM defaults to.

This is a formatting skill, not a workflow skill. It says nothing about which idioms to reach for or how an analysis is sequenced. That is `karthik-r-analysis-style`. Use them together for a notebook; use this alone when the task is just "write/format this R in my style".

## What it fixes

- One pipe (`%>%` or `|>`) per line, next verb indented two spaces.
- Pipelines right-assign into a name with `-> name`, so a chain can be run top-down while exploring.
- Multi-argument calls expand: `(` at line end, one argument per line, `)` on its own line.
- ggplot layers break with `+` at the end of each line.
- Two-space indentation that nests; modern comma and operator spacing.

## Files

- [`claude/SKILL.md`](claude/SKILL.md) - Claude version (Claude-safe frontmatter, description <= 200 chars).
- [`codex/SKILL.md`](codex/SKILL.md) - Codex version, same body.

## Edit rule

The two `SKILL.md` bodies are identical and only the frontmatter differs. Change both.

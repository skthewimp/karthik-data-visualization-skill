# Devlog

## 2026-06-19 - Dataviz selector skill session

### User prompts

> "i already have one data visualisatiohn skill. now i want to build one more to pick the right kind of visualisation for a given data set / problem statementt."

> "check out my old blog visualisations.substack.com where i've commented on various visualisations. both good and bad."

> "also mine my Mint articles (Mint folder here) to get more insgihts from there. also powerpoints in this folder with datavizs."

> "ok now put all this together to make a skill."

> "ok now put this skill as well into this git https://github.com/skthewimp/karthik-data-visualization-skill"

### Work done

- Built a new public `dataviz-selector` skill to choose chart forms from a dataset plus question/hypothesis/story.
- Calibrated the skill from Karthik's Mint articles, local PowerPoints, Substack visualisation critiques, and one-at-a-time user feedback on chart-choice scenarios.
- Added hard guardrails against pie, donut, 3D, animated, interactive-first, gauge, radar/spider, and decorative infographic recommendations.
- Red-teamed the selector with out-of-sample prompts and rendered local examples from fuel-price, small-airport, and management PBT-miss data.
- Added the skill to this public repo, updated `sync-skills.py` to build/install multiple skills, generated Codex and Claude distributions, and pushed commit `df5c507`.
- Added repo documentation, skill docs, this devlog, and a short blog-style writeup about the process.
## 2026-06-19 - Navigation docs preference

- Repo should be easy for a new person to navigate from GitHub alone.
- Keep README files in every public folder, including skill folders and `codex/` / `claude/` subfolders.
- Do not expose private `references/` or `scripts/`; those stay local-only and ignored.

## 2026-06-24 - PowerPoint style skill

- Added `karthik-powerpoint-style` as a third public skill, with both `codex/SKILL.md` and `claude/SKILL.md` to match the repository's per-skill surface layout.
- The skill captures reusable instructions for making analytical PowerPoint-style slides in Karthik's style: claim-first titles, sparse layouts, direct labels, chart-first evidence, minimal decoration, source notes, and management-ready slide patterns.
- Added folder-level READMEs for the new skill and a human guide at `docs/skills/karthik-powerpoint-style.md` so a new GitHub reader can navigate the skill without prior context.
- Updated the root README and docs index to describe how the PowerPoint skill relates to `dataviz-selector` and `karthik-data-visualization`.


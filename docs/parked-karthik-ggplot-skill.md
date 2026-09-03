# Parked: `karthik-ggplot` skill (code-efficiency for weak models)

**Status:** PARKED 2026-09-03. Design agreed, corpus surveyed, not built. Resume from "Next step".

## Problem
The dataviz-fix / dataviz-construct build stage makes weak models free-write ggplot R.
Output is way too verbose (~250 lines for a ~60-line chart). Example anti-patterns seen:
base-R `matrix()`/`as.vector(t())`/`ave()`/`df$col <-`, hand-typed coordinates that
duplicate a data row (`endpoint_values <- c(37,17,...)`), a 45-line `theme()` block retyped
per chart, `labels = function(x) paste0(x,"%")` instead of `scales::percent`.

## What this skill is / is NOT
- IS: a **code-efficiency rule set** for writing concise ggplot R. About *coding style*, not chart look.
- NOT: a frozen theme / palette / house visual style. Theme varies per prompt — do not hardcode one.
- NOT: an R package (render contract is a single self-contained `.R` file `source()`d into a
  fresh process with ggplot2/ragg/grid preloaded — see `dataviz_mcp/rendering.py:557-563`; a
  package would need installing in every render env = harness-coupling, ruled out).

## Decisions locked
- Scope = **both** standalone ("write ggplot in my style") AND referenced by the build stage (option 3).
- Approach = **lean rules skill** (not a helper/theme snippet package — the earlier "Approach A"
  helper block was dropped because the theme legitimately varies per prompt).
- No hardcoded cases (matches memory `no-hardcoded-cases-in-skill-rules`).
- Not frozen in time (see "Non-frozen framing").

## The rule set (each = durable principle + current idiom + before→after pair)
1. dplyr pipeline for data shaping — never base-R `matrix`/`ave`/`as.vector`/`df$x<-`/`order`/`rep`.
2. Vectorized window fns (`cumsum`/`lag`/`lead`/`cummean`/`row_number`) — never loops/`ave` for running/offset calcs.
3. purrr `map_*`/`reduce`/`accumulate` for iteration — not `for`/`sapply`/`lapply`.
4. `pivot_longer` to feed ggplot tidy long data (not hand-built long frames).
5. Derive every number from data (`filter(period==max(period))`, `slice_max`, `max`, `last`) — never hand-type a value that exists in the data.
6. `scales::` for axis/label number formatting (`percent`/`comma`/`label_number_si`) — never hand-rolled formatter functions.
7. ggrepel for label placement — not hand-typed x/y coordinates.

Anti-pattern → rule map (from the real verbose example):
| Anti-pattern | Rule |
|---|---|
| `matrix()`+`as.vector(t())` | 1, 4 |
| `ave(x, FUN=cumsum)` | 2 |
| `endpoint_values <- c(37,17,..)` (retyped data row) | 5 |
| `labels = function(x) paste0(x,"%")` | 6 |
| hand-placed `geom_text` x/y | 7 |
| base-R `df$col <-`, `order()`, `rep()` | 1 |

## Non-frozen framing (required)
Meta-rule at top of SKILL.md:
> These rules name the efficient idiom *as of writing*. The durable goal is concision and
> deriving-from-data. If a clearly better or now-standard tool exists when you write, prefer it —
> the named packages (tidyverse, ggrepel, scales) are current best examples, not a required list.
Each rule states the durable principle first, the current package as a swappable example.
Do not pin versions. `%>%` or `|>` both fine (`%>%` is just what Karthik learned first).

## Corpus evidence (post-2019 `~/Documents/work`, 285 ggplot files)
Coding-style signals (this is what the skill encodes):
- dplyr verbs heavy: mutate 5724, filter 5005, group_by 2833, summarise 2275, arrange 1805, count 1002.
- Vectorized windows: lag 505, cumsum 465, lead 65, row_number 33. purrr map* ~320 > sapply 62/lapply 22.
- `scales::` formatting 600+ (percent/label_percent/comma/label_number_si). `slice_max` for top-n, `fct_reorder` for ordering.
- ggrepel: geom_text_repel 45 across 27 files (used, not dominant — but the right tool vs hand-placed geom_text 597).
Chart-style signals (NOT part of this skill — surveyed then set aside as out-of-scope):
- theme_minimal base, Inter font, Set1 Brewer palette default, legend="none" + direct labels.
- Karthik already hand-rolls reusable theme fns per project (theme_babbage/theme_report/theme_analysis) —
  but theme content stays prompt-driven, so no frozen theme in the skill.

## Build plan (when resumed)
- `karthik-ggplot/{claude,codex}/SKILL.md` in the repo's existing skill format.
- Wire one pointer into the ggplot build stage (build happens in dataviz-construct stage 4 under
  `karthik-data-visualization`): "when builder=ggplot, follow karthik-ggplot code rules".
- Update folder README, root README, `docs/skills/`, docs index, CHANGELOG, DEVLOG.
- Run `./sync.sh --no-pull` to validate + install codex/claude copies. Commit + push.

## Open items
- Final name: `karthik-ggplot` vs a code-focused name (`concise-r-ggplot`). Unresolved.
- Ceremony (formal spec-doc + reviewer subagent loop) vs build-direct. Unresolved.

## Next step
Confirm name, then build the two SKILL.md files from the rule set above and wire + document + sync.

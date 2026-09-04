---
name: dataviz-color
description: Choose and assign colours for a specific chart (or a colour-formatted table). Use whenever a visualization needs a palette - picking series colours, assigning hues to categories, checking a palette for accessibility, honouring a brand palette, or seeding colours from a source chart during repair. Decides which colours to use from an available set and how to assign them, by contrast, adjacent-series distinctness, colour-vision-deficiency and grayscale survival, and focal-colour-plus-grey emphasis. Brand or style guidance, whether from an installed brand skill or supplied in the prompt, takes precedence over defaults, but a specific graph still needs a which-and-how-assigned decision. WCAG is a soft diagnostic, not a hard gate.
metadata:
  short-description: Choose accessible, brand-aware colours for a specific graph
  claude-description: Choose and assign chart colours for a specific graph - by contrast, series distinctness, CVD and grayscale survival, and focal-plus-grey. Brand takes precedence; WCAG is a soft target.
---

# Dataviz Colour

Own the colour decision for one visualization: which colours to use and how to assign them to this chart's series or categories. This is a *decision for the specific graph*, not a palette look-up - even with a brand palette or recommended set in hand, a chart with N series and a given background still needs a call on which to use and how to assign them. Don't design the form, write annotations, or set number precision (those belong to `karthik-data-visualization`, `chart-annotations`, `dataviz-precision`).

The mechanical checks live in the dataviz MCP: `recommend_colours`, `validate_palette`, `extract_palette_from_image`. Use them; keep the judgement here. Inside the construct pipeline, that judgement (available source, focal series, semantic meaning) is made at `select` as a compact `colour_plan`, resolved by `recommend_colours`, and applied at build - so this full skill is the standalone authority the plan distils, not a body loaded into the build call.

## 1. Where the available colours come from (precedence, higher wins)

1. **A brand or style skill, if installed.** Scan the available-skills list for a name matching `brand`, `style`, `design-system`, `theme`, or `palette`; if one exists, invoke it and honour its palette and forbidden colours. The usual way a brand arrives.
2. **Colours or style guidance in the prompt/context** - hex values, a named palette, "use our greens", a pasted style guide. Honour these too.
3. **Accessibility defaults** when neither exists: colour-blind-safe starting palettes (Okabe-Ito, ColorBrewer, viridis).

Whatever wins defines the *available set* - the input to the decision, not the answer.

## 2. How many colours (max series per panel, not total categories)

Size the palette to the **maximum number of series sharing a single panel** that must be told apart by colour - a property of the form, not the total category count. N lines in one panel need N. Small multiples with k lines *per panel* need k (reused across panels), not the total across panels. Small multiples with one line per panel, direct labels, or position carrying identity need 0. Focal-plus-grey needs 1. Take that count as `n_series` (or use the count an upstream step handed you). When it's 0 there is no colour decision.

## 3. Always recommend for the specific graph

Call `recommend_colours(available, colour_groups, background, focal)`. It picks and assigns by maximising the minimum separation between series while keeping each readable against the background, and pins `focal` to the first series. The returned palette is **ordered and prefix-nested** (`ordered_palette`): the first *m* colours are themselves a good *m*-colour palette, so a panel with fewer series uses the first that many and the mapping stays consistent across panels. Read its `rationale`, `shortfall`, `suggested_additions`:

- Available set **too small** for the series count → add the suggested additions/substitutions or collapse series, rather than reusing a hue.
- Colours **dropped for low background contrast** → respect it; a light mark on a light ground is not a real option for a thin line (a large fill tolerates less).

Picking a subset from an available set is the normal case.

## 3b. Semantic colour - use it whenever it fits

When a series carries a colour meaning the reader already holds - a "loss" that reads red, an "ocean" that reads blue, a party or brand with a known colour - honour it; a semantically apt colour is understood before the legend. Reach for this by default when appropriate, and stand down only when something argues against it: the prompt or brand guidance says not to; the convention isn't shared by *this* audience (colour meaning is culture-relative - red is loss in US markets, gain in Indian and Chinese ones - so decide in context, never from a fixed table); or it costs accessibility (a red/green polarity collapsing under CVD - prefer blue/orange).

You own which series means what, and its *away kit*. Pass it as `semantic_hints`:

- `{"series_index": i, "colour": "#hex"}` - a hard pin, for an exact colour (brand red, fixed party colour).
- `{"series_index": i, "hue_family": "blue"}` - a **soft family** (the usual case): name the hue family and `recommend_colours` picks the nearest in-family colour from the available set, so brand and accessibility still shape the shade.
- Add `"alternates": [...]` (colours or family words) as **away kits** for when a series' colour would clash.

**Priority the tool enforces:** (1) series stay distinguishable - the near-hard bar; (2) semantic meaning outranks accessibility - a soft family may take a low-contrast or CVD-weaker in-family colour and is honoured, not vetoed (`validate_palette` still flags it); (3) contrast/CVD/grayscale are soft diagnostics. Meaning wins over accessibility, but never at the cost of two series collapsing into one colour.

**Away kits (the football rule).** When two series' colours would clash, one keeps home and the other switches to an away kit - a *different but still-its-own* colour from `alternates`, not a mechanical darkening. Home is kept for hard pins, then `focal`, then the lower `series_index`; the clashing series takes the first away kit that separates. With no clearing away kit the tool **keeps home and flags `semantic_collision`** - it never silently reskins a series you didn't give an alternate for; supply one that still reads as its own, or merge the series. Read `semantic_findings`: `semantic_unmet` = no in-family colour available (add one or accept the separation pick); `semantic_collision` = resolve with an away kit. Hints make positions identity-bound, so the palette is no longer prefix-nested (`prefix_nested: false`) - expected. Use semantic colour where meaning earns a hue, not to colour every series.

## 4. Defaults and craft rules (when choosing freely)

- **Focal colour plus grey.** One series focal; the rest muted grey context, unless every series genuinely competes for attention.
- **Adjacent regions differ in hue AND lightness** - never hue alone, especially stacked or touching areas.
- **Don't rely on hue to carry meaning**; avoid red-versus-green as the only distinction.
- **WCAG soft targets:** ~4.5:1 normal text, 3:1 large text, 3:1 against background for small/thin essential marks. Diagnostic, not a gate.

## 5. Repair: source colours are a prior, not a rule

Run `extract_palette_from_image(image_path)` to read the source's dominant hues. Treat them as a **prior**: feed them as the `available` set or a `focal` hint and keep the semantic mapping (which series a colour stands for), then override any specific hue freely for brand or accessibility. Preserve the mapping; don't defend the exact colours.

## 6. Validate and iterate

Run `validate_palette(colours, background)` on the assignment. It soft-fails on background contrast, adjacent-series distinctness, CVD (deutan/protan/tritan), and grayscale, each with a concrete nudge. Act on them (lighten/darken to separate, or shift a hue) and re-check. A `soft_fail` is guidance, not a stop - accessible multi-colour palettes on white are genuinely hard, so weigh the findings against how the chart is actually read.

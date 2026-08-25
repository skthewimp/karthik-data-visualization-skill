---
name: dataviz-color
description: Choose and assign colours for a specific chart (or a colour-formatted table). Use whenever a visualization needs a palette - picking series colours, assigning hues to categories, checking a palette for accessibility, honouring a brand palette, or seeding colours from a source chart during repair. Decides which colours to use from an available set and how to assign them, by contrast, adjacent-series distinctness, colour-vision-deficiency and grayscale survival, and focal-colour-plus-grey emphasis. Brand or style guidance, whether from an installed brand skill or supplied in the prompt, takes precedence over defaults, but a specific graph still needs a which-and-how-assigned decision. WCAG is a soft diagnostic, not a hard gate.
metadata:
  short-description: Choose accessible, brand-aware colours for a specific graph
  claude-description: Choose and assign chart colours for a specific graph - by contrast, series distinctness, CVD and grayscale survival, and focal-plus-grey. Brand takes precedence; WCAG is a soft target.
---

# Dataviz Colour

Own the colour decision for one visualization: which colours to use and how to assign them to this chart's series or categories. This is a *decision for the specific graph*, not a palette look-up. Even when a brand palette or a set of recommended colours already exists, a chart with N series and a given background still needs a call on which of them to use and how to assign them. Do not design the chart's form, write its annotations, or set its number precision - those belong to `karthik-data-visualization`, `chart-annotations`, and `dataviz-precision`.

The mechanical checks live in the dataviz MCP: `recommend_colours`, `validate_palette`, `extract_palette_from_image`. Use them; keep the judgement here.

## 1. Where the available colours come from (precedence, higher wins)

1. **A brand or style skill, if one is installed.** Scan the session's available-skills list for a skill whose name matches `brand`, `style`, `design-system`, `theme`, or `palette`. If one exists, invoke it and honour its palette and any forbidden colours. This is the usual way a brand arrives - as an installed skill - though it is not the only way.
2. **Colours or style guidance supplied in the prompt or context.** Hex values, a named palette, "use our greens", a linked style guide pasted into the conversation. Honour these too.
3. **Our accessibility defaults** when neither exists: colour-blind-safe starting palettes - Okabe-Ito, ColorBrewer, or viridis.

Whatever wins defines the *available set*. The available set is the input to the decision, not the answer.

## 2. How many colours (max series per panel, not total categories)

The palette size is decided upstream by the select stage and handed to you as `design.colour_groups`. It is the **maximum number of series that share a single panel** and must be told apart by colour - a property of the form, not the total category count. N lines in one panel need N. Small multiples with k lines *per panel* need k (the same k colours reused across panels) - not 0, and not the total across panels. Small multiples with one line per panel, direct labels, or position carrying identity need 0. Focal-plus-grey needs 1. Use `design.colour_groups` as `n_series`; if it is 0, there is no colour decision to make (the build already skipped this skill via `needs_color_plan`).

## 3. Always recommend for the specific graph

Call `recommend_colours(available, colour_groups, background, focal)`. It picks and assigns colours by maximising the minimum separation between series while keeping each readable against the background, and pins a `focal` colour to the first series. The returned palette is **ordered and prefix-nested** (`ordered_palette`): the first *m* colours are themselves a good *m*-colour palette, so a panel with fewer series than the maximum uses the first that many colours, and the mapping stays consistent across panels. Read its `rationale`, `shortfall`, and `suggested_additions`:

- If the available set is **too small** for the series count, it says so and suggests the minimal additions or substitutions. Add them, or collapse series, rather than reusing a hue.
- If colours are **dropped for low background contrast**, respect that - a light mark on a light ground is not a real option for a thin line, though a large fill tolerates less.

Picking a subset from an available set is the normal case, not an exception.

## 3b. Semantic colour - use it whenever it fits

When a series *carries a colour meaning* the reader already holds, honour it. A "loss" series that reads red, an "ocean" series that reads blue, a party or brand with a known colour - a semantically apt colour is understood before the legend is. Reach for this **by default whenever you judge it appropriate**, and stand down only when something argues against it: the prompt or brand/style guidance says not to, the convention is not shared by *this* audience (colour meaning is culture-relative - red is loss in US markets, gain in Indian and Chinese ones - so decide the meaning in context, never from a fixed table), or it would cost accessibility (a red/green polarity that collapses under CVD - prefer blue/orange).

You own the judgement of which series means what - and what its *away kit* is. Pass it to the tool as `semantic_hints` - a list of:

- `{"series_index": i, "colour": "#hex"}` - a hard pin, when you want an exact colour (a brand red, a fixed party colour).
- `{"series_index": i, "hue_family": "blue"}` - a **soft family** (the usual case): you name the hue family and `recommend_colours` picks the nearest in-family colour from the available set, so brand and accessibility still shape the exact shade.
- Add `"alternates": [...]` (colours or family words) as **away kits** for when a series' colour would clash with another's - see below.

**Priority the tool enforces:** (1) series must stay distinguishable from each other - this is the near-hard bar; (2) semantic meaning outranks accessibility - a soft family may take a low-contrast or CVD-weaker in-family colour, and it is honoured, not vetoed (`validate_palette` still flags the contrast); (3) contrast/CVD/grayscale are soft diagnostics. So meaning wins over accessibility, but never at the cost of two series collapsing into the same colour.

**Away kits (the football rule).** When two series' colours would clash, one keeps its home colour and the other switches to an away kit - a *different but still-its-own* colour you supplied in `alternates`, not a mechanical darkening. Home is kept for hard pins, `focal`, then the lower `series_index`; the clashing series takes the first away kit that separates. If a clashing series has no away kit that clears, the tool **keeps its home colour and flags `semantic_collision`** - it never silently reskins a series you didn't give an alternate for. When you see that flag, give that series an away-kit colour that still reads as its own, or merge the two series.

The tool fills every un-hinted series by max-min separation. Read `semantic_findings`: `semantic_unmet` means the available set had no colour in that family (add one, or accept the separation pick); `semantic_collision` means a clash you need to resolve with an away kit. Hints make positions identity-bound, so the palette is no longer prefix-nested (`prefix_nested: false`); that is expected. Semantic colour still competes with focal-plus-grey (section 4) - use it where the meaning earns a hue, not to colour every series just because you can.

## 4. Defaults and craft rules (when choosing freely)

- **Focal colour plus grey.** One series in the focal colour; the rest muted grey context, unless every series genuinely competes for attention.
- **Adjacent regions differ in hue AND lightness** - never hue alone. Stacked or touching areas especially.
- **Do not rely on hue to carry meaning**; avoid red-versus-green as the only distinction.
- **WCAG soft targets:** roughly 4.5:1 for normal chart text, 3:1 for large text, 3:1 against the background for small or thin essential marks. Diagnostic, not a gate - "not very strict".

## 5. Repair: source colours are a prior, not a rule

In a chart repair, run `extract_palette_from_image(image_path)` to read the source's dominant hues. Treat them as a **prior**: feed them in as the `available` set or as a `focal` hint, and keep the semantic mapping (which series a colour stands for). Then override any specific hue freely for brand or accessibility. Preserve the mapping; do not defend the exact colours.

## 6. Validate and iterate

Run `validate_palette(colours, background)` on the assignment. It reports soft-fails on background contrast, adjacent-series distinctness, colour-vision-deficiency (deutan/protan/tritan), and grayscale, each with a concrete nudge. Act on them: lighten/darken to separate, or shift a hue. Re-check. A `soft_fail` is guidance, not a stop - accessible multi-colour palettes on a white ground are genuinely hard, so weigh the findings against how the chart is actually read.

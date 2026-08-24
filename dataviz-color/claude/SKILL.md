---
name: dataviz-color
description: Choose and assign chart colours for a specific graph - by contrast, series distinctness, CVD and grayscale survival, and focal-plus-grey. Brand takes precedence; WCAG is a soft target.
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

## 2. How many colours (a property of the encoding, not the data)

The number of colours is decided upstream by the select stage and handed to you as `design.colour_groups`. It is **not** the number of series or categories - it is how many distinct colours *this encoding* actually needs. Five series shown as five lines in one panel need five colours; the same five as small multiples need none, because the facet carries identity, not hue. Focal-plus-grey needs one. Direct-labelled or position-carried identity needs none. Use `design.colour_groups` as `n_series`; if it is 0, there is no colour decision to make (the build already skipped this skill via `needs_color_plan`).

## 3. Always recommend for the specific graph

Call `recommend_colours(available, colour_groups, background, focal)`. It picks and assigns colours by maximising the minimum separation between series while keeping each readable against the background, and pins a `focal` colour to the first series. Read its `rationale`, `shortfall`, and `suggested_additions`:

- If the available set is **too small** for the series count, it says so and suggests the minimal additions or substitutions. Add them, or collapse series, rather than reusing a hue.
- If colours are **dropped for low background contrast**, respect that - a light mark on a light ground is not a real option for a thin line, though a large fill tolerates less.

Picking a subset from an available set is the normal case, not an exception.

## 4. Defaults and craft rules (when choosing freely)

- **Focal colour plus grey.** One series in the focal colour; the rest muted grey context, unless every series genuinely competes for attention.
- **Adjacent regions differ in hue AND lightness** - never hue alone. Stacked or touching areas especially.
- **Do not rely on hue to carry meaning**; avoid red-versus-green as the only distinction.
- **WCAG soft targets:** roughly 4.5:1 for normal chart text, 3:1 for large text, 3:1 against the background for small or thin essential marks. Diagnostic, not a gate - "not very strict".

## 5. Repair: source colours are a prior, not a rule

In a chart repair, run `extract_palette_from_image(image_path)` to read the source's dominant hues. Treat them as a **prior**: feed them in as the `available` set or as a `focal` hint, and keep the semantic mapping (which series a colour stands for). Then override any specific hue freely for brand or accessibility. Preserve the mapping; do not defend the exact colours.

## 6. Validate and iterate

Run `validate_palette(colours, background)` on the assignment. It reports soft-fails on background contrast, adjacent-series distinctness, colour-vision-deficiency (deutan/protan/tritan), and grayscale, each with a concrete nudge. Act on them: lighten/darken to separate, or shift a hue. Re-check. A `soft_fail` is guidance, not a stop - accessible multi-colour palettes on a white ground are genuinely hard, so weigh the findings against how the chart is actually read.

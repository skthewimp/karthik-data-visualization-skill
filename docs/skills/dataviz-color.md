# Dataviz Colour Skill

`dataviz-color` owns the colour decision for one visualization: which colours to use and how to assign them to a chart's series or categories.

It exists because a palette is not a colour decision. A brand book gives you eight hues; a specific chart has five series on a white background and needs a call on which five to use, which one leads, and whether any pair collapses for a colour-blind reader. That call is the same whether the colours come from a brand, from the prompt, or from our defaults - so the skill always makes it for the specific graph.

## Where colours come from (precedence)

1. A brand or style skill, if one is installed - detected by scanning the session's available-skills list for a name matching `brand`, `style`, `design-system`, `theme`, or `palette`. Its palette and forbidden colours win.
2. Colours or style guidance supplied directly in the prompt or context.
3. Our accessibility defaults - Okabe-Ito, ColorBrewer, or viridis - when neither exists.

Whatever wins is the *available set*, the input to the decision, not the answer.

## What it does

- **`recommend_colours`** (MCP tool) picks and assigns colours from the available set by maximising the minimum separation between series while keeping each readable against the background, pins a focal colour to the lead series, and reports any shortfall with suggested additions. It also accepts `semantic_hints` - hard pins (`{"series_index": i, "colour": "#hex"}`) or soft hue families (`{"series_index": i, "hue_family": "blue"}`), each with optional `alternates` away-kits - that the model judges appropriate for a series' meaning. It reconciles under a fixed priority: series stay distinguishable (hard), meaning outranks contrast/CVD (a soft family may take a low-contrast colour), and a home colour that clashes with a placed series moves to its first clearing away-kit or, with none, is kept and flagged `semantic_collision` rather than silently reskinned. Semantic colour is used by default when a series carries a colour meaning, unless the prompt, brand, audience, or accessibility argues against it.
- **`validate_palette`** (MCP tool) scores a palette on WCAG background contrast, adjacent-series distinctness, colour-vision-deficiency (deutan/protan/tritan), and grayscale, returning soft-fail findings each with a concrete nudge.
- **`extract_palette_from_image`** (MCP tool) samples a source chart's dominant hues during a repair, so those colours become a *prior* the skill may override for brand or accessibility while keeping the semantic mapping.

WCAG is treated as a soft diagnostic, not a hard gate - accessible multi-colour palettes on a white ground are genuinely hard, and the findings are weighed against how the chart is actually read.

The installable skill lives in `dataviz-color/{codex,claude}/SKILL.md`.

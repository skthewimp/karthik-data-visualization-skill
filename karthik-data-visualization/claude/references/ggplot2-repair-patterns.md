# ggplot2 repair patterns

Use these as structural starting points. Replace fields, copy, scales, palettes, and dimensions from the active implementation contract. Every source file must expose `build_chart()` and return chart metadata with evidence scope, chart form, identification route, zones, colour role, dimensions, and value precision.

## Shared contract

```r
chart_result <- function(plot, form, identification, colour_role, precision = "exact") {
  list(
    plot = plot,
    metadata = list(
      evidence_scope = "Replace with the supplied evidence boundary",
      chart_form = form,
      primary_identification = identification,
      colour_role = colour_role,
      value_precision = precision,
      zones = list(
        title = "claim or question",
        subtitle = "measure, universe, and period",
        legend = "none unless it is the clearest identification route",
        plot = "primary comparison",
        annotation = "supported context only",
        footer = "source and evidence limitations"
      )
    )
  )
}
```

## Sorted horizontal bars

```r
build_chart <- function() {
  frame <- transform(frame, category = reorder(category, value))
  plot <- ggplot2::ggplot(frame, ggplot2::aes(value, category)) +
    ggplot2::geom_col(width = 0.66, fill = "#245b78") +
    ggplot2::geom_text(ggplot2::aes(label = scales::label_number()(value)),
                       hjust = -0.12, colour = "#1f1f1f") +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0, 0.12))) +
    ggplot2::labs(title = "Replace with the supported claim", x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
  chart_result(plot, "sorted horizontal bars", "categorical axis", "none")
}
```

## Diverging bars

```r
build_chart <- function() {
  frame$direction <- ifelse(frame$change >= 0, "increase", "decrease")
  frame$category <- reorder(frame$category, frame$change)
  palette <- c(increase = "#256d4a", decrease = "#a43c3c")
  plot <- ggplot2::ggplot(frame, ggplot2::aes(change, category, fill = direction)) +
    ggplot2::geom_col(width = 0.66) +
    ggplot2::geom_vline(xintercept = 0, colour = "#696969", linewidth = 0.4) +
    ggplot2::geom_text(ggplot2::aes(label = scales::label_percent(accuracy = 0.1)(change),
                                    hjust = ifelse(change >= 0, -0.12, 1.12)),
                       colour = "#1f1f1f") +
    ggplot2::scale_fill_manual(values = palette, guide = "none") +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = 0.15)) +
    ggplot2::labs(title = "Replace with the stated comparison direction", x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(panel.grid = ggplot2::element_blank())
  chart_result(plot, "diverging bars", "categorical axis plus signed labels", "direction")
}
```

## Slopegraph

```r
build_chart <- function() {
  endpoints <- subset(frame, period %in% c(min(period), max(period)))
  plot <- ggplot2::ggplot(endpoints, ggplot2::aes(period, value, group = entity)) +
    ggplot2::geom_line(colour = "#9b9b9b", linewidth = 0.7) +
    ggplot2::geom_point(colour = "#245b78", size = 2.2) +
    ggplot2::geom_text(ggplot2::aes(label = paste0(entity, "  ", value),
                                    hjust = ifelse(period == min(period), 1, 0)),
                       nudge_x = ifelse(endpoints$period == min(endpoints$period), -0.03, 0.03)) +
    ggplot2::scale_x_continuous(breaks = sort(unique(endpoints$period)),
                                expand = ggplot2::expansion(mult = c(0.24, 0.24))) +
    ggplot2::labs(title = "Replace with the endpoint-change claim", x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(panel.grid = ggplot2::element_blank(), axis.text.y = ggplot2::element_blank())
  chart_result(plot, "slopegraph", "complete endpoint labels", "identity only if needed")
}
```

Choose height from entity count and endpoint-label geometry. Inspect both endpoint columns and the closest pair of labels; change the form when pairing cannot remain immediate at delivery size.

## Direct-labelled trends

```r
build_chart <- function() {
  endpoints <- frame[ave(frame$period, frame$series, FUN = function(x) x == max(x)) == 1, ]
  plot <- ggplot2::ggplot(frame, ggplot2::aes(period, value, colour = series)) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_text(data = endpoints, ggplot2::aes(label = series),
                       hjust = 0, nudge_x = 0.03, show.legend = FALSE) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = c(0.02, 0.18))) +
    ggplot2::guides(colour = "none") +
    ggplot2::labs(title = "Replace with the supported trend claim", x = NULL, y = "Unit") +
    ggplot2::theme_minimal(base_size = 12)
  chart_result(plot, "direct-labelled trends", "right endpoint labels", "series identity")
}
```

Do not remove the legend until every series has one legible, correctly coloured endpoint label. Remove redundant categorical scaffolding, but retain quantitative axes that still support comparison.

## Multi-panel charts

```r
build_chart <- function() {
  plot <- ggplot2::ggplot(frame, ggplot2::aes(period, value, colour = series)) +
    ggplot2::geom_line(linewidth = 0.8) +
    ggplot2::facet_wrap(~ panel, scales = "free_y") +
    ggplot2::labs(title = "Replace with the cross-panel question", x = NULL, y = "Unit") +
    ggplot2::theme_minimal(base_size = 11) +
    ggplot2::theme(panel.grid.minor = ggplot2::element_blank(),
                   strip.text = ggplot2::element_text(face = "bold"))
  chart_result(plot, "small multiples", "shared legend or complete labels in every panel",
               "consistent series identity across panels")
}
```

Enumerate expected panels and repeated labels in the inspection contract. Inspect every panel, every strip, the shared legend, neighbouring zones, and the densest repeated placement before evaluation.

build_chart <- function() {
  d <- data.frame(
    x   = c(2, 5, 8),
    y   = factor(c("A", "B", "C"), levels = c("A", "B", "C")),
    grp = c("one", "two", "one")
  )
  pal <- c(one = "#0060A0", two = "#8A5300")
  # An in-panel direct label. Before the guide-box-inside fix this collided with a
  # phantom panel-sized "legend" that ggplot emits when the colour guide is off.
  lab <- data.frame(x = 8, y = factor("C", levels = levels(d$y)), t = "inside label")
  plot <- ggplot2::ggplot(d, ggplot2::aes(x, y, colour = grp)) +
    ggplot2::geom_point(size = 4) +
    ggplot2::geom_text(
      data = lab, ggplot2::aes(x = x, y = y, label = t),
      colour = "#0060A0", vjust = -1.2, inherit.aes = FALSE
    ) +
    ggplot2::scale_colour_manual(values = pal, guide = "none") +
    ggplot2::scale_x_continuous(limits = c(0, 10)) +
    ggplot2::labs(title = "No-legend fixture", x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = 12)
  list(plot = plot, metadata = list(chart_form = "points"))
}

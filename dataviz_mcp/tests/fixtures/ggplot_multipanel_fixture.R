build_chart <- function() {
  frame <- data.frame(
    panel = rep(c("North", "South"), each = 3),
    period = rep(1:3, 2),
    value = c(2, 4, 5, 5, 3, 6)
  )
  plot <- ggplot2::ggplot(frame, ggplot2::aes(period, value, group = panel)) +
    ggplot2::geom_line(colour = "#245b78", linewidth = 0.8) +
    ggplot2::geom_point(colour = "#245b78", size = 2) +
    ggplot2::facet_wrap(~panel, nrow = 1) +
    ggplot2::labs(title = "Two-panel capture", x = NULL, y = "Value") +
    ggplot2::theme_minimal(base_size = 12)
  list(plot = plot, metadata = list(chart_form = "small-multiple trends"))
}

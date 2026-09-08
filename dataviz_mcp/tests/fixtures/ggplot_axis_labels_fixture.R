build_chart <- function() {
  frame <- data.frame(
    category = factor(
      c("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"),
      levels = c("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot")
    ),
    value = c(4, 7, 5, 8, 3, 6)
  )
  plot <- ggplot2::ggplot(frame, ggplot2::aes(category, value)) +
    ggplot2::geom_col(fill = "#245b78", width = 0.65) +
    ggplot2::labs(
      title = "Per-tick axis labels must be individually inspectable",
      x = "Category",
      y = "Value"
    ) +
    ggplot2::theme_minimal(base_size = 12)
  list(plot = plot, metadata = list(chart_form = "vertical bars"))
}

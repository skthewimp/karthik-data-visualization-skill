build_chart <- function() {
  frame <- data.frame(
    category = factor(c("A", "B", "C"), levels = c("C", "B", "A")),
    value = c(4, 7, 5)
  )
  plot <- ggplot2::ggplot(frame, ggplot2::aes(category, value)) +
    ggplot2::geom_col(fill = "#245b78", width = 0.65) +
    ggplot2::coord_flip() +
    ggplot2::labs(
      title = "A deterministic ggplot2 fixture",
      subtitle = "Rendered through ragg",
      x = NULL,
      y = "Value",
      caption = "Source: fixture"
    ) +
    ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(panel.grid.major.y = ggplot2::element_blank())
  list(
    plot = plot,
    metadata = list(
      measure_scope = "Illustrative values",
      chart_form = "sorted horizontal bars"
    )
  )
}

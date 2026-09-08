build_chart <- function() {
  frame <- data.frame(category = c("A", "B"), value = c(4, 7))
  plot <- ggplot2::ggplot(frame, ggplot2::aes(category, value)) +
    ggplot2::geom_col(fill = "#245b78", width = 0.6) +
    ggplot2::labs(
      title = paste(
        "An extraordinarily and gratuitously long chart title that cannot",
        "possibly fit inside the rendered canvas width and therefore overflows"
      )
    ) +
    ggplot2::theme_minimal(base_size = 22)
  list(plot = plot, metadata = list(chart_form = "vertical bars"))
}

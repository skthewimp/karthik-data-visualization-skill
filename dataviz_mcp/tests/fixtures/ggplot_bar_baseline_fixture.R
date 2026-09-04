build_chart <- function() {
  frame <- data.frame(
    category = c("A", "B", "C", "D"),
    value = c(10, 40, 25, 60)
  )
  ggplot2::ggplot(frame, ggplot2::aes(category, value)) +
    ggplot2::geom_col(fill = "#4477aa", width = 0.8) +
    ggplot2::labs(title = "Vertical columns of differing height", y = "Value") +
    ggplot2::theme_minimal()
}

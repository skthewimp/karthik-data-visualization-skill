build_chart <- function() {
  frame <- data.frame(x = 1:4, y = c(2, 20, 200, 2000))
  ggplot2::ggplot(frame, ggplot2::aes(x, y)) +
    ggplot2::geom_point(size = 3) +
    ggplot2::scale_y_log10() +
    ggplot2::labs(title = "A log-y scatter") +
    ggplot2::theme_minimal()
}

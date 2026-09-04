build_chart <- function() {
  ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) +
    ggplot2::geom_point() +
    ggplot2::facet_wrap(~cyl, scales = "free") +
    ggplot2::labs(title = "Faceted, free scales") +
    ggplot2::theme_minimal()
}

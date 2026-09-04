build_chart <- function() {
  frame <- data.frame(
    category = c("A", "B", "C", "D"),
    value = c(10, 40, 25, 60)
  )
  # Each bar carries its value printed inside the bar (vjust pushes the text down from the top,
  # so the label box sits on the geom_col rect). ggplot cannot tag these as data labels, so the
  # adapter must infer that a text on a mark is that mark's value label - not an accidental overlap.
  ggplot2::ggplot(frame, ggplot2::aes(category, value)) +
    ggplot2::geom_col(fill = "#4477aa", width = 0.8) +
    ggplot2::geom_text(
      ggplot2::aes(label = value),
      vjust = 1.8, colour = "white"
    ) +
    ggplot2::labs(title = "Every column labelled with its value", y = "Value") +
    ggplot2::theme_minimal()
}

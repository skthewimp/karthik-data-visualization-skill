suppressPackageStartupMessages(library(gridExtra))
suppressPackageStartupMessages(library(grid))

build_table <- function() {
  df <- data.frame(
    Region = c("North", "South", "East"),
    Revenue = c("12.5", "8.3", "15.0"),
    Share = c("35%", "23%", "42%"),
    stringsAsFactors = FALSE
  )
  tableGrob(df, rows = NULL)
}

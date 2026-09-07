# Shared table constructor: build a gtable straight from a recommend_table_layout plan.
#
# The plan already carries the measured geometry - wrapped headers and cells, exact column
# widths, per-row heights, the header-band height, and per-role frame bands (title / subtitle /
# notes) each sized at its own font. This constructor applies that geometry verbatim, so a weak
# build model cannot re-normalise row positions or re-guess the frame and reintroduce the
# clipping the measurement removed. It returns a tableGrob-based gtable, so the geometry
# inspector still recognises every logical cell.
suppressPackageStartupMessages({
  library(gridExtra); library(grid); library(gtable); library(jsonlite)
})

build_table_from_plan <- function(plan_path, page = 1L) {
  plan <- fromJSON(plan_path, simplifyVector = FALSE)
  dpi <- as.numeric(plan$dpi)
  in_of <- function(px) as.numeric(px) / dpi                      # export px -> inches
  fam <- if (is.null(plan$font_family)) "sans" else plan$font_family
  body_pt <- as.numeric(plan$body_pt); header_pt <- as.numeric(plan$header_pt)
  px <- as.numeric(plan$padding_x_px); py <- as.numeric(plan$padding_y_px)

  pg <- plan$pages[[page]]
  col_idx <- unlist(pg$columns) + 1L                             # 0-based -> 1-based
  rr <- unlist(pg$rows); r0 <- rr[[1]] + 1L; r1 <- rr[[2]]       # half-open [start, end)
  headers <- unlist(plan$headers)[col_idx]
  col_cells <- lapply(col_idx, function(j) unlist(plan$cells[[j]])[r0:r1])
  m <- do.call(cbind, col_cells)
  colnames(m) <- headers

  pad <- unit(in_of(c(px, py)), "in")                         # plan padding is in export pixels
  th <- ttheme_minimal(
    base_family = fam, padding = pad,
    core = list(fg_params = list(fontsize = body_pt, fontfamily = fam)),
    colhead = list(fg_params = list(fontsize = header_pt, fontface = "bold", fontfamily = fam)))
  tg <- tableGrob(m, rows = NULL, theme = th)

  # Apply the measured geometry verbatim (tableGrob row 1 is the header, rows 2.. the body).
  # The plan's page width already reserves the widest frame band (a title wider than the
  # columns): widen the columns to fill that width so the band never overflows the table.
  col_w_px <- unlist(plan$col_widths_px)[col_idx]
  total_px <- max(sum(col_w_px), as.numeric(pg$width_px))
  surplus <- total_px - sum(col_w_px)
  if (surplus > 0) col_w_px <- col_w_px + surplus / length(col_w_px)
  tg$widths <- unit(in_of(col_w_px), "in")
  body_heights <- unlist(plan$row_heights_px)[r0:r1]
  tg$heights <- unit(in_of(c(plan$header_height_px, body_heights)), "in")

  add_band <- function(g, b, side) {
    h <- unit(in_of(b$height_px), "in")
    face <- if (isTRUE(b$bold)) "bold" else "plain"
    grob <- textGrob(b$text, x = unit(in_of(px), "in"), hjust = 0,
                     gp = gpar(fontsize = as.numeric(b$font_pt), fontfamily = fam, fontface = face))
    pos <- if (side == "top") 0 else -1
    g <- gtable_add_rows(g, h, pos = pos)
    row <- if (side == "top") 1 else nrow(g)
    gtable_add_grob(g, grob, t = row, l = 1, r = ncol(g), name = paste0("band_", b$role))
  }
  by_role <- function(role) Filter(function(b) identical(b$role, role), plan$frame_bands)
  for (b in by_role("notes"))    tg <- add_band(tg, b, "bottom")
  for (b in by_role("subtitle")) tg <- add_band(tg, b, "top")   # subtitle then title on top,
  for (b in by_role("title"))    tg <- add_band(tg, b, "top")   # so title ends as the top row
  tg
}

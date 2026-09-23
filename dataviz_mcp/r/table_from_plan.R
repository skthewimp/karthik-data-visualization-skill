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
  tg <- apply_cell_styles(tg, plan, col_idx, r0, r1, px, body_pt)

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

# Draw the plan's resolved treatments into the cells: alignment, heat fills with the ink each
# fill needs, bold focal text, data bars trailing their number, and sparklines. Every value
# here was computed by the planner; nothing is re-derived, so the drawn table is the plan.
apply_cell_styles <- function(tg, plan, col_idx, r0, r1, px, body_pt) {
  dpi <- as.numeric(plan$dpi)
  in_of <- function(v) as.numeric(v) / dpi
  align <- if (is.null(plan$col_align)) rep("left", length(plan$headers)) else unlist(plan$col_align)
  visual <- if (is.null(plan$visual_width_px)) rep(0, length(plan$headers)) else unlist(plan$visual_width_px)
  styles <- plan$cell_styles
  line_in <- body_pt / 72 * 1.25
  gap_in <- 0.4 * body_pt / 72
  for (k in seq_along(tg$grobs)) {
    item <- tg$layout[k, ]
    if (!item$name %in% c("core-fg", "colhead-fg")) next
    j <- col_idx[item$l]
    right <- identical(align[[j]], "right")
    g <- tg$grobs[[k]]
    # Body numbers sit left of their trailing graphic; a header spans the whole column.
    inset <- in_of(px) + if (item$name == "core-fg") in_of(visual[[j]]) else 0
    g$x <- if (right) unit(1, "npc") - unit(inset, "in") else unit(in_of(px), "in")
    g$hjust <- if (right) 1 else 0
    g$just <- if (right) "right" else "left"
    if (item$name == "core-fg" && !is.null(styles)) {
      st <- styles[[j]][[r0 + item$t - 2]]
      if (!is.null(st$ink)) g$gp$col <- st$ink
      if (isTRUE(st$bold)) { g$gp$font <- NULL; g$gp$fontface <- "bold" }
    }
    tg$grobs[[k]] <- g
  }
  # One rule under the header makes it a distinct layer from the body.
  tg <- gtable_add_grob(tg, linesGrob(x = unit(c(0, 1), "npc"), y = unit(c(0, 0), "npc"),
    gp = gpar(col = "#444444", lwd = 1), name = "rule-header"),
    t = 1, l = 1, r = ncol(tg), z = Inf, clip = "off", name = "rule-header")
  if (is.null(styles)) return(tg)
  for (l in seq_along(col_idx)) {
    j <- col_idx[[l]]
    vw <- in_of(visual[[j]])
    for (r in r0:r1) {
      st <- styles[[j]][[r]]
      t <- r - r0 + 2                                            # row 1 is the header
      tag <- paste0("-", j - 1, "-", r - 1)
      if (!is.null(st$fill)) {
        tg <- gtable_add_grob(tg, rectGrob(gp = gpar(fill = st$fill, col = NA),
          name = paste0("treat-fill", tag)), t = t, l = l, z = 0.5, clip = "off",
          name = paste0("treat-fill", tag))
      }
      # Graphic area: the reserved band at the cell's right, after the number-to-graphic gap.
      left <- unit(1, "npc") - unit(in_of(px) + vw - gap_in, "in")
      area <- unit(vw - gap_in, "in")
      if (!is.null(st$bar)) {
        b <- st$bar
        tg <- gtable_add_grob(tg, rectGrob(
          x = left + area * as.numeric(b$start), width = area * (as.numeric(b$end) - as.numeric(b$start)),
          height = unit(0.6 * line_in, "in"), just = c("left", "centre"),
          gp = gpar(fill = b$colour, col = NA), name = paste0("treat-bar", tag)),
          t = t, l = l, z = Inf, clip = "off", name = paste0("treat-bar", tag))
      }
      if (!is.null(st$spark)) {
        pts <- do.call(rbind, lapply(st$spark$points, function(p) as.numeric(unlist(p))))
        h <- 0.8 * line_in
        tg <- gtable_add_grob(tg, linesGrob(
          x = left + area * pts[, 1], y = unit(0.5, "npc") + unit((pts[, 2] - 0.5) * h, "in"),
          gp = gpar(col = st$spark$colour, lwd = 1.3), name = paste0("treat-spark", tag)),
          t = t, l = l, z = Inf, clip = "off", name = paste0("treat-spark", tag))
      }
    }
  }
  tg
}

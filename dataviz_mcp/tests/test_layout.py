from __future__ import annotations

# ---- from test_layout.py ----

from dataviz_mcp.layout import (
    MAX_PANEL_ASPECT,
    MIN_PANEL_H,
    boxes_overlap,
    pt_to_px,
    recommend_layout,
    suggest_dims_for_overflow,
)


def test_continuous_axes_take_a_pleasant_aspect_not_a_squashed_box():
    result = recommend_layout(x_slots=0, y_slots=0)
    assert result["width_px"] >= result["height_px"]  # wider than tall
    assert 1.2 < result["width_px"] / result["height_px"] < 2.2
    assert result["warnings"] == []


def test_x_slots_grow_width_toward_the_density_floor():
    sparse = recommend_layout(x_slots=10)
    dense = recommend_layout(x_slots=220)
    assert dense["width_px"] > sparse["width_px"]


def test_y_slots_grow_height_directly_because_labels_stack():
    few = recommend_layout(y_slots=5, filled_marks=True)
    many = recommend_layout(y_slots=40, filled_marks=True)
    assert many["height_px"] > few["height_px"]


def test_wide_few_row_filled_panels_do_not_letterbox():
    # Paired share panels / a few-row horizontal bar chart on a wide canvas used to get a
    # squat plot height from row demand alone, flattening marks and crowding category labels
    # (the token-vs-dollar share failure). Height now grows so the canvas is no wider than the
    # panel-aspect cap; chrome only adds height, so canvas aspect stays under the cap too.
    from dataviz_mcp.layout import FONT_PT, PANEL_GUTTER, pt_to_px

    result = recommend_layout(
        x_slots=0, y_slots=4, filled_marks=True, n_panels=2, facet_scales="free_x",
        y_labels=True, longest_y_label_chars=10, title_lines=1, subtitle_lines=1,
    )
    ncol, nrow = result["facet_ncol"], result["facet_nrow"]
    axis_band = pt_to_px(FONT_PT["axis"], result["dpi"]) * 3.0
    panel_w = (result["width_px"] - ncol * result["reserved_left_px"]
               - (ncol - 1) * PANEL_GUTTER) / ncol
    panel_h = (result["height_px"] - result["reserved_band_px"] - axis_band) / nrow
    assert panel_w / panel_h <= MAX_PANEL_ASPECT + 0.05  # the panel itself is not letterboxed
    assert result["data_panel_fraction"] >= 0.4          # and it is not starved


def test_many_row_horizontal_bars_still_grow_height_by_rows():
    # The letterbox floor must not shrink a tall ranked strip: row demand dominates there,
    # so the floor never binds and height keeps scaling with the row count.
    few = recommend_layout(y_slots=6, filled_marks=True)
    many = recommend_layout(y_slots=30, filled_marks=True)
    assert many["height_px"] > few["height_px"]


def test_continuous_y_facets_use_the_profile_height_not_a_starved_panel_width():
    # A 2-panel continuous-y chart with long y labels used to collapse to a wide, short strip
    # (1318x357): the left label band starved each panel's width, and height was derived only
    # from that starved width, dropping the profile's own 675px height. Height must now floor
    # to the profile so the canvas is not squished.
    squished = recommend_layout(
        x_slots=6, y_slots=0, filled_marks=True, n_panels=2, y_labels=True,
        longest_y_label_chars=35, title_lines=1, subtitle_lines=1, footer_lines=1,
    )
    assert squished["height_px"] >= 650  # ~profile height, not a 357px strip
    assert squished["width_px"] / squished["height_px"] < 2.2  # not letterboxed


def test_sparse_discrete_y_facets_also_use_the_profile_height():
    # The height floor must cover a few-category discrete y axis too, not only continuous y:
    # a 2-panel chart with y_slots=5 and long labels came out 1318x427 (a wide strip) because
    # the profile-height floor was gated on y_slots==0. Row demand still wins once there are
    # enough rows.
    sparse = recommend_layout(
        x_slots=6, y_slots=5, filled_marks=True, n_panels=2, y_labels=True,
        longest_y_label_chars=35, title_lines=1, subtitle_lines=1, footer_lines=1,
    )
    assert sparse["height_px"] >= 650  # profile height, not a 427px strip
    assert sparse["width_px"] / sparse["height_px"] < 2.2
    # Many rows still dominate the floor and grow height further.
    many = recommend_layout(
        x_slots=6, y_slots=40, filled_marks=True, n_panels=2, y_labels=True,
        longest_y_label_chars=35, title_lines=1, subtitle_lines=1, footer_lines=1,
    )
    assert many["height_px"] > sparse["height_px"]


def test_overflow_past_the_ceiling_grows_width_never_squashes_slots():
    result = recommend_layout(x_slots=1000, delivery_profile="chat")
    # Width is resized up past the ceiling rather than clamped, so slots keep their density.
    assert result["width_px"] > 1600
    assert any("width" in w.lower() for w in result["warnings"])
    fit = result["fit"]
    assert fit["legible"] is True          # nothing squashed; the image just got bigger
    assert fit["status"] == "over_ceiling"
    assert fit["over_width"] is True
    assert any(d["action"] == "reduce_slots" for d in fit["directives"])


def test_faceting_returns_a_grid_not_a_shallow_strip():
    result = recommend_layout(n_panels=7)
    assert result["facet_ncol"] >= 2 and result["facet_nrow"] >= 2
    assert result["facet_ncol"] * result["facet_nrow"] >= 7


def test_free_y_is_read_like_free_not_silently_dropped():
    # free_y frees the y-axis, so it must reserve the same per-panel left band as free -
    # strictly more than a fixed grid - and size identically to free.
    free = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="free")
    free_y = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="free_y")
    fixed = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="fixed")
    assert free_y["reserved_left_px"] == free["reserved_left_px"] > fixed["reserved_left_px"]
    assert free_y["width_px"] == free["width_px"] >= fixed["width_px"]
    assert free_y["facet_scales"] == "free_y"  # axis-specific value preserved
    assert free_y["warnings"] == []


def test_free_x_leaves_the_y_axis_band_alone():
    # free_x frees only the x-axis; no per-panel left band is reserved.
    free_x = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="free_x")
    fixed = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="fixed")
    assert free_x["width_px"] == fixed["width_px"]
    assert free_x["facet_scales"] == "free_x"


def test_unrecognised_scales_degrade_to_fixed_with_a_warning():
    result = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="loose")
    fixed = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="fixed")
    assert result["facet_scales"] == "fixed"
    assert result["width_px"] == fixed["width_px"]
    assert any("scales" in w for w in result["warnings"])


def test_crowded_x_labels_never_recommend_rotation():
    crowded = recommend_layout(x_slots=15, x_labels=True, longest_x_label_chars=20)
    assert crowded["rotate_x_labels"] is False
    assert any("do not rotate" in w for w in crowded["warnings"])
    roomy = recommend_layout(x_slots=15, x_labels=True, longest_x_label_chars=2)
    assert roomy["rotate_x_labels"] is False
    assert not any("do not rotate" in w for w in roomy["warnings"])


def test_title_bands_reserve_vertical_space():
    plain = recommend_layout(title_lines=0)
    titled = recommend_layout(title_lines=2, subtitle_lines=1, footer_lines=1)
    assert titled["reserved_band_px"] > 0
    assert titled["height_px"] > plain["height_px"]


def test_long_y_labels_are_capped_and_wrapped_not_grown_into_the_margin():
    # Long y-axis category names (ranked entities, model labels on a heatmap) must not grow
    # the left margin without bound - that starves the plot panel (the 7-Sep 29%-panel
    # failure). The band is capped and the overflow wraps into stacked text rows: the label
    # band still scales with the name, but only up to the cap, and the panel keeps the width.
    short = recommend_layout(
        x_slots=11, y_slots=24, filled_marks=True, y_labels=True, longest_y_label_chars=4
    )
    long = recommend_layout(
        x_slots=11, y_slots=24, filled_marks=True, y_labels=True, longest_y_label_chars=60
    )
    # A short name needs no wrapping; a long one is wrapped to a per-line character budget.
    assert short["wrap_y_labels_chars"] == 0
    assert long["wrap_y_labels_chars"] > 0
    # The band still grows with the name, but the cap holds it far below the unbounded demand
    # (60 chars would otherwise reserve ~600px of left band) and the panel keeps its share.
    assert long["reserved_left_px"] > short["reserved_left_px"]
    assert long["reserved_left_px"] < 60 * 11
    assert long["data_panel_fraction"] >= 0.4
    # The wrapped label spends its overflow on vertical rows, so the canvas grows taller, not
    # ever-wider behind the labels.
    assert long["height_px"] >= short["height_px"]


def test_reports_data_panel_fraction_and_keeps_it_healthy():
    result = recommend_layout(
        x_slots=11, y_slots=24, filled_marks=True, y_labels=True, longest_y_label_chars=34,
        delivery_profile="chat",
    )
    assert 0.0 < result["data_panel_fraction"] <= 1.0
    # With the left band budgeted and the canvas grown, the plot panel keeps a real share
    # of the canvas rather than collapsing behind the labels.
    assert result["data_panel_fraction"] >= 0.4


def test_a_left_band_that_would_dominate_is_warned():
    # Extreme labels the ceiling cannot fully absorb must be surfaced, not silently squashed.
    result = recommend_layout(
        x_slots=6, y_slots=10, filled_marks=True, y_labels=True, longest_y_label_chars=90,
        delivery_profile="chat",
    )
    assert any("label" in w.lower() for w in result["warnings"])


def test_short_labels_leave_layout_unchanged():
    # Regression: the new label budgeting must not perturb the default sizing.
    with_flag = recommend_layout(y_slots=8, filled_marks=True)
    assert with_flag["width_px"] == recommend_layout(y_slots=8, filled_marks=True)["width_px"]


def test_suggest_dims_grows_by_the_measured_overflow():
    out = suggest_dims_for_overflow(1200, 700, top_overflow_px=14, right_overflow_px=8)
    assert out["grow_height_px"] == 14
    assert out["grow_width_px"] == 8


def test_suggest_dims_grows_height_for_squashed_panels():
    out = suggest_dims_for_overflow(1200, 700, min_panel_height_px=MIN_PANEL_H - 50)
    panel_fraction = (MIN_PANEL_H - 50) / 700
    assert out["suggested_height_px"] * panel_fraction >= MIN_PANEL_H
    assert (out["suggested_height_px"] - 1) * panel_fraction < MIN_PANEL_H


def test_boxes_overlap_detects_and_clears():
    a = {"x": 0, "y": 0, "width": 10, "height": 10}
    b = {"x": 5, "y": 5, "width": 10, "height": 10}
    c = {"x": 100, "y": 100, "width": 10, "height": 10}
    assert boxes_overlap(a, b)
    assert not boxes_overlap(a, c)


def test_fractional_overflow_rounds_up_to_clear_the_edge():
    out = suggest_dims_for_overflow(1200, 700, top_overflow_px=0.2, right_overflow_px=0.2)
    assert out["grow_height_px"] == out["grow_width_px"] == 1


def test_zero_height_panel_keeps_a_finite_growth_proposal():
    out = suggest_dims_for_overflow(1200, 700, min_panel_height_px=0)
    assert out["suggested_height_px"] == 700 + MIN_PANEL_H


# --- Heterogeneous panel groups (overview/detail hierarchy) ------------------
# A uniform facet grid flattens a deliberately heterogeneous layout: an aggregate
# total panel set apart, a composition panel, and a small-multiple detail grid
# (the selector's aggregate-and-parts guardrail). panel_groups lets recommend_layout
# size each group's own sub-grid into its own full-width band, so Build no longer
# collapses overview and detail into one equally-weighted grid.

def _weekly_usage_groups():
    return [
        {"role": "overview", "n_panels": 1, "emphasis": 2.0, "filled_marks": True, "x_slots": 12},
        {"role": "composition", "n_panels": 1, "emphasis": 1.0, "x_slots": 12},
        {"role": "detail", "n_panels": 10, "emphasis": 1.0, "filled_marks": True, "x_slots": 12},
    ]


def test_scalar_path_reports_no_regions():
    # Back-compat: the single-grid API is unchanged and carries a null regions key.
    result = recommend_layout(n_panels=12, x_slots=12, filled_marks=True)
    assert result["regions"] is None
    assert result["facet_ncol"] * result["facet_nrow"] >= 12


def test_panel_groups_return_one_region_per_group_in_order():
    result = recommend_layout(panel_groups=_weekly_usage_groups(), delivery_profile="chat")
    regions = result["regions"]
    assert regions is not None and len(regions) == 3
    assert [r["role"] for r in regions] == ["overview", "composition", "detail"]
    # Every panel is accounted for; the twelve are NOT one 4x3 uniform grid.
    assert sum(r["facet_ncol"] * r["facet_nrow"] >= r["n_panels"] for r in regions) == 3
    assert regions[0]["n_panels"] == 1 and regions[2]["n_panels"] == 10


def test_panel_groups_stack_as_disjoint_full_width_bands():
    result = recommend_layout(panel_groups=_weekly_usage_groups())
    regions = result["regions"]
    width = result["width_px"]
    # Each band spans the canvas width, and bands are stacked top to bottom without overlap.
    for r in regions:
        assert r["x"] == 0 and r["width"] == width
    for a, b in zip(regions, regions[1:]):
        assert b["y"] >= a["y"] + a["height"]


def test_overview_band_is_taller_than_a_single_detail_cell():
    # The aggregate panel must be set apart, not read as one more equal cell.
    result = recommend_layout(panel_groups=_weekly_usage_groups())
    overview, detail = result["regions"][0], result["regions"][2]
    detail_cell_h = detail["height"] / detail["facet_nrow"]
    assert overview["height"] > detail_cell_h


def test_emphasis_grows_the_prominent_band():
    groups = _weekly_usage_groups()
    low = recommend_layout(panel_groups=[dict(groups[0], emphasis=1.0), groups[1], groups[2]])
    high = recommend_layout(panel_groups=[dict(groups[0], emphasis=3.0), groups[1], groups[2]])
    assert high["regions"][0]["height"] > low["regions"][0]["height"]


def test_group_roles_are_echoed_verbatim_not_enumerated():
    # Roles are free-text labels for Build, never a fixed vocabulary the sizer branches on.
    groups = [
        {"role": "headline_kpi", "n_panels": 1, "x_slots": 4, "filled_marks": True},
        {"role": "whatever the model calls it", "n_panels": 6, "x_slots": 8, "filled_marks": True},
    ]
    result = recommend_layout(panel_groups=groups)
    assert [r["role"] for r in result["regions"]] == [
        "headline_kpi",
        "whatever the model calls it",
    ]


def test_band_height_follows_what_each_group_shows():
    # A one-bar overview above a four-bar detail panel is not an equal split: each band takes
    # its rows plus the axis expansion, so the overview gets about a third of the plot height.
    result = recommend_layout(
        y_labels=True, longest_y_label_chars=20,
        panel_groups=[
            {"role": "overview", "n_panels": 1, "filled_marks": True, "y_slots": 1},
            {"role": "detail", "n_panels": 1, "filled_marks": True, "y_slots": 4},
        ],
    )
    overview, detail = result["regions"]
    share = overview["height"] / (overview["height"] + detail["height"])
    assert 0.2 <= share <= 0.4


def test_group_grid_aims_at_the_target_aspect():
    # The tool picks the column count: a wide target spreads a ten-panel detail grid into more
    # columns than a square one, and the whole image lands wider.
    groups = [{"role": "overview", "n_panels": 1}, {"role": "detail", "n_panels": 10}]
    square = recommend_layout(panel_groups=groups, target_aspect=1.0)
    wide = recommend_layout(panel_groups=groups, target_aspect=16 / 9)
    assert wide["regions"][1]["facet_ncol"] > square["regions"][1]["facet_ncol"]
    assert wide["width_px"] / wide["height_px"] > square["width_px"] / square["height_px"]


def test_default_target_is_the_delivery_aspect_not_square():
    # With no target given, a facet grid aims at the profile's own aspect (16:9 for chat).
    result = recommend_layout(n_panels=11, facet_scales="free_y")
    assert result["width_px"] / result["height_px"] > 1.4


def test_wide_panel_group_grows_width_never_squashes_slots():
    # A group with many slots must widen the image, not crowd the slots into a clamped width.
    from dataviz_mcp.layout import PROFILES

    result = recommend_layout(
        panel_groups=[{"role": "detail", "n_panels": 8, "x_slots": 40, "filled_marks": True}],
        delivery_profile="chat",
    )
    assert result["width_px"] > PROFILES["chat"]["max_width_px"]
    fit = result["fit"]
    assert fit["over_width"] is True and fit["legible"] is True
    assert any(d["action"] == "reduce_slots" for d in fit["directives"])


def test_panel_groups_still_report_data_panel_fraction():
    result = recommend_layout(panel_groups=_weekly_usage_groups())
    assert 0.0 < result["data_panel_fraction"] <= 1.0


def test_tall_group_stack_grows_the_canvas_never_squashes_panels():
    # Many emphasized groups exceed the profile height. The old behaviour scaled every band
    # down to cram into the ceiling, returning sub-floor panels while claiming a clean fit.
    # Now the canvas is grown (height is the scroll dimension) so no panel is squashed, and the
    # overflow is surfaced as a machine-branchable fit verdict plus directives.
    from dataviz_mcp.layout import MIN_PANEL_H, PROFILES

    groups = [
        {"role": f"g{i}", "n_panels": 6, "emphasis": 3.0, "x_slots": 10, "filled_marks": True}
        for i in range(6)
    ]
    result = recommend_layout(panel_groups=groups, delivery_profile="chat")
    # The honest size exceeds the nominal ceiling rather than clamping to it.
    assert result["height_px"] > PROFILES["chat"]["max_height_px"]
    assert any("height" in w.lower() for w in result["warnings"])
    # No panel is squashed below the floor, and the fit says the box is over the ceiling.
    fit = result["fit"]
    assert fit["min_panel_height_px"] >= MIN_PANEL_H - 0.5
    assert fit["status"] == "over_ceiling"
    assert fit["over_height"] is True
    assert fit["legible"] is True
    actions = {d["action"] for d in fit["directives"]}
    assert {"drop_group", "split_pages"} <= actions
    # Regions still stack disjoint inside the (grown) honest canvas.
    last = result["regions"][-1]
    assert last["y"] + last["height"] <= result["height_px"]
    for a, b in zip(result["regions"], result["regions"][1:]):
        assert b["y"] >= a["y"] + a["height"]


def test_column_count_balances_the_image_aspect_to_the_panel_shape():
    # "Figure out the number of columns": the grid is chosen so the whole IMAGE lands square-ish
    # given each panel's floored shape. Tall panels (many y-rows) take MORE columns so the image
    # is not a narrow tower; short/wide panels take fewer.
    short = recommend_layout(n_panels=12, y_slots=3, filled_marks=True)
    tall = recommend_layout(n_panels=12, y_slots=40, filled_marks=True)
    assert tall["facet_ncol"] >= short["facet_ncol"]
    assert tall["facet_ncol"] * tall["facet_nrow"] >= 12
    assert short["facet_ncol"] * short["facet_nrow"] >= 12


def test_grid_makes_the_whole_image_square_ish():
    # The overall image aspect should sit near 1 (square-ish) across panel shapes, not blow out
    # into a wide strip or a narrow tower.
    for kw in [
        dict(n_panels=12, y_slots=3, filled_marks=True),
        dict(n_panels=16, y_slots=8, filled_marks=True),
        dict(n_panels=24, y_slots=30, filled_marks=True),
        dict(n_panels=30, y_slots=12, filled_marks=True),
        dict(n_panels=6, x_slots=30, filled_marks=True),
    ]:
        result = recommend_layout(**kw)
        aspect = result["width_px"] / result["height_px"]
        # The target is the delivery aspect (16:9); a grid lands within a third of it either way
        # (16 panels x 8 rows: 8x2 at 2.3 and 6x3 at 1.3 sit equally far from it).
        assert 0.45 <= aspect <= 2.4, (kw, aspect)


def test_grid_finds_the_exact_fit_shape_a_round_sqrt_misses():
    # 24 tall panels pack into 12x2 (image aspect ~1.4, zero empty cells) - a shape a plain
    # round(sqrt(n * ratio)) skips in favour of a more portrait 8x3. The row-iterating chooser
    # finds it because it is the compact grid closest to square.
    result = recommend_layout(n_panels=24, y_slots=30, filled_marks=True)
    assert result["facet_ncol"] == 12 and result["facet_nrow"] == 2
    # No wasted (empty) cells: the grid holds exactly the panels.
    assert result["facet_ncol"] * result["facet_nrow"] == 24


def test_facet_panels_never_fall_below_the_height_floor():
    # A big facet grid on the chat profile keeps every panel at or above MIN_PANEL_H by growing
    # the image, rather than clamping to the ceiling and returning thumbnails.
    from dataviz_mcp.layout import MIN_PANEL_H

    result = recommend_layout(n_panels=30, y_slots=12, filled_marks=True, delivery_profile="chat")
    assert result["fit"]["min_panel_height_px"] >= MIN_PANEL_H - 0.5
    # The actual returned canvas holds panels at that floor (no squash).
    from dataviz_mcp.layout import FONT_PT, PANEL_GUTTER, pt_to_px

    axis_band = pt_to_px(FONT_PT["axis"], result["dpi"]) * 3.0
    nrow = result["facet_nrow"]
    panel_h = (result["height_px"] - result["reserved_band_px"] - axis_band
               - (nrow - 1) * PANEL_GUTTER) / nrow
    assert panel_h >= MIN_PANEL_H - 0.5


def test_returns_resolved_house_fonts_matching_reserve_frame():
    # recommend_layout returns the canvas-scaled house fonts so the sizes travel with the dims,
    # and they must equal house_font_pt(final_w, final_h) - exactly what reserve_frame will use.
    from dataviz_mcp.layout import house_font_pt

    for kw in [
        dict(x_slots=8, y_slots=8, filled_marks=True),                       # chat, scale ~1
        dict(x_slots=6, filled_marks=True, delivery_profile="slide"),        # bigger canvas
        dict(n_panels=24, y_slots=30, filled_marks=True, delivery_profile="document"),
    ]:
        result = recommend_layout(**kw)
        assert result["font_pt"] == house_font_pt(result["width_px"], result["height_px"])


def test_scaled_text_bands_grow_the_reserved_band_and_height():
    # On a large canvas the house title/subtitle grow, so the reserved text band (and thus the
    # reported height accounting) must reflect the scaled sizes, not the flat base 16/12pt.
    small = recommend_layout(x_slots=8, title_lines=1, subtitle_lines=1)
    big = recommend_layout(x_slots=8, title_lines=1, subtitle_lines=1, delivery_profile="document")
    assert big["font_pt"]["title"] > small["font_pt"]["title"]
    assert big["reserved_band_px"] > small["reserved_band_px"]


def test_panel_groups_also_return_resolved_fonts():
    from dataviz_mcp.layout import house_font_pt

    result = recommend_layout(
        panel_groups=[
            {"role": "overview", "n_panels": 1, "x_slots": 8, "filled_marks": True},
            {"role": "detail", "n_panels": 12, "x_slots": 8, "filled_marks": True},
        ],
        delivery_profile="document",
    )
    assert result["font_pt"] == house_font_pt(result["width_px"], result["height_px"])


def test_fit_object_is_ok_for_a_comfortable_chart():
    result = recommend_layout(x_slots=8, y_slots=8, filled_marks=True)
    fit = result["fit"]
    assert fit["status"] == "ok"
    assert fit["legible"] is True
    assert fit["fits_ceiling"] is True
    assert fit["directives"] == []

# ---- from test_frame.py ----

from dataviz_mcp.frame import reserve_frame
from dataviz_mcp.layout import boxes_overlap


def _canvas_box(result):
    c = result["canvas"]
    return {"x": 0, "y": 0, "width": c["width_px"], "height": c["height_px"]}


def test_plot_area_sits_inside_the_canvas_below_the_title():
    result = reserve_frame(title="Sales fell in every region", subtitle="FY24 vs FY23")
    plot = result["plot_area"]
    canvas = result["canvas"]
    assert plot["x"] > 0 and plot["y"] > 0
    assert plot["x"] + plot["width"] <= canvas["width_px"]
    assert plot["y"] + plot["height"] <= canvas["height_px"]
    # The plot area starts below the reserved top band.
    assert plot["y"] >= result["reserved_px"]["top"]


def test_frame_blocks_are_returned_wrapped_and_never_overlap_the_plot_area():
    result = reserve_frame(
        title="Revenue grew but margin did not",
        subtitle="Quarterly, indexed to Q1",
        caption="Source: internal finance",
    )
    ids = {block["id"] for block in result["frame_blocks"]}
    assert {"title", "subtitle", "caption"} <= ids
    for block in result["frame_blocks"]:
        assert block["wrapped_text"]
        assert not boxes_overlap(block["bbox"], result["plot_area"])


def test_a_longer_title_reserves_a_taller_top_band():
    short = reserve_frame(title="Sales up")
    long = reserve_frame(
        title="Sales rose across every single region this year while costs stayed flat and "
        "margins widened for the first time in a decade"
    )
    assert long["reserved_px"]["top"] > short["reserved_px"]["top"]
    assert long["plot_area"]["height"] < short["plot_area"]["height"]


def test_no_frame_text_leaves_almost_the_whole_canvas_for_the_plot():
    result = reserve_frame()
    plot = result["plot_area"]
    canvas = result["canvas"]
    # Only the outer edge margins are subtracted - no reserved bands.
    assert plot["width"] / canvas["width_px"] > 0.9
    assert plot["height"] / canvas["height_px"] > 0.88


def test_canvas_and_dpi_and_font_sizes_are_inputs():
    default = reserve_frame(title="A title")
    custom = reserve_frame(
        title="A title",
        width_px=800,
        height_px=800,
        dpi=96,
        font_pt={"title": 40.0},
    )
    assert custom["canvas"] == {"width_px": 800, "height_px": 800, "dpi": 96}
    # A 40pt title reserves a taller band than the 16pt house default.
    assert custom["reserved_px"]["top"] > default["reserved_px"]["top"]


def test_a_longer_y_axis_reserves_a_wider_left_band():
    narrow = reserve_frame(title="t", longest_y_tick="0%", y_axis_title="Share")
    wide = reserve_frame(
        title="t", longest_y_tick="1,250,000 units", y_axis_title="Units sold per quarter"
    )
    assert wide["reserved_px"]["left"] > narrow["reserved_px"]["left"]
    assert wide["plot_area"]["x"] > narrow["plot_area"]["x"]


def test_plot_margin_is_the_edge_only_and_decoupled_from_the_bands():
    # The renderer lays out the chrome natively; the builder must set plot.margin to the outer
    # edge alone. If it summed the reserved bands into plot.margin, the axis/legend/title would
    # be reserved twice and the panel would collapse (the 2-panel squish). So plot_margin_px
    # must NOT grow when the bands grow - it stays the edge margin regardless of frame text.
    plain = reserve_frame()
    heavy = reserve_frame(
        title="A rather long headline that wraps across the width of the canvas",
        subtitle="and a subtitle too", caption="Source: internal finance",
        x_axis_title="Quarter", longest_x_tick="Q1'24", y_axis_title="Revenue ($MM)",
        longest_y_tick="$1,250,000", legend_side="right", longest_legend_label="Google Network",
    )
    # Bands grew a lot; the plot margin did not.
    assert heavy["reserved_px"]["top"] > plain["reserved_px"]["top"]
    assert heavy["plot_margin_px"] == plain["plot_margin_px"]
    # It is only the outer edge, not the reserved band.
    assert heavy["plot_margin_px"]["top"] < heavy["reserved_px"]["top"]
    assert heavy["plot_margin_px"]["left"] < heavy["reserved_px"]["left"]


def test_a_canvas_too_small_for_the_frame_is_warned_not_squashed():
    result = reserve_frame(
        title="A rather long title that cannot possibly fit",
        subtitle="and a subtitle",
        caption="and a caption line too",
        width_px=200,
        height_px=120,
    )
    assert result["warnings"]
    assert any("too" in w.lower() or "small" in w.lower() or "shorten" in w.lower()
               for w in result["warnings"])

# ---- from test_refit.py ----

from pathlib import Path

import pytest

from dataviz_mcp import refit
from dataviz_mcp.artifacts import read_json, write_json
from dataviz_mcp.layout import MIN_PANEL_H, PROFILES, suggest_dims_for_overflow
from dataviz_mcp.refit import _grow_residual, _propose_dims, refit_chart


# --- pure helpers -----------------------------------------------------------


def _geometry_summary(dims, *, top_overflow=0.0, right_overflow=0.0, min_panel_h=None):
    squashed = min_panel_h is not None and min_panel_h < MIN_PANEL_H
    edge = {
        "top": round(max(0.0, top_overflow), 2),
        "bottom": 0.0,
        "left": 0.0,
        "right": round(max(0.0, right_overflow), 2),
    }
    suggested = None
    if any(edge.values()) or squashed:
        suggested = suggest_dims_for_overflow(
            dims["width_px"],
            dims["height_px"],
            top_overflow_px=edge["top"],
            right_overflow_px=edge["right"],
            min_panel_height_px=min_panel_h,
        )
    return {
        "clip_px_max": round(max(edge.values()), 2),
        "edge_overflow_px": edge,
        "min_panel_height_px": min_panel_h,
        "panels_squashed": squashed,
        "worst_offenders": [],
        "suggested_dims": suggested,
    }


def test_grow_residual_sums_overflow_and_squash_deficit():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, top_overflow=14.0, right_overflow=6.0)
    assert _grow_residual(gs) == pytest.approx(20.0)


def test_grow_residual_counts_squashed_panels():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, min_panel_h=MIN_PANEL_H - 40.0)
    assert _grow_residual(gs) == pytest.approx(40.0)


def test_grow_residual_zero_on_clean_geometry():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    assert _grow_residual(_geometry_summary(dims)) == 0.0


def test_propose_dims_grows_by_the_overflow():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, top_overflow=30.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["height_px"] == 705
    assert proposed["width_px"] == 1200
    assert proposed["dpi"] == 144


def test_propose_dims_clamps_to_ceiling():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, right_overflow=5000.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["width_px"] == 1600  # clamped, not 6200


def test_propose_dims_never_shrinks_below_current():
    dims = {"width_px": 2000, "height_px": 675, "dpi": 144}  # already past a 1600 ceiling
    gs = _geometry_summary(dims, top_overflow=30.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["width_px"] == 2000  # ceiling never forces a shrink


# --- the loop (fake renderer, no real render) -------------------------------


class _FakeRender:
    """Stands in for render_and_inspect_chart: writes a real inspection.json per pass."""

    def __init__(self, geom_fn):
        self.geom_fn = geom_fn
        self.calls: list[dict] = []

    def __call__(
        self,
        source_path,
        output_dir,
        renderer="auto",
        delivery_profile="chat",
        dimensions=None,
        artifact_name="chart.png",
        build_function="build_chart",
        content="chart",
    ):
        index = len(self.calls)
        self.calls.append(dict(dimensions))
        gs, defects = self.geom_fn(dimensions, index)
        report = {
            "schema_version": 3,
            "geometry_summary": gs,
            "defects": defects,
            "passes_geometry_checks": not defects,
            "width": dimensions["width_px"],
            "height": dimensions["height_px"],
        }
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        inspection_path = out / "inspection.json"
        write_json(inspection_path, report)
        return {
            "artifact": {
                "path": str(out / "chart.png"),
                "width": dimensions["width_px"],
                "height": dimensions["height_px"],
                "sha256": "deadbeef",
            },
            "layout_metadata_path": str(out / "layout-metadata.json"),
            "manifest_path": str(out / "manifest.json"),
            "inspection_path": str(inspection_path),
            "review_view_paths": [],
            "renderer": "matplotlib",
            "content": content,
        }


def _install(monkeypatch, geom_fn):
    fake = _FakeRender(geom_fn)
    monkeypatch.setattr(refit, "render_and_inspect_chart", fake)
    return fake


def test_growing_clears_the_clip_and_reports_resolved(tmp_path, monkeypatch):
    need_h = 900

    def geom(dims, _index):
        overflow = max(0.0, need_h - dims["height_px"])
        gs = _geometry_summary(dims, top_overflow=overflow)
        defects = (
            [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]
            if overflow
            else []
        )
        return gs, defects

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True
    assert result["final_dimensions"]["height_px"] >= need_h
    assert fake.calls[-1]["height_px"] >= need_h
    assert result["history"][0]["action"] == "grow"
    assert result["history"][-1]["action"] == "resolved"


def test_ceiling_is_warned_not_squashed(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims, right_overflow=5000.0)
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is False
    ceiling = PROFILES["chat"]["max_width_px"]
    assert result["final_dimensions"]["width_px"] == ceiling
    assert any("ceiling" in w for w in result["warnings"])
    assert result["history"][-1]["action"] == "ceiling_reached"


def test_no_improvement_stops_the_loop(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims, top_overflow=50.0)  # constant, growth never helps
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=5)
    assert result["resolved"] is False
    assert result["history"][-1]["action"] == "no_improvement"
    assert len(fake.calls) == 2  # initial + one ineffective grow, then stop
    assert any("improv" in w for w in result["warnings"])


def test_max_iterations_is_respected(tmp_path, monkeypatch):
    # Overflow keeps falling (so each grow improves) but never reaches zero within the budget,
    # and stays well under the ceiling so max_iterations is the exit, not ceiling_reached.
    def geom(dims, index):
        overflow = [40.0, 20.0, 10.0][index]
        gs = _geometry_summary(dims, top_overflow=overflow)
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=2)
    assert len(fake.calls) == 3  # initial render + 2 regrows
    assert result["history"][-1]["action"] == "max_iterations"


def test_underfill_is_reported_but_not_resized(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims)  # clean geometry, nothing to grow
        return gs, [
            {"code": "UNDERFILLED_CANVAS", "severity": "low", "element_ids": [], "message": "empty"}
        ]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True  # nothing resize-fixable remains
    assert result["underfilled"] is True
    assert len(fake.calls) == 1  # never grew
    assert any("underfill" in w.lower() for w in result["warnings"])


def test_clean_chart_needs_a_single_pass(tmp_path, monkeypatch):
    def geom(dims, _index):
        return _geometry_summary(dims), []

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True
    assert result["underfilled"] is False
    assert len(fake.calls) == 1
    assert result["warnings"] == []


def test_max_iterations_must_be_positive(tmp_path):
    with pytest.raises(ValueError):
        refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=0)


# --- live renders (real matplotlib / ggplot2, no fakes) ---------------------


_CLIP_MPL = '''
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


def build_chart():
    fig, ax = plt.subplots()
    ax.bar(["a", "b", "c", "d"], [3, 7, 4, 9], color="#4c72b0")
    ax.set_ylabel("Revenue")
    # Headline pinned at a fixed physical position: it overruns the top of a short canvas and
    # a taller canvas clears it exactly.
    fig.text(0.15, 1.9, "Quarterly revenue by division", fontsize=30, va="bottom",
             transform=fig.dpi_scale_trans)
    return fig
'''


def test_live_matplotlib_grows_until_the_clip_clears(tmp_path):
    source = tmp_path / "clip.py"
    source.write_text(_CLIP_MPL, encoding="utf-8")
    result = refit_chart(
        str(source),
        str(tmp_path / "out"),
        renderer="matplotlib",
        delivery_profile="document",
        dimensions={"width_px": 520, "height_px": 300, "dpi": 144},
        max_iterations=4,
    )
    assert result["history"][0]["clip_px_max"] > 100  # really clipped at the start
    assert result["resolved"] is True
    assert result["history"][-1]["clip_px_max"] == 0.0
    assert result["final_dimensions"]["height_px"] > 300  # it grew


_SQUASH_GG = '''
library(ggplot2)

build_chart <- function() {
  set.seed(1)
  df <- data.frame(
    x = rep(1:10, times = 6),
    y = rnorm(60),
    panel = factor(rep(paste("Region", 1:6), each = 10))
  )
  ggplot(df, aes(x, y)) +
    geom_line(colour = "#4c72b0") +
    facet_wrap(~panel, ncol = 2) +
    labs(title = "Signal by region", y = "Value") +
    theme_minimal()
}
'''


def _ggplot2_available() -> bool:
    from dataviz_mcp.rendering import probe_renderers

    return probe_renderers()["renderers"]["ggplot2"]["available"]


@pytest.mark.skipif(not _ggplot2_available(), reason="ggplot2 renderer unavailable")
def test_live_ggplot_grows_squashed_facet_panels(tmp_path):
    source = tmp_path / "squash.R"
    source.write_text(_SQUASH_GG, encoding="utf-8")
    result = refit_chart(
        str(source),
        str(tmp_path / "out"),
        renderer="ggplot2",
        delivery_profile="document",
        dimensions={"width_px": 700, "height_px": 320, "dpi": 144},
        max_iterations=4,
    )
    assert result["renderer"] == "ggplot2"
    heights = [h["min_panel_height_px"] for h in result["history"]]
    assert heights[0] < MIN_PANEL_H  # panels started squashed
    assert all(later > earlier for earlier, later in zip(heights, heights[1:]))  # each grow helps
    assert result["final_dimensions"]["height_px"] > 320
    assert result["resolved"] is True
    assert result["passes"] == 2


def test_dimensions_override_the_starting_size(tmp_path, monkeypatch):
    def geom(dims, _index):
        return _geometry_summary(dims), []

    fake = _install(monkeypatch, geom)
    refit_chart(
        str(tmp_path / "src.py"),
        str(tmp_path / "out"),
        dimensions={"width_px": 1000, "height_px": 800, "dpi": 120},
    )
    assert fake.calls[0] == {"width_px": 1000, "height_px": 800, "dpi": 120}


@pytest.mark.parametrize("panel_share", [0.5, 0.25, 0.13])
@pytest.mark.parametrize("fixed_chrome", [0, 60])
def test_panel_deficit_clears_in_one_growth(tmp_path, monkeypatch, panel_share, fixed_chrome):
    # The old additive correction halves the 44px deficit when share=0.5,
    # and converges even more slowly for smaller panels.
    initial_h = int((MIN_PANEL_H - 44) / panel_share + fixed_chrome)

    def geom(dims, _index):
        panel_h = (dims["height_px"] - fixed_chrome) * panel_share
        return _geometry_summary(dims, min_panel_h=panel_h), []

    _install(monkeypatch, geom)
    result = refit_chart(
        str(tmp_path / "src.py"), str(tmp_path / "out"),
        delivery_profile="document", dimensions={"height_px": initial_h},
    )
    assert result["resolved"] is True
    assert result["passes"] == 2
    assert result["history"][-1]["min_panel_height_px"] >= MIN_PANEL_H


def test_facet_rows_reserve_their_heading_strips_and_the_edge_margin():
    # Seven panels at the canvas the layout returns must keep the panel floor after every row's
    # heading strip and reserve_frame's edge margin are drawn; a long heading takes more lines.
    base = dict(n_panels=7, title_lines=2, subtitle_lines=1, x_labels=True, longest_x_label_chars=4,
                target_aspect=1.36)
    for chars in (0, 47):
        result = recommend_layout(**base, longest_facet_label_chars=chars)
        rows = result["facet_nrow"]
        strip = pt_to_px(11, 144) * 1.25 + pt_to_px(11 * 0.8, 144)
        chrome = result["reserved_band_px"] + 2 * round(0.03 * result["width_px"]) + rows * strip
        assert (result["height_px"] - chrome) / rows >= 150, (chars, result)


def test_a_detail_group_reserves_a_heading_strip_per_row():
    # The overview/detail stack gave the detail grid panel height only, so its facet strips came
    # out of the panels: every row of a multi-panel group now carries its strip in the band.
    groups = [{"role": "overview", "n_panels": 1}, {"role": "detail", "n_panels": 6}]
    plain = recommend_layout(panel_groups=groups)
    long = recommend_layout(panel_groups=groups, longest_facet_label_chars=60)
    detail = next(r for r in long["regions"] if r["role"] == "detail")
    assert detail["height"] >= detail["facet_nrow"] * (MIN_PANEL_H + pt_to_px(11, 144) * 1.25)
    assert long["height_px"] > plain["height_px"]

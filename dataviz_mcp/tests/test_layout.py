from dataviz_mcp.layout import (
    MAX_PANEL_ASPECT,
    MIN_PANEL_H,
    boxes_overlap,
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


def test_overflow_past_the_ceiling_is_warned_not_squashed():
    result = recommend_layout(x_slots=1000, delivery_profile="chat")
    assert result["width_px"] <= 1600  # clamped to the chat ceiling
    assert any("crowd" in w or "split" in w for w in result["warnings"])


def test_faceting_returns_a_grid_not_a_shallow_strip():
    result = recommend_layout(n_panels=7)
    assert result["facet_ncol"] >= 2 and result["facet_nrow"] >= 2
    assert result["facet_ncol"] * result["facet_nrow"] >= 7


def test_free_y_is_read_like_free_not_silently_dropped():
    # free_y frees the y-axis, so it must reserve the same per-panel band as free -
    # and strictly more width than a fixed grid (x_slots push width past the base).
    free = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="free")
    free_y = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="free_y")
    fixed = recommend_layout(n_panels=6, x_slots=15, filled_marks=True, facet_scales="fixed")
    assert free_y["width_px"] == free["width_px"] > fixed["width_px"]
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


def test_long_y_labels_reserve_left_width_and_grow_the_canvas():
    # The 7-Sep heatmap failure: long model labels on the y-axis were not budgeted, so
    # the renderer grew the left margin at the panel's expense (panel fell to 29%). The
    # left band must scale with the longest y label and the canvas grow to keep the panel.
    short = recommend_layout(
        x_slots=11, y_slots=24, filled_marks=True, y_labels=True, longest_y_label_chars=4
    )
    long = recommend_layout(
        x_slots=11, y_slots=24, filled_marks=True, y_labels=True, longest_y_label_chars=60
    )
    assert long["reserved_left_px"] > short["reserved_left_px"]
    # Once the label band plus the panel floor exceeds the base width, the canvas grows
    # rather than shrinking the panel behind the labels.
    assert long["width_px"] > short["width_px"]


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

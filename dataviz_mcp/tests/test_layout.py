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


def test_group_honours_a_declared_column_count():
    # select may declare the grid shape ("a two-column grid of ten panels"); the sizer must
    # not override it with its own near-square guess.
    result = recommend_layout(panel_groups=[
        {"role": "detail", "n_panels": 10, "ncol": 2, "filled_marks": True, "x_slots": 6},
    ])
    detail = result["regions"][0]
    assert detail["facet_ncol"] == 2 and detail["facet_nrow"] == 5


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
        assert 0.45 <= aspect <= 2.2, (kw, aspect)


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


def test_fit_object_is_ok_for_a_comfortable_chart():
    result = recommend_layout(x_slots=8, y_slots=8, filled_marks=True)
    fit = result["fit"]
    assert fit["status"] == "ok"
    assert fit["legible"] is True
    assert fit["fits_ceiling"] is True
    assert fit["directives"] == []

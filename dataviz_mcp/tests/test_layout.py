from dataviz_mcp.layout import (
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


def test_suggest_dims_grows_by_the_measured_overflow():
    out = suggest_dims_for_overflow(1200, 700, top_overflow_px=14, right_overflow_px=8)
    assert out["grow_height_px"] == 14
    assert out["grow_width_px"] == 8


def test_suggest_dims_grows_height_for_squashed_panels():
    out = suggest_dims_for_overflow(1200, 700, min_panel_height_px=MIN_PANEL_H - 50)
    assert out["grow_height_px"] == 50


def test_boxes_overlap_detects_and_clears():
    a = {"x": 0, "y": 0, "width": 10, "height": 10}
    b = {"x": 5, "y": 5, "width": 10, "height": 10}
    c = {"x": 100, "y": 100, "width": 10, "height": 10}
    assert boxes_overlap(a, b)
    assert not boxes_overlap(a, c)

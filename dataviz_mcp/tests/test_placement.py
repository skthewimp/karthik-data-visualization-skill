from __future__ import annotations

# ---- from test_text_fit.py ----

from dataviz_mcp.layout import boxes_overlap
from dataviz_mcp.text_fit import (
    _leader_endpoints,
    _leader_line,
    _search_clear,
    _segments_cross,
    _uncross_leaders,
    recommend_text_placement as _recommend_text_placement,
)


def test_search_clear_returns_the_nearest_spot_not_a_line_height_jump():
    # A blocker overlaps the box by a few pixels; a small nudge clears it. The search must land
    # close to the anchor, not fling the box a whole line-height (step) away in the first free
    # compass direction.
    step = 16.0
    bbox = {"x": 400.0, "y": 300.0, "width": 40.0, "height": 14.0}
    blocker = {"x": 400.0, "y": 290.0, "width": 40.0, "height": 18.0}  # overlaps y 300..308
    found = _search_clear(bbox, [blocker], 800.0, 600.0, 10.0, step=step)
    assert found is not None
    cx, cy = found
    moved = {"x": cx, "y": cy, "width": bbox["width"], "height": bbox["height"]}
    assert not boxes_overlap(moved, blocker)
    distance = ((cx - bbox["x"]) ** 2 + (cy - bbox["y"]) ** 2) ** 0.5
    assert distance < step  # sub-line-height: the whole point of the nearest search


def recommend_text_placement(*args, **kwargs):
    """Keep unrelated fixtures explicit enough for the label-budget API."""
    blocks = kwargs.get("blocks") or (args[3] if len(args) > 3 else [])
    for block in blocks:
        if block.get("role") in {"label", "data_label", "axis_label"}:
            block.setdefault("max_width_px", 180)
            block.setdefault("max_lines", 3)
    return _recommend_text_placement(*args, **kwargs)


def _leaders_cross(a, b):
    return _segments_cross(
        *_leader_endpoints(a["leader_line"]), *_leader_endpoints(b["leader_line"])
    )


def _movable_with_leader(block_id, box, mark):
    return {
        "id": block_id,
        "role": "annotation",
        "bbox": dict(box),
        "leader_line": _leader_line(box, mark),
        "suggested_anchor": {"x": box["x"], "y": box["y"]},
        "warnings": [],
    }


def _by_id(result, block_id):
    return next(p for p in result["placements"] if p["id"] == block_id)


def test_long_title_wraps_within_the_canvas():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "t", "role": "title", "text": " ".join(["word"] * 40)}],
    )
    title = _by_id(result, "t")
    assert "\n" in title["wrapped_text"]  # wrapped to several lines
    assert title["bbox"]["x"] + title["bbox"]["width"] <= 1200
    assert not title["warnings"]


def test_annotation_is_moved_off_a_data_mark():
    obstacle = {"x": 390, "y": 290, "width": 120, "height": 60}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "a", "role": "annotation", "text": "peak here", "anchor": {"x": 400, "y": 300}}],
        obstacles=[obstacle],
    )
    placement = _by_id(result, "a")
    assert placement["suggested_anchor"] is not None
    assert not boxes_overlap(placement["bbox"], obstacle)


def test_on_mark_data_label_stays_on_its_mark():
    # A stacked-bar segment value sits centred inside its segment. Its own bar is a data mark,
    # but the label belongs there - it must be wrapped in place, never pushed off, never given a
    # leader line, even though an obstacle covers its anchor.
    segment = {"x": 380, "y": 280, "width": 140, "height": 100}
    anchor = {"x": 400, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "v", "role": "data_label", "text": "44%", "anchor": anchor}],
        obstacles=[segment],
    )
    placement = _by_id(result, "v")
    assert placement["suggested_anchor"] is None
    assert placement["leader_line"] is None
    assert placement["bbox"]["x"] == anchor["x"]
    assert placement["bbox"]["y"] == anchor["y"]
    assert not placement["warnings"]


def test_two_on_mark_values_at_adjacent_ends_are_nudged_apart_on_their_marks():
    # Two line-end values land on nearly the same spot. Both are pinned data labels, so neither
    # is shoved a callout's distance - but the second is nudged clear within a line-height and
    # stays adjacent to its mark, so they no longer overlap.
    first = {"x": 900, "y": 300}
    second = {"x": 906, "y": 306}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "a", "role": "data_label", "text": "44%", "anchor": first},
            {"id": "b", "role": "data_label", "text": "41%", "anchor": second},
        ],
    )
    a, b = _by_id(result, "a"), _by_id(result, "b")
    assert a["bbox"]["x"] == first["x"] and a["bbox"]["y"] == first["y"]  # first claims its spot
    assert b["suggested_anchor"] is not None
    assert b["leader_line"] is None  # kept on its mark, no connector
    assert any("nudged clear" in w for w in b["warnings"])
    assert not boxes_overlap(a["bbox"], b["bbox"])
    # The nudge is bounded: it stayed within about a line-height of its mark.
    assert abs(b["bbox"]["x"] - second["x"]) + abs(b["bbox"]["y"] - second["y"]) < 60


def test_two_on_mark_values_that_cannot_separate_report_the_residual():
    # Two wide, tall on-mark boxes stacked on the same anchor cannot separate within a
    # line-height in any direction, so the second reports the residual for the build to resolve
    # (move the movable label, stack, or cut) rather than silently overlapping.
    anchor = {"x": 600, "y": 350}
    tall = {"role": "data_label", "text": "12345 67890 13579 24680", "max_width_px": 110, "max_lines": 3}
    result = _recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "a", "anchor": anchor, **tall},
            {"id": "b", "anchor": dict(anchor), **tall},
        ],
    )
    b = _by_id(result, "b")
    assert any("cannot be separated on the mark" in w for w in b["warnings"])


def test_two_annotations_are_separated_from_each_other():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "a1", "role": "annotation", "text": "first note", "anchor": {"x": 400, "y": 300}},
            {"id": "a2", "role": "annotation", "text": "second note", "anchor": {"x": 405, "y": 305}},
        ],
        obstacles=[],
    )
    a1 = _by_id(result, "a1")
    a2 = _by_id(result, "a2")
    assert not boxes_overlap(a1["bbox"], a2["bbox"])


def test_annotation_near_the_edge_is_nudged_inward():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "a", "role": "annotation", "text": "edge case label", "anchor": {"x": 1180, "y": 680}}],
        obstacles=[],
    )
    placement = _by_id(result, "a")
    assert placement["bbox"]["x"] + placement["bbox"]["width"] <= 1200
    assert placement["bbox"]["y"] + placement["bbox"]["height"] <= 700


def test_label_is_shrunk_when_no_clear_spot_exists_at_full_size():
    # Obstacles leave only a small top-right window: a 14pt box cannot fit it, an 8pt one can.
    walls = [
        {"x": 0, "y": 0, "width": 240, "height": 200},
        {"x": 240, "y": 40, "width": 60, "height": 160},
    ]
    result = recommend_text_placement(
        300, 200, 144,
        blocks=[{"id": "a", "role": "label", "text": "peak", "anchor": {"x": 250, "y": 15}, "font_pt": 14}],
        obstacles=walls,
        min_font_pt=8.0,
    )
    placement = _by_id(result, "a")
    assert placement["suggested_font_pt"] is not None
    assert 8.0 <= placement["suggested_font_pt"] < 14.0


def test_shrink_never_goes_below_the_legibility_floor():
    walls = [{"x": 0, "y": 0, "width": 300, "height": 200}]  # entire canvas blocked
    result = recommend_text_placement(
        300, 200, 144,
        blocks=[{"id": "a", "role": "label", "text": "unavoidable overlap here", "anchor": {"x": 20, "y": 20}, "font_pt": 14}],
        obstacles=walls,
        min_font_pt=8.0,
    )
    placement = _by_id(result, "a")
    # Nothing fits even at the floor: it falls through to a tightened wrap, never a sub-floor font.
    if placement["suggested_font_pt"] is not None:
        assert placement["suggested_font_pt"] >= 8.0


def test_unresolvable_landscape_recommends_portrait_flip():
    walls = [{"x": 0, "y": 0, "width": 400, "height": 200}]  # whole landscape canvas blocked
    result = recommend_text_placement(
        400, 200, 144,
        blocks=[{"id": "a", "role": "label", "text": "does not fit anywhere at all", "anchor": {"x": 20, "y": 20}}],
        obstacles=walls,
    )
    assert result["suggested_orientation"] == "portrait"
    assert result["suggested_canvas"] == {"width_px": 200, "height_px": 400, "dpi": 144}


def test_clean_placement_recommends_no_flip():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "a", "role": "annotation", "text": "peak", "anchor": {"x": 400, "y": 300}}],
        obstacles=[],
    )
    assert result["suggested_orientation"] is None
    assert result["suggested_canvas"] is None


def test_moved_label_gets_a_leader_line_back_to_its_point():
    anchor = {"x": 400, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "a", "role": "label", "text": "36%", "anchor": anchor}],
        obstacles=[{"x": 390, "y": 290, "width": 120, "height": 60}],
    )
    placement = _by_id(result, "a")
    assert placement["suggested_anchor"] is not None  # it moved
    leader = placement["leader_line"]
    assert leader is not None
    assert leader["to"] == {"x": anchor["x"], "y": anchor["y"]}  # points back to the mark
    assert any("leader line" in w for w in placement["warnings"])


def test_label_parks_beside_its_mark_without_a_leader():
    # The anchor is the mark. With nothing in the way the label parks just to its right and
    # carries no leader, no suggested_anchor and no warning - it is where it belongs.
    mark = {"x": 400, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "s", "role": "label", "text": "Cereals", "anchor": mark}],
        obstacles=[],
    )
    placement = _by_id(result, "s")
    assert placement["leader_line"] is None
    assert placement["suggested_anchor"] is None
    assert not placement["warnings"]
    assert placement["bbox"]["x"] > mark["x"]  # parked to the right of the mark, not on it


def test_series_label_wraps_to_a_short_measure_not_a_canvas_fraction():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{
            "id": "s",
            "role": "label",
            "text": "Milk and dairy excluding butter fresh milk equivalent",
            "anchor": {"x": 700, "y": 300},
            "max_width_px": 280,
            "max_lines": 3,
        }],
    )
    placement = _by_id(result, "s")
    lines = placement["wrapped_text"].split("\n")
    assert 1 < len(lines) <= 3
    assert placement["curtailed"] is False
    assert placement["over_line_budget"] is False


def test_overlong_series_label_is_curtailed_and_preserved_for_a_key():
    full = " ".join(["internationally"] * 12)
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{
            "id": "s", "role": "label", "text": full,
            "anchor": {"x": 700, "y": 300}, "max_width_px": 150,
            "max_lines": 3, "allow_curtail": True,
        }],
    )
    placement = _by_id(result, "s")
    assert len(placement["wrapped_text"].split("\n")) == 3
    assert placement["wrapped_text"].endswith("…")
    assert placement["curtailed"] is True
    assert placement["full_text"] == full
    assert any("key or footnote" in warning for warning in placement["warnings"])


def test_long_data_label_uses_the_same_readable_line_budget():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{
            "id": "d",
            "role": "data_label",
            "text": "Provisional estimate adjusted for seasonal variation",
            "anchor": {"x": 400, "y": 300},
            "max_width_px": 230,
            "max_lines": 3,
        }],
    )
    placement = _by_id(result, "d")
    assert 1 < len(placement["wrapped_text"].split("\n")) <= 3


def test_axis_label_uses_the_builder_supplied_measure_and_line_budget():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{
            "id": "tick", "role": "axis_label", "text": "Very long category name",
            "anchor": {"x": 400, "y": 650}, "max_width_px": 90, "max_lines": 2,
        }],
    )
    placement = _by_id(result, "tick")
    assert len(placement["wrapped_text"].split("\n")) > 2
    assert placement["over_line_budget"] is True
    assert placement["curtailed"] is False


def test_label_budget_is_required_instead_of_invented_by_the_tool():
    import pytest

    with pytest.raises(ValueError, match="must declare max_width_px and max_lines"):
        _recommend_text_placement(
            1200, 700, 144,
            blocks=[{"id": "s", "role": "label", "text": "Cereals", "anchor": {"x": 1, "y": 1}}],
        )


def test_blocked_side_parks_on_another_side_still_without_a_leader():
    # The preferred (right) side is blocked but the space above is open: the label parks above,
    # adjacent to its mark, so it still needs no leader - only a note that it changed sides.
    mark = {"x": 400, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "s", "role": "label", "text": "Meat", "anchor": mark}],
        obstacles=[{"x": 405, "y": 285, "width": 200, "height": 40}],
    )
    placement = _by_id(result, "s")
    assert placement["leader_line"] is None  # still adjacent, no dash needed
    assert placement["suggested_anchor"] is not None  # but it moved off the preferred side


def test_category_label_may_sit_beside_any_point_along_its_series():
    # The endpoint neighbourhood is blocked, but an earlier point on the same line is clear.
    # The label attaches there - adjacency, not the endpoint, is what names the series - with
    # no leader. Candidate marks are passed in `anchors`; the first is the primary.
    endpoint = {"x": 900, "y": 300}
    midpoint = {"x": 500, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{
            "id": "line", "role": "label", "text": "Roots and tubers",
            "anchor": endpoint, "anchors": [endpoint, midpoint],
        }],
        obstacles=[{"x": 880, "y": 260, "width": 260, "height": 80}],  # smothers the endpoint
    )
    placement = _by_id(result, "line")
    assert placement["leader_line"] is None
    assert placement["bbox"]["x"] < 880  # parked near the mid-line point, clear of the endpoint


def test_placement_priority_data_label_then_label_then_annotation():
    # All three want the same spot. The data label is pinned there; the category label and the
    # annotation each yield in turn, so none overlaps another - and the pinned label never moves.
    anchor = {"x": 400, "y": 300}
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "ann", "role": "annotation", "text": "note", "anchor": anchor},
            {"id": "lab", "role": "label", "text": "series", "anchor": anchor},
            {"id": "dl", "role": "data_label", "text": "42%", "anchor": anchor},
        ],
    )
    dl = _by_id(result, "dl")
    lab = _by_id(result, "lab")
    ann = _by_id(result, "ann")
    assert dl["bbox"]["x"] == anchor["x"] and dl["bbox"]["y"] == anchor["y"]  # pinned, unmoved
    assert not boxes_overlap(dl["bbox"], lab["bbox"])
    assert not boxes_overlap(dl["bbox"], ann["bbox"])
    assert not boxes_overlap(lab["bbox"], ann["bbox"])


def test_unmoved_label_has_no_leader_line():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "a", "role": "label", "text": "36%", "anchor": {"x": 400, "y": 300}}],
        obstacles=[],
    )
    assert _by_id(result, "a")["leader_line"] is None


def test_fixed_roles_are_wrapped_but_never_given_a_moved_anchor():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "cap", "role": "caption", "text": " ".join(["source"] * 30), "anchor": {"x": 40, "y": 660}}],
    )
    caption = _by_id(result, "cap")
    assert caption["suggested_anchor"] is None
    assert caption["wrap_width_chars"] > 0


def test_crossing_leaders_are_swapped_back_to_their_own_marks():
    # Two labels landed on the wrong sides: the one naming the LOW mark sits at the top, the one
    # naming the HIGH mark sits at the bottom, so their leaders cross (the bottom-right-panel bug).
    # A collision-free swap sends each back toward its own mark and uncrosses them.
    a = _movable_with_leader("q4", {"x": 120, "y": 80, "width": 200, "height": 50}, (600, 400))
    b = _movable_with_leader("q3", {"x": 120, "y": 380, "width": 160, "height": 50}, (600, 80))
    assert _leaders_cross(a, b)  # crossed before
    _uncross_leaders([a, b], [])
    assert not _leaders_cross(a, b)  # uncrossed after
    assert a["bbox"]["y"] == 380 and b["bbox"]["y"] == 80  # they traded positions
    assert a["suggested_anchor"] == {"x": 120, "y": 380}
    assert any("uncross" in w for w in a["warnings"])


def test_crossing_leaders_are_left_alone_when_the_swap_would_collide():
    # Same crossing pair, but an obstacle sits exactly where each box would land after the swap.
    # The swap is refused rather than trading one defect (a cross) for a worse one (an overlap).
    a = _movable_with_leader("q4", {"x": 120, "y": 80, "width": 200, "height": 50}, (600, 400))
    b = _movable_with_leader("q3", {"x": 120, "y": 380, "width": 160, "height": 50}, (600, 80))
    blockers = [
        {"x": 120, "y": 380, "width": 200, "height": 50},
        {"x": 120, "y": 80, "width": 160, "height": 50},
    ]
    _uncross_leaders([a, b], blockers)
    assert a["bbox"]["y"] == 80 and b["bbox"]["y"] == 380  # unchanged
    assert not any("uncross" in w for w in a["warnings"])


def test_non_crossing_leaders_are_left_in_place():
    # Each label already sits on its own mark's side - nothing to swap.
    a = _movable_with_leader("a", {"x": 120, "y": 80, "width": 160, "height": 50}, (600, 80))
    b = _movable_with_leader("b", {"x": 120, "y": 380, "width": 160, "height": 50}, (600, 400))
    assert not _leaders_cross(a, b)
    _uncross_leaders([a, b], [])
    assert a["bbox"]["x"] == 120 and a["bbox"]["y"] == 80
    assert not any("uncross" in w for w in a["warnings"])


def test_annotation_restating_a_nearby_data_label_is_flagged_for_removal():
    # A "Peak: 42% in 2000" callout beside a data label already showing 42% only restates it -
    # recommend dropping it. The year 2000 is a coordinate, not a second data value.
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "dl", "role": "data_label", "text": "42.0%", "anchor": {"x": 500, "y": 300}},
            {"id": "ann", "role": "annotation", "text": "Peak: 42% in 2000", "anchor": {"x": 540, "y": 330}},
        ],
    )
    redundant = {item["id"] for item in result["redundant_annotations"]}
    assert "ann" in redundant
    assert any("restates the data label" in w for w in _by_id(result, "ann")["warnings"])


def test_comparison_annotation_naming_two_values_is_not_flagged():
    # "fell from 51% to 26%" names two values and states a change - it adds what the labels do
    # not, so even with matching data labels nearby it is never flagged.
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "dl1", "role": "data_label", "text": "51%", "anchor": {"x": 300, "y": 300}},
            {"id": "dl2", "role": "data_label", "text": "26%", "anchor": {"x": 340, "y": 320}},
            {"id": "ann", "role": "annotation", "text": "fell from 51% to 26%", "anchor": {"x": 360, "y": 340}},
        ],
    )
    assert result["redundant_annotations"] == []


def test_delta_annotation_whose_number_is_on_no_label_is_not_flagged():
    # "Up 9 points" restates a change; 9 is on no data label (endpoints are 14 and 23), so the
    # mechanical check leaves it - the value-add judgement stays with the skill.
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "dl1", "role": "data_label", "text": "14%", "anchor": {"x": 300, "y": 300}},
            {"id": "dl2", "role": "data_label", "text": "23%", "anchor": {"x": 340, "y": 320}},
            {"id": "ann", "role": "annotation", "text": "Up 9 points", "anchor": {"x": 360, "y": 340}},
        ],
    )
    assert result["redundant_annotations"] == []


def test_bar_value_labels_inside_with_per_bar_contrast():
    # A saturated focal bar and pale grey context bars, all long enough to hold their value: every
    # label sits inside, and the colour flips per bar so neither vanishes into its fill.
    from dataviz_mcp.text_fit import place_bar_value_labels

    result = place_bar_value_labels(
        [
            {"id": "focal", "value_text": "610", "fill": "#B23A2E", "bar_length_px": 600, "bar_thickness_px": 160},
            {"id": "grey", "value_text": "540", "fill": "#C9C5BE", "bar_length_px": 540, "bar_thickness_px": 160},
        ],
        dpi=144,
        font_pt=21,
    )
    by_id = {p["id"]: p for p in result["placements"]}
    assert by_id["focal"]["placement"] == "inside"
    assert by_id["grey"]["placement"] == "inside"
    # White on the red focal fill, dark on the pale grey - never one colour for both.
    assert by_id["focal"]["colour"] == "#ffffff"
    assert by_id["grey"]["colour"] == "#1a1a1a"
    assert by_id["grey"]["contrast_ratio"] >= 4.5


def test_bar_value_label_too_long_for_short_bar_goes_outside():
    from dataviz_mcp.text_fit import place_bar_value_labels

    result = place_bar_value_labels(
        [{"id": "short", "value_text": "260", "fill": "#C9C5BE", "bar_length_px": 30, "bar_thickness_px": 160}],
        dpi=144,
        font_pt=21,
    )
    placement = result["placements"][0]
    assert placement["placement"] == "outside"
    # Outside sits on the canvas, so contrast is judged against the background, not the fill.
    assert placement["surface"] == "#ffffff"


def test_real_font_widths_distinguish_narrow_from_wide_glyphs():
    # The flat 0.5-em estimate boxed "iii..." and "WWW..." identically; real advances must not.
    # Narrow glyphs get a narrower box, wide glyphs a wider one, at the same char count.
    common = dict(width_px=1200, height_px=675, dpi=144, obstacles=[])
    narrow = recommend_text_placement(
        blocks=[{"id": "n", "text": "iiiiiiiiiiiiii", "role": "title",
                 "anchor": {"x": 60, "y": 40}}],
        **common,
    )["placements"][0]["bbox"]["width"]
    wide = recommend_text_placement(
        blocks=[{"id": "w", "text": "WWWWWWWWWWWWWW", "role": "title",
                 "anchor": {"x": 60, "y": 40}}],
        **common,
    )["placements"][0]["bbox"]["width"]
    assert wide > narrow * 2  # real faces: W is ~3.5x the advance of i


def test_bold_weight_reserves_more_width_than_normal():
    common = dict(width_px=1200, height_px=675, dpi=144, obstacles=[])
    text = "Manufacturing output"
    normal = recommend_text_placement(
        blocks=[{"id": "t", "text": text, "role": "title", "anchor": {"x": 60, "y": 40}}],
        **common,
    )["placements"][0]["bbox"]["width"]
    bold = recommend_text_placement(
        blocks=[{"id": "t", "text": text, "role": "title", "anchor": {"x": 60, "y": 40},
                 "font_weight": "bold"}],
        **common,
    )["placements"][0]["bbox"]["width"]
    assert bold > normal


def test_font_family_threads_through_place_on_marks():
    from dataviz_mcp.text_fit import place_on_marks

    transform = [[1.0, 0.0, 0.0], [0.0, -1.0, 675.0], [0.0, 0.0, 1.0]]
    out = place_on_marks(
        width_px=1200, height_px=675, dpi=144, transform=transform,
        labels=[{"id": "a", "text": "Manufacturing", "role": "annotation",
                 "data_x": 300, "data_y": 300, "font_family": "Times New Roman"}],
        marks=[],
    )
    # It placed without error and produced a real box for the label in the requested face.
    box = out["placements"][0]["bbox"]
    assert box["width"] > 0 and box["height"] > 0


def test_repel_settles_each_label_nearest_its_own_mark():
    # Two series labels whose marks sit close together are both smothered by one big obstacle, so
    # both defer to the ggrepel solve. Because each is pulled only toward its OWN mark but pushed
    # off everything, each must end up nearer its own mark than the other's - reading as the right
    # series with no hand-tuned ambiguity term - and the two boxes must not overlap.
    a_mark = {"x": 500, "y": 300}
    b_mark = {"x": 500, "y": 340}
    smother = {"x": 360, "y": 240, "width": 300, "height": 160}  # covers both marks + all sides
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[
            {"id": "A", "role": "label", "text": "Alpha", "anchor": a_mark},
            {"id": "B", "role": "label", "text": "Bravo", "anchor": b_mark},
        ],
        obstacles=[smother],
    )
    a, b = _by_id(result, "A"), _by_id(result, "B")

    def near(box, mark):
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        return ((cx - mark["x"]) ** 2 + (cy - mark["y"]) ** 2) ** 0.5

    assert near(a["bbox"], a_mark) < near(a["bbox"], b_mark)   # A reads as its own series
    assert near(b["bbox"], b_mark) < near(b["bbox"], a_mark)   # B reads as its own series
    assert not boxes_overlap(a["bbox"], b["bbox"])
    assert not boxes_overlap(a["bbox"], smother)
    assert not boxes_overlap(b["bbox"], smother)
    assert a["leader_line"] is not None and b["leader_line"] is not None


def test_repel_is_deterministic():
    # No random jitter: the same input places to the same pixels every run.
    blocks = [
        {"id": "A", "role": "label", "text": "Alpha", "anchor": {"x": 500, "y": 300}},
        {"id": "B", "role": "label", "text": "Bravo", "anchor": {"x": 500, "y": 340}},
    ]
    obstacles = [{"x": 360, "y": 240, "width": 300, "height": 160}]
    first = recommend_text_placement(1200, 700, 144, blocks=[dict(b) for b in blocks], obstacles=obstacles)
    second = recommend_text_placement(1200, 700, 144, blocks=[dict(b) for b in blocks], obstacles=obstacles)
    assert _by_id(first, "A")["bbox"] == _by_id(second, "A")["bbox"]
    assert _by_id(first, "B")["bbox"] == _by_id(second, "B")["bbox"]

# ---- from test_place_on_marks.py ----

import pytest

from dataviz_mcp.text_fit import place_on_marks


# A simple top-left affine: pixel_x = 2*data_x + 100, pixel_y = 600 - 5*data_y.
# Stored the way layout metadata stores it: [[a, c, e], [d, e2, f2], [0, 0, 1]].
TRANSFORM = [[2.0, 0.0, 100.0], [0.0, -5.0, 600.0], [0.0, 0.0, 1.0]]


def test_a_label_is_projected_from_data_coords_and_parked_beside_its_mark():
    result = place_on_marks(
        width_px=800,
        height_px=600,
        dpi=144,
        transform=TRANSFORM,
        labels=[
            {"id": "peak", "text": "Peak", "role": "label",
             "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1},
        ],
        marks=[],
    )
    placement = result["placements"][0]
    # data (50, 40) -> pixel (200, 400); the label parks just to the right of it.
    assert placement["bbox"]["x"] >= 200
    assert abs(placement["bbox"]["y"] + placement["bbox"]["height"] / 2 - 400) < 40
    assert result["projected_anchors"]["peak"] == {"x": 200.0, "y": 400.0}


def test_a_mark_in_the_way_pushes_the_label_off_its_preferred_side():
    # A mark box straddling the point's right side blocks the default "right" placement.
    blocking = {"x": 200, "y": 360, "width": 120, "height": 80}
    result = place_on_marks(
        width_px=800,
        height_px=600,
        dpi=144,
        transform=TRANSFORM,
        labels=[
            {"id": "peak", "text": "Peak", "role": "label",
             "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1},
        ],
        marks=[{"id": "m1", "role": "mark", "bbox": blocking}],
    )
    placement = result["placements"][0]
    assert placement["suggested_anchor"] is not None
    assert not _overlap(placement["bbox"], blocking)


def test_fixed_frame_blocks_pass_through_and_block_movable_labels():
    title = {"id": "title", "role": "title", "text": "A title",
             "anchor": {"x": 40, "y": 20}}
    result = place_on_marks(
        width_px=800,
        height_px=600,
        dpi=144,
        transform=TRANSFORM,
        labels=[{"id": "l", "text": "x", "role": "label",
                 "data_x": 0, "data_y": 0, "max_width_px": 80, "max_lines": 1}],
        marks=[],
        fixed_blocks=[title],
    )
    ids = {p["id"] for p in result["placements"]}
    assert "title" in ids and "l" in ids


def test_an_on_mark_data_label_stays_at_its_projected_anchor():
    result = place_on_marks(
        width_px=800,
        height_px=600,
        dpi=144,
        transform=TRANSFORM,
        labels=[
            {"id": "v", "text": "42%", "role": "data_label",
             "data_x": 50, "data_y": 40, "max_width_px": 80, "max_lines": 1},
        ],
        # even with a mark right on top, an on-mark data label is not shoved away
        marks=[{"id": "m1", "role": "mark", "bbox": {"x": 195, "y": 395, "width": 20, "height": 20}}],
    )
    placement = result["placements"][0]
    assert placement["bbox"]["x"] == 200.0
    assert placement["bbox"]["y"] == 400.0
    assert placement["leader_line"] is None


def test_place_on_marks_refuses_without_a_transform():
    # A ggplot render with no emitted transform (a non-Cartesian coord_trans/polar/sf, or an
    # unreproducible date/logit/custom scale) must make this fail loudly so the driver falls
    # back to ggrepel, not project through a missing map.
    with pytest.raises(ValueError, match="data->pixel transform") as excinfo:
        place_on_marks(
            800, 600, 144, [],
            labels=[{"id": "l", "text": "x", "role": "label",
                     "data_x": 0, "data_y": 0, "max_width_px": 80, "max_lines": 1}],
            marks=[],
        )
    message = str(excinfo.value)
    # The guidance must name the truly-unsupported cases and must NOT claim the supported
    # ones (coord_flip, log/sqrt/reverse scales, facets) emit no transform.
    assert "coord_trans" in message and "polar" in message
    assert "included" in message  # coord_flip / scales / facets named as SUPPORTED
    assert "coord_flip/polar" not in message  # the old lie grouped coord_flip with unsupported


def _overlap(a, b, tol=0.5):
    ow = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    oh = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    return ow > tol and oh > tol


# A mark box surrounding the point on every side, so the label has no adjacent spot and must
# travel - the case that grows a leader line.
_SURROUNDING_MARK = {"id": "b", "role": "mark", "bbox": {"x": 120, "y": 300, "width": 220, "height": 220}}


def test_a_displaced_label_returns_native_data_coordinates_for_its_leader():
    result = place_on_marks(
        width_px=800,
        height_px=600,
        dpi=144,
        transform=TRANSFORM,
        labels=[
            {"id": "peak", "text": "Peak", "role": "label",
             "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1},
        ],
        marks=[_SURROUNDING_MARK],
    )
    placement = result["placements"][0]
    # It had to travel, so it carries a pixel leader AND its native-coordinate twin.
    assert placement["leader_line"] is not None
    assert placement["leader_line_data"] is not None
    # The leader's mark end, inverted, lands exactly back on the mark's data coordinates
    # (px 200,400 -> data 50,40 under this affine) - never an improvised segment endpoint.
    assert placement["leader_line_data"]["to"] == {"x": 50.0, "y": 40.0}
    assert placement["anchor_data"] == {"x": 50, "y": 40}
    # placed_data is the inverse of the box origin, so the builder draws the label in data space.
    assert placement["placed_data"] is not None
    bx, by = placement["bbox"]["x"], placement["bbox"]["y"]
    assert placement["placed_data"] == {"x": round((bx - 100) / 2, 6), "y": round((600 - by) / 5, 6)}


def test_an_adjacent_label_has_no_leader_data_but_still_reports_placed_data():
    result = place_on_marks(
        width_px=800, height_px=600, dpi=144, transform=TRANSFORM,
        labels=[{"id": "peak", "text": "Peak", "role": "label",
                 "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1}],
        marks=[],
    )
    placement = result["placements"][0]
    assert placement["leader_line"] is None
    assert "leader_line_data" not in placement
    assert placement["placed_data"] is not None
    assert placement["anchor_data"] == {"x": 50, "y": 40}


def test_a_singular_transform_yields_no_fabricated_data_coordinates():
    # A degenerate affine (the y row collapses x and y) cannot be inverted; the tool must omit
    # data coordinates rather than invent them.
    singular = [[2.0, 0.0, 100.0], [2.0, 0.0, 100.0], [0.0, 0.0, 1.0]]
    result = place_on_marks(
        width_px=800, height_px=600, dpi=144, transform=singular,
        labels=[{"id": "l", "text": "Peak", "role": "label",
                 "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1}],
        marks=[_SURROUNDING_MARK],
    )
    placement = result["placements"][0]
    assert "placed_data" not in placement
    assert "leader_line_data" not in placement


def test_plot_area_pulls_a_straddling_label_wholly_inside_and_reports_the_move():
    # The label parks to the right of its mark and straddles a plot boundary whose right edge is
    # at pixel 230. Canvas growth cannot fix that; place_on_marks moves it inside and says by how much.
    plot_area = {"x": 50, "y": 50, "width": 180, "height": 540}  # right edge 230, bottom 590
    result = place_on_marks(
        width_px=800, height_px=600, dpi=144, transform=TRANSFORM,
        labels=[{"id": "peak", "text": "Peak", "role": "label",
                 "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1}],
        marks=[_SURROUNDING_MARK],
        plot_area=plot_area,
    )
    placement = result["placements"][0]
    assert placement["plot_boundary_correction"] is not None
    assert placement["plot_boundary_correction"]["dx"] < 0  # shifted left, back inside
    right_edge = placement["bbox"]["x"] + placement["bbox"]["width"]
    assert right_edge <= plot_area["x"] + plot_area["width"] + 0.5


def test_without_plot_area_no_boundary_correction_is_applied():
    result = place_on_marks(
        width_px=800, height_px=600, dpi=144, transform=TRANSFORM,
        labels=[{"id": "peak", "text": "Peak", "role": "label",
                 "data_x": 50, "data_y": 40, "max_width_px": 120, "max_lines": 1}],
        marks=[_SURROUNDING_MARK],
    )
    assert result["placements"][0]["plot_boundary_correction"] is None


def test_interval_end_values_go_outward_along_the_interval():
    # A horizontal dumbbell: one path from the minimum to the maximum, a dot at each end. The
    # minimum's value sits left of its dot and the maximum's right of its dot, both centred on the
    # row - not with their box corners on the points (below and to the right of both).
    lo, hi = TRANSFORM[0][0] * 20 + 100, TRANSFORM[0][0] * 80 + 100  # 140, 260
    row = 600 - 5 * 40  # 400
    marks = [
        {"id": "bar", "role": "series", "points": [[lo, row], [hi, row]]},
        {"id": "dot-lo", "role": "mark", "bbox": {"x": lo - 6, "y": row - 6, "width": 12, "height": 12}},
        {"id": "dot-hi", "role": "mark", "bbox": {"x": hi - 6, "y": row - 6, "width": 12, "height": 12}},
    ]
    result = place_on_marks(
        width_px=800, height_px=600, dpi=144, transform=TRANSFORM,
        labels=[
            {"id": "lo", "text": "20%", "role": "data_label", "data_x": 20, "data_y": 40,
             "max_width_px": 80, "max_lines": 1},
            {"id": "hi", "text": "80%", "role": "data_label", "data_x": 80, "data_y": 40,
             "max_width_px": 80, "max_lines": 1},
        ],
        marks=marks,
    )
    lo_box, hi_box = _by_id(result, "lo")["bbox"], _by_id(result, "hi")["bbox"]
    assert lo_box["x"] + lo_box["width"] <= lo - 6   # wholly left of the minimum's dot
    assert hi_box["x"] >= hi + 6                     # wholly right of the maximum's dot
    for box in (lo_box, hi_box):
        assert abs(box["y"] + box["height"] / 2 - row) < 1  # centred on the row


def test_ggplot_segments_export_as_paths_so_interval_ends_are_known(tmp_path):
    # geom_segment draws from (x0, y0) to (x1, y1) with no x/y; the render metadata must still
    # carry each segment as a two-point path, or the interval rule never sees a dumbbell.
    from dataviz_mcp.rendering import probe_renderers, render_and_inspect_chart

    if not probe_renderers()["renderers"]["ggplot2"]["available"]:
        pytest.skip("ggplot2 unavailable")
    source = tmp_path / "chart.R"
    source.write_text(
        "library(ggplot2)\n"
        "build_chart <- function() {\n"
        "  d <- data.frame(y = c('a', 'b'), lo = c(10, 20), hi = c(60, 80))\n"
        "  ggplot(d) + geom_segment(aes(x = lo, xend = hi, y = y, yend = y))\n"
        "}\n",
        encoding="utf-8",
    )
    bundle = render_and_inspect_chart(
        str(source), str(tmp_path / "out"), dimensions={"width_px": 800, "height_px": 500, "dpi": 144}
    )
    import json
    from pathlib import Path

    meta = json.loads(Path(bundle["layout_metadata_path"]).read_text(encoding="utf-8"))
    paths = [s for s in meta["series"] if len(s["points"]) == 2]
    assert len(paths) == 2
    for path in paths:
        (x0, y0), (x1, y1) = path["points"]
        assert abs(y0 - y1) < 0.5 and x1 > x0  # horizontal, drawn low to high


def test_bar_value_label_extent_follows_the_bar_orientation():
    # A wide number fits a short fat column (its line height runs up the column, its width across
    # the bar) but not the same length of horizontal bar, where its width runs along the value.
    from dataviz_mcp.text_fit import place_bar_value_labels

    bar = {"id": "b", "value_text": "77,264", "fill": "#106010", "bar_length_px": 50, "bar_thickness_px": 120}
    column = place_bar_value_labels([bar], dpi=144, font_pt=12, orientation="vertical")["placements"][0]
    row = place_bar_value_labels([bar], dpi=144, font_pt=12, orientation="horizontal")["placements"][0]
    assert column["placement"] == "inside" and row["placement"] == "outside"
    # The width is the face's measured advance, so a bold face needs more room than the regular.
    regular = place_bar_value_labels([bar], dpi=144, font_pt=12, orientation="horizontal")["placements"][0]
    bold = place_bar_value_labels([bar], dpi=144, font_pt=12, orientation="horizontal",
                                  font_weight="bold")["placements"][0]
    assert bold["label_px"] > regular["label_px"]

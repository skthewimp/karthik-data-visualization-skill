from dataviz_mcp.layout import boxes_overlap
from dataviz_mcp.text_fit import (
    _leader_endpoints,
    _leader_line,
    _segments_cross,
    _uncross_leaders,
    recommend_text_placement,
)


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
        }],
    )
    placement = _by_id(result, "s")
    lines = placement["wrapped_text"].split("\n")
    assert 1 < len(lines) <= 3
    assert max(map(len, lines)) <= 24
    assert placement["curtailed"] is False


def test_overlong_series_label_is_curtailed_and_preserved_for_a_key():
    full = " ".join(["internationally"] * 12)
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "s", "role": "label", "text": full, "anchor": {"x": 700, "y": 300}}],
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
        }],
        max_label_chars_per_line=20,
    )
    placement = _by_id(result, "d")
    assert 1 < len(placement["wrapped_text"].split("\n")) <= 3
    assert max(map(len, placement["wrapped_text"].split("\n"))) <= 20


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

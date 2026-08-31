from dataviz_mcp.layout import boxes_overlap
from dataviz_mcp.text_fit import recommend_text_placement


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

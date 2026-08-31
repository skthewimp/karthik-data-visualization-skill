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


def test_fixed_roles_are_wrapped_but_never_given_a_moved_anchor():
    result = recommend_text_placement(
        1200, 700, 144,
        blocks=[{"id": "cap", "role": "caption", "text": " ".join(["source"] * 30), "anchor": {"x": 40, "y": 660}}],
    )
    caption = _by_id(result, "cap")
    assert caption["suggested_anchor"] is None
    assert caption["wrap_width_chars"] > 0

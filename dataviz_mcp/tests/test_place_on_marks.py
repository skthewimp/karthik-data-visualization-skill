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


def _overlap(a, b, tol=0.5):
    ow = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    oh = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    return ow > tol and oh > tol

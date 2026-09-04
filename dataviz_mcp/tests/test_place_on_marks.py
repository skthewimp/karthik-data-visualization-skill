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

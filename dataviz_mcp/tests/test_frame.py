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

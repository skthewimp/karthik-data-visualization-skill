from copy import deepcopy
import json
from pathlib import Path

import pytest

from dataviz_mcp.artifacts import sha256_file
from dataviz_mcp.frame import reserve_frame
from dataviz_mcp.inspection import _planned_geometry_defects, inspect_rendered_chart
from dataviz_mcp.rendering import probe_renderers, render_and_inspect_chart
from dataviz_mcp.text_fit import place_on_marks


def test_reserved_frame_checks_real_panels_and_stale_canvas():
    frame = reserve_frame(width_px=800, height_px=600, dpi=144)
    metadata = {
        "canvas": {"width": 800, "height": 600}, "artifact": {"dpi": [144, 144]},
        "plot_areas": [{"id": "panel", "bbox": deepcopy(frame["plot_area"])}],
        "inspection_contract": {"frame": frame},
    }
    assert not _planned_geometry_defects(metadata)
    metadata["plot_areas"][0]["bbox"]["y"] = 0
    assert _planned_geometry_defects(metadata)[0]["code"] == "FRAME_PLAN_MISMATCH"
    metadata["plot_areas"][0]["bbox"] = deepcopy(frame["plot_area"])
    metadata["canvas"]["width"] = 900
    assert _planned_geometry_defects(metadata)[0]["code"] == "FRAME_PLAN_MISMATCH"


@pytest.mark.parametrize("role", ["label", "data_label", "annotation"])
def test_attachment_uses_explicit_target_not_text_role(role):
    args = dict(
        width_px=800, height_px=600, dpi=144,
        transform=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        marks=[{"id": "lower", "bbox": {"x": 100, "y": 200, "width": 100, "height": 100}},
               {"id": "upper", "bbox": {"x": 100, "y": 100, "width": 100, "height": 100}}],
        labels=[{"id": "value", "text": "20", "role": role,
                 "data_x": 150, "data_y": 250, "mark_id": "lower",
                 "max_width_px": 80, "max_lines": 1}],
    )
    assert place_on_marks(**args)["unverified_attachments"] == []
    # The independently computed stack anchor landed neatly inside the wrong segment.
    args["labels"][0]["data_y"] = 150
    with pytest.raises(ValueError, match="anchor misses target mark"):
        place_on_marks(**args)
    args["labels"][0]["mark_id"] = "missing"
    with pytest.raises(ValueError, match="must identify one mark"):
        place_on_marks(**args)
    del args["labels"][0]["mark_id"]
    assert place_on_marks(**args)["unverified_attachments"] == ["value"]


def test_series_anchor_must_touch_path_not_just_bounding_box():
    with pytest.raises(ValueError, match="anchor misses target mark"):
        place_on_marks(800, 600, 144, [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                       [{"id": "value", "text": "20", "role": "label", "mark_id": "line",
                         "data_x": 100, "data_y": 200}],
                       [{"id": "line", "points": [[100, 100], [200, 200]],
                         "bbox": {"x": 100, "y": 100, "width": 100, "height": 100}}])


def test_repeated_text_cannot_satisfy_two_planned_labels():
    block = {"id": "first", "wrapped_text": "20", "bbox": {"x": 10, "y": 10, "width": 20, "height": 10}}
    metadata = {"inspection_contract": {"placements": [block, {**block, "id": "second"}]},
                "elements": [{"id": "arbitrary", "text": "20", "role": "data_label", "bbox": block["bbox"]}]}
    assert len(_planned_geometry_defects(metadata)) == 1


@pytest.mark.skipif(not probe_renderers()["renderers"]["ggplot2"]["available"], reason="ggplot2+ragg not installed")
def test_ggplot_preserved_and_swapped_text_checked_without_classification(tmp_path):
    source = Path(__file__).parent / "fixtures" / "ggplot_value_labels_fixture.R"
    dims = {"width_px": 800, "height_px": 500, "dpi": 144}
    ruler = render_and_inspect_chart(str(source), str(tmp_path / "ruler"), dimensions=dims)
    layout = json.loads(Path(ruler["layout_metadata_path"]).read_text())
    # The adapter treats all in-panel text alike; the plan does not try to reverse that.
    text = [e for e in layout["elements"] if e["axes_id"] and e["text"] in {"10", "40", "25", "60"}]
    assert len(text) == 4
    assert {e["role"] for e in text} == {"data_label"}
    contract = {"placements": [{"id": f"planned-{i}", "wrapped_text": e["text"], "bbox": e["bbox"]}
                               for i, e in enumerate(text)]}
    for swapped in (False, True):
        build = tmp_path / f"build-{swapped}.R"
        code = source.read_text()
        if swapped:
            code = code.replace("aes(label = value)", "aes(label = rev(value))")
        build.write_text(code)
        bundle = render_and_inspect_chart(str(build), str(tmp_path / str(swapped)),
                                          dimensions=dims, inspection_contract=contract)
        report = json.loads(Path(bundle["inspection_path"]).read_text())
        codes = {d["code"] for d in report["defects"]}
        assert ("TEXT_PLAN_MISMATCH" in codes) is swapped
        assert "TEXT_MARK_COLLISION" not in codes
        if swapped:
            assert report["passes_geometry_checks"] is False
        manifest = json.loads(Path(bundle["manifest_path"]).read_text())
        assert manifest["layout_metadata"]["sha256"] == sha256_file(Path(bundle["layout_metadata_path"]))
        # Standalone inspection must retain the same enforcement, not just the render wrapper.
        again = inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"])
        assert ("TEXT_PLAN_MISMATCH" in {d["code"] for d in again["defects"]}) is swapped


def test_builder_applies_forward_frame_and_placement_results(tmp_path):
    frame = reserve_frame(title="Planned frame", width_px=800, height_px=600, dpi=144)
    placement = place_on_marks(
        800, 600, 144, [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [{"id": "value", "text": "20", "role": "data_label", "font_pt": 12,
          "data_x": 300, "data_y": 200, "max_width_px": 80, "max_lines": 1}],
    )["placements"][0]
    assert placement["placed_data"] == {"x": 300, "y": 200}
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"frame": frame, "placements": [placement]}))
    source = tmp_path / "build.py"
    source.write_text(f'''
import json
import matplotlib.pyplot as plt

def build_chart():
    plan = json.load(open({str(plan)!r}))
    frame = plan["frame"]
    fig = plt.figure(figsize=(800/144, 600/144), dpi=144)
    p = frame["plot_area"]
    ax = fig.add_axes([p["x"]/800, 1-(p["y"]+p["height"])/600,
                       p["width"]/800, p["height"]/600])
    ax.set_axis_off()
    for block in frame["frame_blocks"]:
        fig.text(block["bbox"]["x"]/800, 1-block["bbox"]["y"]/600,
                 block["wrapped_text"], fontsize=block["font_pt"], ha="left", va="top")
    for block in plan["placements"]:
        fig.text(block["bbox"]["x"]/800, 1-block["bbox"]["y"]/600,
                 block["wrapped_text"], fontsize=12, ha="left", va="top")
    return fig
''')
    contract = {"frame": frame, "placements": [placement]}
    bundle = render_and_inspect_chart(str(source), str(tmp_path / "out"),
                                      dimensions=frame["canvas"], inspection_contract=contract)
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert not ({"FRAME_PLAN_MISMATCH", "TEXT_PLAN_MISMATCH"} & {d["code"] for d in report["defects"]})


def test_planned_leader_must_reach_the_returned_endpoints():
    block = {"id": "callout", "wrapped_text": "Name", "bbox": {"x": 10, "y": 10, "width": 20, "height": 10},
             "leader_line": {"from": {"x": 30, "y": 20}, "to": {"x": 80, "y": 80}}}
    metadata = {"inspection_contract": {"placements": [block]},
                "elements": [{"id": "gg-1", "text": "Name", "bbox": block["bbox"]}],
                "series": [{"segments": [[[30, 20], [80, 80]]]}]}
    assert not _planned_geometry_defects(metadata)
    metadata["series"][0]["segments"][0][-1] = [120, 120]
    assert _planned_geometry_defects(metadata)[0]["code"] == "TEXT_PLAN_MISMATCH"


def test_refit_preserves_contract_and_requires_remeasurement_before_growth(tmp_path):
    from dataviz_mcp.refit import refit_chart

    frame = reserve_frame(width_px=800, height_px=450, dpi=144)
    source = Path(__file__).parent / "fixtures" / "chart_fixtures.py"
    result = refit_chart(str(source), str(tmp_path / "refit"), renderer="matplotlib",
                         dimensions=frame["canvas"], build_function="annotation_outside_canvas",
                         inspection_contract={"frame": frame})
    assert result["history"][-1]["action"] == "remeasure_required"
    assert len(result["history"]) == 1
    layout = json.loads(Path(result["layout_metadata_path"]).read_text())
    assert layout["inspection_contract"]["frame"] == frame

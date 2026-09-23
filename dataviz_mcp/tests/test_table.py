from __future__ import annotations

# ---- from test_table_layout.py ----

import pytest

from dataviz_mcp.table_layout import recommend_table_layout


def test_wrapping_pagination_preserves_content_and_type():
    cols = [{"header": "Name", "identifier": True, "max_width_px": 120,
             "cells": ["A much longer name", "B", "C", "D"]}]
    cols += [{"header": "Metric " + str(i), "cells": ["100", "20", "3", "0"]}
             for i in range(4)]
    out = recommend_table_layout(cols, delivery={"max_width_px": 300, "max_height_px": 180})
    assert out["status"] == "split"
    assert out["body_pt"] == 11
    assert out["row_heights_px"][0] > out["row_heights_px"][1]
    seen = set()
    for page in out["pages"]:
        assert 0 in page["columns"]
        assert page["width_px"] <= 300 and page["height_px"] <= 180
        for c in page["columns"]:
            for r in range(*page["rows"]):
                seen.add((c, r))
    assert seen == {(c, r) for c in range(5) for r in range(4)}
    assert out["cells"][0][0].replace("\n", " ") == cols[0]["cells"][0]


def test_display_floor_and_unbreakable_content():
    out = recommend_table_layout([{"header": "Value", "cells": ["W" * 100]}],
        delivery={"display_width_px": 400, "minimum_text_px": 16, "max_width_px": 1600})
    assert out["status"] == "cannot_fit"
    assert out["body_pt"] >= 11
    assert out["cells"][0][0] == "W" * 100


def test_treatment_requires_shared_scale_semantics_not_column_counts():
    cols = [{"header": "Value", "cells": ["-3", "10"]}]
    with pytest.raises(ValueError, match="commensurability"):
        recommend_table_layout(cols, treatment={"kind": "shading", "scope": "table"})
    plan = {"kind": "bar", "columns": [0], "scope": "column", "domain": [-3, 10], "baseline": 0}
    out = recommend_table_layout(cols * 4, treatment=plan)
    assert out["treatment"] == [plan]


@pytest.mark.parametrize("long_header", [True, False])
def test_construction_wraps_long_content_without_a_manual_width_cap(long_header):
    phrase = "Average revenue per active customer"
    cols = [
        {"header": "Name", "cells": ["A", "B", "C"] * 4},
        {"header": phrase if long_header else "Note",
         "cells": ["12", "35", "40"] * 4 if long_header else [phrase, "OK", "OK"] * 4},
    ]
    compact = recommend_table_layout(cols)
    # An unbreakable equivalent forces the former natural-width behavior.
    unbreakable = [dict(c) for c in cols]
    if long_header:
        unbreakable[1]["header"] = phrase.replace(" ", "_")
    else:
        unbreakable[1]["cells"] = [v.replace(" ", "_") for v in cols[1]["cells"]]
    wide = recommend_table_layout(unbreakable)
    assert compact["col_widths_px"][1] < wide["col_widths_px"][1]
    assert compact["body_pt"] == wide["body_pt"]
    assert compact["header_pt"] == wide["header_pt"]
    wrapped = compact["headers"][1] if long_header else compact["cells"][1][0]
    assert "\n" in wrapped and wrapped.replace("\n", " ") == phrase
    if long_header:
        assert compact["row_heights_px"] == wide["row_heights_px"]


def test_header_budget_requires_complete_text_and_respects_column_ceiling():
    with pytest.raises(ValueError, match="full header text"):
        recommend_table_layout([{"header_chars": 40, "max_cell_chars": 4}])
    col = {"header": "Average revenue per active customer", "cells": ["12", "35"],
           "max_header_lines": 2}
    plan = recommend_table_layout([col])
    assert plan["status"] == "fits"
    assert plan["headers"][0].count("\n") + 1 <= 2
    assert plan["headers"][0].replace("\n", " ") == col["header"]
    impossible = recommend_table_layout([{**col, "max_width_px": 40}])
    assert impossible["status"] == "cannot_fit"
    assert impossible["headers"][0].replace("\n", " ") == col["header"]
    assert impossible["header_pt"] == plan["header_pt"]


def test_frame_bands_measure_each_role_at_its_own_size():
    out = recommend_table_layout(
        [{"header": "Region", "cells": ["North", "South"]},
         {"header": "Revenue", "cells": ["12.5", "8.3"]}],
        title="A deliberately long claim-style title that must not clip at the edge",
        subtitle="a smaller subtitle line",
        notes="source: internal",
        delivery={"max_width_px": 1200, "max_height_px": 800},
    )
    bands = {b["role"]: b for b in out["frame_bands"]}
    assert set(bands) == {"title", "subtitle", "notes"}
    # Title is larger than a header and reserved bold; notes no larger than a header.
    assert bands["title"]["font_pt"] > out["header_pt"]
    assert bands["title"]["bold"] is True
    assert bands["notes"]["font_pt"] <= out["header_pt"]
    # A larger role gets a taller band (per-role line height, not the header's).
    assert bands["title"]["height_px"] > bands["notes"]["height_px"]
    assert out["reserved_band_px"] > 0


def test_title_pt_override_shrinks_its_reserved_band():
    kw = dict(delivery={"max_width_px": 1200, "max_height_px": 800})
    big = recommend_table_layout([{"header": "H", "cells": ["1", "2"]}],
                                 title="Long title text here", **kw)
    small = recommend_table_layout([{"header": "H", "cells": ["1", "2"]}],
                                   title="Long title text here",
                                   typography={"title_pt": 8}, **kw)
    tb = next(b for b in big["frame_bands"] if b["role"] == "title")
    sb = next(b for b in small["frame_bands"] if b["role"] == "title")
    assert tb["font_pt"] > sb["font_pt"]
    assert tb["height_px"] > sb["height_px"]   # bigger font -> taller band
    assert tb["width_px"] >= sb["width_px"]    # bigger font -> at least as wide

# ---- from test_table_builder.py ----

import json
from pathlib import Path

import pytest

from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import probe_renderers, render_and_inspect_chart
from dataviz_mcp.table_builder import write_table_build_source
from dataviz_mcp.table_layout import recommend_table_layout


def _codes(report: dict) -> set:
    return {d["code"] for d in report["defects"]}


@pytest.mark.skipif(
    not probe_renderers()["table_rendering"]["r_available"],
    reason="R table constructor dependencies unavailable",
)
def test_constructor_renders_recognized_unclipped_table(tmp_path: Path) -> None:
    plan = recommend_table_layout(
        [{"header": "Model", "identifier": True, "cells": ["Fable 5.1", "Opus 5", "GPT-5.6"]},
         {"header": "Combined I/O cost\nUSD per 1M tokens", "cells": ["$60.0", "$30.0", "$24.0"]},
         {"header": "Terminal-Bench 2.1", "cells": ["91.4%", "89.1%", "88.8%"]}],
        title="Muse Spark beats every rival at up to 200x lower cost",
        subtitle="Combined per-token cost vs coding-benchmark accuracy",
        notes="Private evaluation; source fidelity only.",
        delivery={"max_width_px": 1400, "max_height_px": 900},
    )
    assert plan["status"] == "fits"
    build = write_table_build_source(plan, tmp_path / "build.R")
    bundle = render_and_inspect_chart(build, str(tmp_path / "out"),
                                      content="table", build_function="build_table")
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text(encoding="utf-8"))
    # Still a recognised gtable, so the geometry checker keeps working.
    assert layout["coverage"]["table_cell_bounds"] is True
    texts = " ".join(str(e.get("text", "")) for e in layout["elements"])
    for expected in ("Muse Spark", "Combined I/O cost", "Fable 5.1", "$60.0", "Private evaluation"):
        assert expected in texts
    report = inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"])
    # The whole point: measured geometry applied verbatim, nothing clips or overflows.
    assert "OUT_OF_BOUNDS" not in _codes(report)
    assert "CELL_OVERFLOW" not in _codes(report)
    assert "BLANK_RENDER" not in _codes(report)
    assert report["occupied_utilization_ratio"] > 0.2


@pytest.mark.skipif(
    not probe_renderers()["table_rendering"]["r_available"],
    reason="R table constructor dependencies unavailable",
)
@pytest.mark.parametrize("dpi", [72, 144, 216])
def test_constructor_preserves_pixel_padding(tmp_path: Path, dpi: int) -> None:
    plan = recommend_table_layout(
        [{"header": "Group", "cells": ["Alpha", "Beta"]},
         {"header": "Value", "cells": ["10", "20"]}],
        title="Measured padding",
        subtitle="Same inset at every resolution",
        notes="Source: test data",
        typography={"padding_x_px": 18, "padding_y_px": 7},
        delivery={"max_width_px": 1400, "max_height_px": 900, "dpi": dpi},
    )
    assert plan["status"] == "fits"
    build = write_table_build_source(plan, tmp_path / "build.R")
    bundle = render_and_inspect_chart(
        build, str(tmp_path / "out"), content="table", build_function="build_table",
        dimensions={"dpi": dpi},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text(encoding="utf-8"))
    # Check actual rendered text against its containing band, not the R source.
    frame_text = {band["text"] for band in plan["frame_bands"]}
    frame_elements = [e for e in layout["elements"] if e.get("text") in frame_text]
    assert len(frame_elements) == len(frame_text)
    for element in frame_elements:
        assert element["bbox"]["x"] - element["cell_bbox"]["x"] == pytest.approx(
            plan["padding_x_px"], abs=0.1
        )
    report = inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"])
    assert not ({"OUT_OF_BOUNDS", "CELL_OVERFLOW", "BLANK_RENDER"} & _codes(report))

# ---- from test_no_r.py ----

"""Portable installs use Python; a working R backend remains the automatic default."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dataviz_mcp import rendering
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.server import create_server
from dataviz_mcp.table_builder import render_table_from_plan
from dataviz_mcp.table_layout import recommend_table_layout


def _no_r(monkeypatch):
    monkeypatch.setattr(rendering.shutil, "which", lambda _: None)


def _plan(**delivery):
    return recommend_table_layout(
        [{"header": "Group", "identifier": True, "cells": ["Alpha", "Beta", "Gamma", "Delta"]},
         {"header": "Long heading\nwith units", "cells": ["10", "20", "30", "40"]}],
        title="Measured table", subtitle="One plan for either renderer", notes="Source: test data",
        typography={"padding_x_px": 18, "padding_y_px": 7},
        delivery={"max_width_px": 1000, "max_height_px": 400, **delivery},
    )


@pytest.mark.parametrize("dpi", [72, 144, 216])
def test_no_r_table_fallback_preserves_geometry_and_inspection(tmp_path, monkeypatch, dpi):
    _no_r(monkeypatch)
    plan = _plan(dpi=dpi)
    assert plan["measurement_backend"] == "matplotlib/Agg"
    assert plan["status"] in {"fits", "split"}
    for page in range(1, len(plan["pages"]) + 1):
        bundle = render_table_from_plan(plan, str(tmp_path / str(page)), page=page)
        assert bundle["renderer"] == "matplotlib"
        assert "Rscript" in bundle["renderer_selection"]["fallback_reason"]
        layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
        report = json.loads(Path(bundle["inspection_path"]).read_text())
        assert layout["coverage"]["table_content"] is True
        assert layout["coverage"]["table_cell_bounds"] is True
        assert report["checks_complete"] is True
        assert not ({"OUT_OF_BOUNDS", "CELL_OVERFLOW", "BLANK_RENDER"} & {d["code"] for d in report["defects"]})
        assert all(e["font_size_pt"] >= plan["body_pt"] for e in layout["elements"])
        pg = plan["pages"][page - 1]
        visible = [e["text"] for e in layout["elements"]]
        for col in pg["columns"]:
            assert plan["headers"][col] in visible
            for row in range(*pg["rows"]):
                assert plan["cells"][col][row] in visible
        for e in layout["elements"]:
            if e["role"] in {"title", "subtitle", "footer"}:
                assert e["bbox"]["x"] - e["cell_bbox"]["x"] == pytest.approx(18, abs=0.1)
        # Standalone inspection uses measured containers too.
        assert inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"])["checks_complete"]


def test_fallback_does_not_hide_cell_overflow(tmp_path, monkeypatch):
    _no_r(monkeypatch)
    plan = _plan()
    plan["cells"][0][0] = "An unmeasured replacement that is much wider than the original cell" * 3
    bundle = render_table_from_plan(plan, str(tmp_path))
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert "CELL_OVERFLOW" in {d["code"] for d in report["defects"]}
    assert report["passes_geometry_checks"] is False


def test_public_table_tool_works_without_r(tmp_path, monkeypatch):
    _no_r(monkeypatch)
    async def run():
        result = await create_server().call_tool("render_table_from_plan", {"plan": _plan(), "output_dir": str(tmp_path)})
        assert result.is_error is False
        assert result.structured_content["renderer"] == "matplotlib"
    asyncio.run(run())


def _r_probe(monkeypatch, missing=()):
    monkeypatch.setattr(rendering.shutil, "which", lambda _: "/example/Rscript")
    output = "R\t4.5.0\n" + "".join(f"{p}\t{'MISSING' if p in missing else '1.0'}\n"
                                    for p in ("ggplot2", "ragg", "gridExtra", "gtable", "jsonlite"))
    monkeypatch.setattr(rendering.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=output, stderr=""))


def test_partial_r_install_reports_table_fallback(monkeypatch):
    _r_probe(monkeypatch, missing=("gridExtra",))
    probe = rendering.probe_renderers()
    assert probe["renderers"]["ggplot2"]["available"] is True
    assert probe["table_rendering"]["r_available"] is False
    assert probe["table_rendering"]["available"] is True
    assert probe["table_rendering"]["backend"] == "matplotlib/Agg"


def test_working_r_is_preferred_and_render_errors_do_not_trigger_fallback(tmp_path, monkeypatch):
    _no_r(monkeypatch)
    plan = _plan()
    _r_probe(monkeypatch)
    assert rendering.probe_renderers()["table_rendering"]["r_available"] is True
    calls = []
    def failed_r(source, *args, **kwargs):
        calls.append(source.suffix)
        raise RuntimeError("R build failed")
    monkeypatch.setattr(rendering, "_render_ggplot2", failed_r)
    with pytest.raises(RuntimeError, match="R build failed"):
        render_table_from_plan(plan, str(tmp_path))
    assert calls == [".R"]
    py = tmp_path / "chart.py"
    py.write_text("raise AssertionError('must not execute Python')")
    with pytest.raises(ValueError, match="generate .r source"):
        rendering.render_and_inspect_chart(str(py), str(tmp_path / "chart"))


def test_existing_r_source_gets_actionable_no_r_error(tmp_path, monkeypatch):
    _no_r(monkeypatch)
    source = tmp_path / "chart.R"
    source.write_text("stop('must not execute R')")
    with pytest.raises(ValueError, match="generate .py source"):
        rendering.render_and_inspect_chart(str(source), str(tmp_path / "out"))


@pytest.mark.skipif(not rendering.probe_renderers()["table_rendering"]["r_available"],
                    reason="R table constructor dependencies unavailable")
def test_table_plan_prefers_available_r_in_real_render(tmp_path):
    plan = _plan()
    assert plan["measurement_backend"] == "grid/ragg"
    bundle = render_table_from_plan(plan, str(tmp_path))
    assert bundle["renderer"] == "ggplot2"
    assert bundle["renderer_selection"]["fallback_reason"] is None
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert layout["coverage"]["table_cell_bounds"] is True
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert not ({"OUT_OF_BOUNDS", "CELL_OVERFLOW"} & {d["code"] for d in report["defects"]})


def test_r_measurement_error_is_not_retried_in_python(monkeypatch):
    from dataviz_mcp.table_layout import _metrics
    monkeypatch.setattr(rendering.subprocess, "run", lambda *a, **kw:
                        SimpleNamespace(returncode=1, stdout="", stderr="R metric failure"))
    with pytest.raises(RuntimeError, match="R metric failure"):
        _metrics(["text"], "sans", 12, 144, use_r=True)


# ---- treatments: resolved per cell, drawn by both constructors ----

from dataviz_mcp.color_math import _contrast_ratio
from dataviz_mcp.table_treatment import parse_number


def _benchmark_columns():
    return [
        {"header": "Model", "identifier": True, "cells": ["A", "B", "C", "D"]},
        {"header": "Cost", "cells": ["$0.30", "$5.50", "$24.00", "$60.00"]},
        {"header": "Score", "cells": ["88.8%", "89.1%", "91.4%", "67.4%"]},
    ]


def _lightness(colour):
    return sum(int(colour[i:i + 2], 16) for i in (1, 3, 5))


def test_display_strings_parse_to_numbers():
    assert parse_number("$1,234.5") == 1234.5
    assert parse_number("(3.2%)") == -3.2
    assert parse_number("\u22122") == -2
    assert parse_number("12.5K") == 12500
    assert parse_number("n/a") is None


def test_shading_resolves_ordered_fills_with_legible_ink():
    out = recommend_table_layout(_benchmark_columns(), treatment=[
        {"kind": "shading", "columns": [2]},
        {"kind": "shading", "columns": [1], "higher_is_better": False}])
    styles = out["cell_styles"]
    score = [styles[2][r]["fill"] for r in range(4)]
    # Higher score -> stronger (darker) fill; the lowest score is the lightest.
    assert _lightness(score[2]) < _lightness(score[1]) < _lightness(score[0])
    assert _lightness(score[3]) == max(map(_lightness, score))
    # Lower cost is better, so the cheapest row gets the strongest fill.
    cost = [styles[1][r]["fill"] for r in range(4)]
    assert _lightness(cost[0]) == min(map(_lightness, cost))
    for col in (1, 2):
        for style in styles[col]:
            assert _contrast_ratio(style["ink"], style["fill"]) >= 4.5
    assert out["col_align"] == ["left", "right", "right"]
    assert out["untreated_numeric_columns"] == []


def test_shared_row_scale_needs_commensurability_and_normalises_each_row():
    cols = [{"header": "Metric", "identifier": True, "cells": ["Pace", "HR"]}]
    cols += [{"header": str(k), "cells": [str(p), str(h)]}
             for k, (p, h) in enumerate([(300, 140), (360, 150), (330, 180)])]
    with pytest.raises(ValueError, match="commensurability"):
        recommend_table_layout(cols, treatment={"kind": "shading", "columns": [1, 2, 3], "scope": "row"})
    out = recommend_table_layout(cols, treatment={"kind": "shading", "columns": [1, 2, 3],
                                                  "scope": "row", "commensurable": True})
    fills = [[out["cell_styles"][c][r]["fill"] for c in (1, 2, 3)] for r in (0, 1)]
    # Each row is its own scale: row 0 peaks at column 2, row 1 at column 3.
    assert min(fills[0], key=_lightness) == fills[0][1]
    assert min(fills[1], key=_lightness) == fills[1][2]


def test_bars_reserve_graphic_space_and_start_at_the_baseline():
    plain = recommend_table_layout(_benchmark_columns())
    out = recommend_table_layout(_benchmark_columns(), treatment={"kind": "bar", "columns": [1]})
    assert out["visual_width_px"][1] > 0
    assert out["col_widths_px"][1] > plain["col_widths_px"][1]
    bars = [out["cell_styles"][1][r]["bar"] for r in range(4)]
    assert all(b["start"] == 0 for b in bars)
    assert bars[3]["end"] == 1 and bars[0]["end"] < bars[1]["end"] < bars[2]["end"]


def test_sparklines_show_each_rows_shape_unless_shared():
    cols = [{"header": "Metric", "identifier": True, "cells": ["Pace", "HR"]},
            {"header": "Trend", "cells": ["", ""], "values": [[300, 360, 330], [140, 150, 180]]}]
    out = recommend_table_layout(cols, treatment={"kind": "sparkline", "columns": [1]})
    for r in (0, 1):
        ys = [y for _, y in out["cell_styles"][1][r]["spark"]["points"]]
        assert min(ys) == 0 and max(ys) == 1
    with pytest.raises(ValueError, match="commensurability"):
        recommend_table_layout(cols, treatment={"kind": "sparkline", "columns": [1], "scope": "column"})


def test_emphasis_and_untreated_numbers_warning():
    out = recommend_table_layout(_benchmark_columns(), treatment={"kind": "emphasis", "rows": [0]})
    assert all(out["cell_styles"][c][0]["bold"] for c in range(3))
    assert out["untreated_numeric_columns"] == [1, 2]
    assert any("no magnitude treatment" in w for w in out["warnings"])
    with pytest.raises(ValueError, match="numeric values"):
        recommend_table_layout([{"header": "Name", "cells": ["x", "y"]}],
                               treatment={"kind": "bar", "columns": [0]})


def test_chat_tables_assume_a_screen_display_width():
    wide = [{"header": f"Column {i}", "cells": ["1,234,567"] * 3} for i in range(20)]
    out = recommend_table_layout(wide)
    assert out["delivery"]["display_width_px"] == 800
    assert all(p["width_px"] <= 800 * 22 / 12 + 1 for p in out["pages"])


def _treated_plan():
    return recommend_table_layout(_benchmark_columns(), treatment=[
        {"kind": "bar", "columns": [1]}, {"kind": "shading", "columns": [2]},
        {"kind": "emphasis", "rows": [0], "columns": [0]}],
        title="Treated table", notes="Source: test")


@pytest.mark.parametrize("with_r", [True, False])
def test_both_constructors_draw_the_resolved_treatment(tmp_path, monkeypatch, with_r):
    if with_r and not probe_renderers()["table_rendering"]["r_available"]:
        pytest.skip("R table constructor dependencies unavailable")
    if not with_r:
        _no_r(monkeypatch)
    plan = _treated_plan()
    bundle = render_table_from_plan(plan, str(tmp_path))
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert sum(m["kind"] == "rect" for m in layout["marks"]) == 4 + 4 + 1
    # No sparklines here, so the one captured line is the rule under the header.
    assert len(layout["series"]) == 1
    codes = {d["code"] for d in report["defects"]}
    assert not ({"TREATMENT_NOT_DRAWN", "LOW_TEXT_CONTRAST", "CELL_OVERFLOW"} & codes)
    assert report["checks_complete"] is True


def test_a_dropped_treatment_is_a_defect(tmp_path, monkeypatch):
    _no_r(monkeypatch)
    plan = _treated_plan()
    stripped = {k: v for k, v in plan.items() if k != "cell_styles"}
    build = write_table_build_source(stripped, tmp_path / "build.py")
    bundle = render_and_inspect_chart(
        build, str(tmp_path / "out"), content="table", build_function="build_table",
        inspection_contract={"table_treatment": {"rects": 9, "lines": 0}})
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert "TREATMENT_NOT_DRAWN" in {d["code"] for d in report["defects"]}

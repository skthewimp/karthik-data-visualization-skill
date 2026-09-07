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

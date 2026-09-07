from __future__ import annotations

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
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
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

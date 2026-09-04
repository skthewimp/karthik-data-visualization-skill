from __future__ import annotations

from pathlib import Path

import pytest

from dataviz_mcp import refit
from dataviz_mcp.artifacts import read_json, write_json
from dataviz_mcp.layout import MIN_PANEL_H, PROFILES, suggest_dims_for_overflow
from dataviz_mcp.refit import _grow_residual, _propose_dims, refit_chart


# --- pure helpers -----------------------------------------------------------


def _geometry_summary(dims, *, top_overflow=0.0, right_overflow=0.0, min_panel_h=None):
    squashed = min_panel_h is not None and min_panel_h < MIN_PANEL_H
    edge = {
        "top": round(max(0.0, top_overflow), 2),
        "bottom": 0.0,
        "left": 0.0,
        "right": round(max(0.0, right_overflow), 2),
    }
    suggested = None
    if any(edge.values()) or squashed:
        suggested = suggest_dims_for_overflow(
            dims["width_px"],
            dims["height_px"],
            top_overflow_px=edge["top"],
            right_overflow_px=edge["right"],
            min_panel_height_px=min_panel_h,
        )
    return {
        "clip_px_max": round(max(edge.values()), 2),
        "edge_overflow_px": edge,
        "min_panel_height_px": min_panel_h,
        "panels_squashed": squashed,
        "worst_offenders": [],
        "suggested_dims": suggested,
    }


def test_grow_residual_sums_overflow_and_squash_deficit():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, top_overflow=14.0, right_overflow=6.0)
    assert _grow_residual(gs) == pytest.approx(20.0)


def test_grow_residual_counts_squashed_panels():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, min_panel_h=MIN_PANEL_H - 40.0)
    assert _grow_residual(gs) == pytest.approx(40.0)


def test_grow_residual_zero_on_clean_geometry():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    assert _grow_residual(_geometry_summary(dims)) == 0.0


def test_propose_dims_grows_by_the_overflow():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, top_overflow=30.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["height_px"] == 705
    assert proposed["width_px"] == 1200
    assert proposed["dpi"] == 144


def test_propose_dims_clamps_to_ceiling():
    dims = {"width_px": 1200, "height_px": 675, "dpi": 144}
    gs = _geometry_summary(dims, right_overflow=5000.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["width_px"] == 1600  # clamped, not 6200


def test_propose_dims_never_shrinks_below_current():
    dims = {"width_px": 2000, "height_px": 675, "dpi": 144}  # already past a 1600 ceiling
    gs = _geometry_summary(dims, top_overflow=30.0)
    proposed = _propose_dims(gs, dims, max_w=1600, max_h=1400)
    assert proposed["width_px"] == 2000  # ceiling never forces a shrink


# --- the loop (fake renderer, no real render) -------------------------------


class _FakeRender:
    """Stands in for render_and_inspect_chart: writes a real inspection.json per pass."""

    def __init__(self, geom_fn):
        self.geom_fn = geom_fn
        self.calls: list[dict] = []

    def __call__(
        self,
        source_path,
        output_dir,
        renderer="auto",
        delivery_profile="chat",
        dimensions=None,
        artifact_name="chart.png",
        build_function="build_chart",
        content="chart",
    ):
        index = len(self.calls)
        self.calls.append(dict(dimensions))
        gs, defects = self.geom_fn(dimensions, index)
        report = {
            "schema_version": 3,
            "geometry_summary": gs,
            "defects": defects,
            "passes_geometry_checks": not defects,
            "width": dimensions["width_px"],
            "height": dimensions["height_px"],
        }
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        inspection_path = out / "inspection.json"
        write_json(inspection_path, report)
        return {
            "artifact": {
                "path": str(out / "chart.png"),
                "width": dimensions["width_px"],
                "height": dimensions["height_px"],
                "sha256": "deadbeef",
            },
            "layout_metadata_path": str(out / "layout-metadata.json"),
            "manifest_path": str(out / "manifest.json"),
            "inspection_path": str(inspection_path),
            "review_view_paths": [],
            "renderer": "matplotlib",
            "content": content,
        }


def _install(monkeypatch, geom_fn):
    fake = _FakeRender(geom_fn)
    monkeypatch.setattr(refit, "render_and_inspect_chart", fake)
    return fake


def test_growing_clears_the_clip_and_reports_resolved(tmp_path, monkeypatch):
    need_h = 900

    def geom(dims, _index):
        overflow = max(0.0, need_h - dims["height_px"])
        gs = _geometry_summary(dims, top_overflow=overflow)
        defects = (
            [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]
            if overflow
            else []
        )
        return gs, defects

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True
    assert result["final_dimensions"]["height_px"] >= need_h
    assert fake.calls[-1]["height_px"] >= need_h
    assert result["history"][0]["action"] == "grow"
    assert result["history"][-1]["action"] == "resolved"


def test_ceiling_is_warned_not_squashed(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims, right_overflow=5000.0)
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is False
    ceiling = PROFILES["chat"]["max_width_px"]
    assert result["final_dimensions"]["width_px"] == ceiling
    assert any("ceiling" in w for w in result["warnings"])
    assert result["history"][-1]["action"] == "ceiling_reached"


def test_no_improvement_stops_the_loop(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims, top_overflow=50.0)  # constant, growth never helps
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=5)
    assert result["resolved"] is False
    assert result["history"][-1]["action"] == "no_improvement"
    assert len(fake.calls) == 2  # initial + one ineffective grow, then stop
    assert any("improv" in w for w in result["warnings"])


def test_max_iterations_is_respected(tmp_path, monkeypatch):
    # Overflow keeps falling (so each grow improves) but never reaches zero within the budget,
    # and stays well under the ceiling so max_iterations is the exit, not ceiling_reached.
    def geom(dims, index):
        overflow = [40.0, 20.0, 10.0][index]
        gs = _geometry_summary(dims, top_overflow=overflow)
        return gs, [{"code": "OUT_OF_BOUNDS", "severity": "high", "element_ids": [], "message": "x"}]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=2)
    assert len(fake.calls) == 3  # initial render + 2 regrows
    assert result["history"][-1]["action"] == "max_iterations"


def test_underfill_is_reported_but_not_resized(tmp_path, monkeypatch):
    def geom(dims, _index):
        gs = _geometry_summary(dims)  # clean geometry, nothing to grow
        return gs, [
            {"code": "UNDERFILLED_CANVAS", "severity": "low", "element_ids": [], "message": "empty"}
        ]

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True  # nothing resize-fixable remains
    assert result["underfilled"] is True
    assert len(fake.calls) == 1  # never grew
    assert any("underfill" in w.lower() for w in result["warnings"])


def test_clean_chart_needs_a_single_pass(tmp_path, monkeypatch):
    def geom(dims, _index):
        return _geometry_summary(dims), []

    fake = _install(monkeypatch, geom)
    result = refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"))
    assert result["resolved"] is True
    assert result["underfilled"] is False
    assert len(fake.calls) == 1
    assert result["warnings"] == []


def test_max_iterations_must_be_positive(tmp_path):
    with pytest.raises(ValueError):
        refit_chart(str(tmp_path / "src.py"), str(tmp_path / "out"), max_iterations=0)


# --- live renders (real matplotlib / ggplot2, no fakes) ---------------------


_CLIP_MPL = '''
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


def build_chart():
    fig, ax = plt.subplots()
    ax.bar(["a", "b", "c", "d"], [3, 7, 4, 9], color="#4c72b0")
    ax.set_ylabel("Revenue")
    # Headline pinned at a fixed physical position: it overruns the top of a short canvas and
    # a taller canvas clears it exactly.
    fig.text(0.15, 1.9, "Quarterly revenue by division", fontsize=30, va="bottom",
             transform=fig.dpi_scale_trans)
    return fig
'''


def test_live_matplotlib_grows_until_the_clip_clears(tmp_path):
    source = tmp_path / "clip.py"
    source.write_text(_CLIP_MPL, encoding="utf-8")
    result = refit_chart(
        str(source),
        str(tmp_path / "out"),
        renderer="matplotlib",
        delivery_profile="document",
        dimensions={"width_px": 520, "height_px": 300, "dpi": 144},
        max_iterations=4,
    )
    assert result["history"][0]["clip_px_max"] > 100  # really clipped at the start
    assert result["resolved"] is True
    assert result["history"][-1]["clip_px_max"] == 0.0
    assert result["final_dimensions"]["height_px"] > 300  # it grew


_SQUASH_GG = '''
library(ggplot2)

build_chart <- function() {
  set.seed(1)
  df <- data.frame(
    x = rep(1:10, times = 6),
    y = rnorm(60),
    panel = factor(rep(paste("Region", 1:6), each = 10))
  )
  ggplot(df, aes(x, y)) +
    geom_line(colour = "#4c72b0") +
    facet_wrap(~panel, ncol = 2) +
    labs(title = "Signal by region", y = "Value") +
    theme_minimal()
}
'''


def _ggplot2_available() -> bool:
    from dataviz_mcp.rendering import probe_renderers

    return probe_renderers()["renderers"]["ggplot2"]["available"]


@pytest.mark.skipif(not _ggplot2_available(), reason="ggplot2 renderer unavailable")
def test_live_ggplot_grows_squashed_facet_panels(tmp_path):
    source = tmp_path / "squash.R"
    source.write_text(_SQUASH_GG, encoding="utf-8")
    result = refit_chart(
        str(source),
        str(tmp_path / "out"),
        renderer="ggplot2",
        delivery_profile="document",
        dimensions={"width_px": 700, "height_px": 320, "dpi": 144},
        max_iterations=4,
    )
    assert result["renderer"] == "ggplot2"
    heights = [h["min_panel_height_px"] for h in result["history"]]
    assert heights[0] < MIN_PANEL_H  # panels started squashed
    assert all(later > earlier for earlier, later in zip(heights, heights[1:]))  # each grow helps
    assert result["final_dimensions"]["height_px"] > 320


def test_dimensions_override_the_starting_size(tmp_path, monkeypatch):
    def geom(dims, _index):
        return _geometry_summary(dims), []

    fake = _install(monkeypatch, geom)
    refit_chart(
        str(tmp_path / "src.py"),
        str(tmp_path / "out"),
        dimensions={"width_px": 1000, "height_px": 800, "dpi": 120},
    )
    assert fake.calls[0] == {"width_px": 1000, "height_px": 800, "dpi": 120}

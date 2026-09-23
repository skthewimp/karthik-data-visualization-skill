from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from dataviz_mcp import handoff
from dataviz_mcp.layout import recommend_layout
from dataviz_mcp.plot_data import prepare_plot_data
from dataviz_mcp.rendering import probe_renderers, render_and_inspect_chart
from dataviz_mcp.scaffold import MARKS_BEGIN, MARKS_END, _parse_date, check_chart, scaffold_chart

R_AVAILABLE = probe_renderers()["renderers"]["ggplot2"]["available"]
PALETTE = {"ordered_palette": ["#0072B2", "#D55E00"]}


def _frame(tmp_path: Path, **kwargs) -> str:
    rows = kwargs.pop("rows", [["Tokens", 95, 4], ["Cost", 50, 30]])
    result = prepare_plot_data(
        str(tmp_path), "Measure", ["Reads", "Writes"],
        columns=["Measure", "Reads", "Writes"], rows=rows, **kwargs,
    )
    return result["plot_data_path"]


def _scaffold(tmp_path: Path, **kwargs) -> dict:
    copy = kwargs.pop("public_copy", {"title": "Reads are most tokens but half the cost"})
    return scaffold_chart(
        str(tmp_path), kwargs.pop("plot_data_path", None) or _frame(tmp_path), copy,
        layout=kwargs.pop("layout", recommend_layout(x_slots=2)), colours=kwargs.pop("colours", PALETTE),
        **kwargs,
    )


def _fill(source: str, body: str) -> None:
    text = Path(source).read_text(encoding="utf-8")
    head, rest = text.split(MARKS_BEGIN)
    tail = rest.split(MARKS_END)[1]
    Path(source).write_text(f"{head}{MARKS_BEGIN}\n{body}\n{MARKS_END}{tail}", encoding="utf-8")


GOOD_MARKS = """chart_marks <- function(d) {
  list(
    geom_line(aes(x = category, y = value, group = series, colour = series)),
    geom_text(aes(x = category, y = value, label = fmt_value(value), colour = series), size = label_size)
  )
}"""


def test_routing_block_carries_the_scaffold_scalars() -> None:
    text = """## DESIGN
slopegraph
```routing
builder: chart
identification_strategy: subtitle key
x_kind: Date
value_labels: 8 labels
zero_baseline: no
value_encoding: nonsense
```"""
    keys = ("builder", "identification_strategy", "x_kind", "value_labels", "zero_baseline", "value_encoding")
    routing = handoff.parse_routing(text, keys)
    assert routing == {
        "builder": "chart",
        "identification_strategy": "subtitle_key",
        "x_kind": "date",
        "value_labels": 8,
        "zero_baseline": False,
        "value_encoding": "position",  # an unknown word degrades to the default, never raises
    }


@pytest.mark.parametrize(
    ("label", "expected"),
    [("2019", "2019-01-01"), ("2019-03", "2019-03-01"), ("Mar 2019", "2019-03-01"),
     ("Q2 2024", "2024-04-01"), ("Q1'25", "2025-01-01"), ("2024-06-30", "2024-06-30")],
)
def test_time_labels_parse_to_real_dates(label: str, expected: str) -> None:
    assert _parse_date(label).isoformat() == expected


def test_period_ranges_are_not_dates() -> None:
    assert _parse_date("2010-14") is None
    assert _parse_date("FY24 H1") is None


def test_scaffold_writes_the_planned_settings_and_one_slot(tmp_path: Path) -> None:
    layout = recommend_layout(x_slots=2)
    result = _scaffold(
        tmp_path,
        layout=layout,
        public_copy={"title": "Reads are most tokens but half the cost", "axis_titles": {"x": "Period"}},
        number_format={"step": 1.0, "suffix": "%"},
    )
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert source.count(MARKS_BEGIN) == 1 and source.count(MARKS_END) == 1
    # Fonts and palette come from the tools, not a model's guess.
    assert f"size = {layout['font_pt']['title']}" in source
    assert 'palette <- c("Reads" = "#0072B2", "Writes" = "#D55E00")' in source
    assert "accuracy = 1.0" in source and 'suffix = "%"' in source
    # Only the declared axis title is drawn; no legend without a legend strategy; no limits.
    assert 'x = "Period"' in source and "y = NULL" in source
    assert 'legend.position = "none"' in source
    assert "limits" not in source
    # Labels past the panel edge must reach the canvas, where refit can measure and grow for them.
    assert 'coord_cartesian(clip = "off")' in source
    # The scaffold's scales, labs and theme come after the slot, so the slot cannot win.
    assert source.index(MARKS_END) < source.index("scale_colour_manual")


def test_value_axis_goes_when_planned_labels_carry_the_reading(tmp_path: Path) -> None:
    shown = _scaffold(tmp_path / "shown", value_labels=0)
    hidden = _scaffold(
        tmp_path / "hidden", value_labels=4,
        public_copy={"title": "t", "axis_titles": {"y": "Share (%)"}},
    )
    assert not shown["value_axis_hidden"]
    assert hidden["value_axis_hidden"]
    source = Path(hidden["source_path"]).read_text(encoding="utf-8")
    assert "axis.text.y = element_blank()" in source
    assert "panel.grid.major.y = element_blank()" in source
    # An axis title on a hidden axis would float alone, so it is dropped and said so.
    assert "y = NULL" in source
    assert any("axis title" in w for w in hidden["warnings"])


def test_horizontal_chart_flips_and_reads_top_down(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, orientation="horizontal", public_copy={"title": "t", "axis_titles": {"x": "Share"}})
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert 'coord_flip(clip = "off")' in source
    assert "scale_x_discrete(limits = rev)" in source
    # A displayed-x title lands on the value aesthetic under the flip.
    assert 'y = "Share"' in source and "x = NULL" in source


def test_zero_baseline_and_date_axis(tmp_path: Path) -> None:
    months = [["Jan 2020", 1, 2], ["Feb 2020", 2, 3], ["Mar 2020", 3, 5]]
    result = _scaffold(tmp_path, plot_data_path=_frame(tmp_path, rows=months), x_kind="date", zero_baseline=True)
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert "as.Date(plot_data$category)" in source
    assert "scale_x_date(labels = scales::label_date_short())" in source
    assert "limits = c(0, NA)" in source
    data = Path(result["chart_data_path"]).read_text(encoding="utf-8")
    assert "2020-02-01" in data


def test_unparseable_dates_fall_back_to_discrete_with_a_warning(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, x_kind="date")
    assert "factor(plot_data$category" in Path(result["source_path"]).read_text(encoding="utf-8")
    assert any("could not read" in w for w in result["warnings"])


def test_frame_text_is_drawn_as_reserve_frame_wrapped_it(tmp_path: Path) -> None:
    long = "Reads were most of the tokens but only half of the bill, while writes and output made up the rest of it"
    result = _scaffold(tmp_path, public_copy={"title": "t", "subtitle": long})
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert "\\n" in source.split("subtitle = ")[1].split("\n")[0]


def test_subtitle_key_colours_series_names(tmp_path: Path) -> None:
    result = _scaffold(
        tmp_path, identification="subtitle_key",
        public_copy={"title": "t", "subtitle": "Reads fell while Writes rose"},
    )
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert "<span style='color:#0072B2'>Reads</span>" in source
    assert "<span style='color:#D55E00'>Writes</span>" in source
    assert "ggtext::element_markdown" in source


def test_check_restores_an_edited_scaffold(tmp_path: Path) -> None:
    result = _scaffold(tmp_path)
    source = Path(result["source_path"])
    edited = source.read_text(encoding="utf-8").replace("legend.position = \"none\"", "legend.position = \"right\"")
    source.write_text(edited, encoding="utf-8")
    report = check_chart(str(source))
    assert report["restored_scaffold"]
    assert 'legend.position = "none"' in source.read_text(encoding="utf-8")


def test_check_reports_a_missing_slot(tmp_path: Path) -> None:
    result = _scaffold(tmp_path)
    Path(result["source_path"]).write_text("build_chart <- function() NULL\n", encoding="utf-8")
    report = check_chart(result["source_path"])
    assert not report["ok"]
    assert report["deviations"][0]["code"] == "MARKS_SLOT_MISSING"


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_check_passes_clean_marks_and_renders(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, value_labels=4)
    _fill(result["source_path"], GOOD_MARKS)
    report = check_chart(result["source_path"])
    assert report == {"ok": True, "restored_scaffold": False, "deviations": [], "fix_list": ""}
    bundle = render_and_inspect_chart(result["source_path"], str(tmp_path / "out"), dimensions=result["dimensions"])
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text(encoding="utf-8"))
    # No legend and no axis titles reached the pixels.
    roles = {element.get("role") for element in layout["elements"]}
    assert "legend_text" not in roles
    assert "axis_label" not in roles


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_check_names_each_slot_deviation(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, value_labels=4)
    _fill(
        result["source_path"],
        """chart_marks <- function(d) {
  list(
    geom_line(aes(x = category, y = value, group = series), colour = "#3366cc"),
    geom_label(aes(x = category, y = value, label = "x"), size = 3),
    scale_y_continuous(limits = c(0, 100))
  )
}""",
    )
    codes = {d["code"] for d in check_chart(result["source_path"])["deviations"]}
    assert codes == {"MARKS_NON_LAYER", "GEOM_LABEL", "COLOUR_NOT_IN_PALETTE", "TEXT_TOO_SMALL"}


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_value_on_a_discrete_axis_fails_the_build_with_a_fix(tmp_path: Path) -> None:
    # The flat-slopegraph bug: series on y, value only in the label text.
    result = _scaffold(tmp_path)
    _fill(
        result["source_path"],
        "chart_marks <- function(d) list(geom_line(aes(x = category, y = series, group = series)))",
    )
    report = check_chart(result["source_path"])
    assert report["deviations"][0]["code"] == "BUILD_ERROR"
    assert "map y = value" in report["deviations"][0]["message"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_hidden_value_axis_requires_the_promised_labels(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, value_labels=4)
    _fill(
        result["source_path"],
        "chart_marks <- function(d) list(geom_line(aes(x = category, y = value, group = series, colour = series)))",
    )
    codes = [d["code"] for d in check_chart(result["source_path"])["deviations"]]
    assert codes == ["VALUE_LABELS_MISSING"]


def test_matplotlib_scaffold_checks_and_renders(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, renderer="matplotlib", value_labels=4)
    source = result["source_path"]
    assert source.endswith(".py")
    text = Path(source).read_text(encoding="utf-8")
    head, rest = text.split(MARKS_BEGIN)
    tail = rest.split(MARKS_END)[1]
    body = """def chart_marks(ax, rows):
    for name, colour in PALETTE.items():
        pts = sorted((pos(r), r['value']) for r in rows if r['series'] == name)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=colour)
        for x, y in pts:
            ax.text(x, y, fmt_value(y), color=colour, fontsize=LABEL_PT)"""
    Path(source).write_text(f"{head}{MARKS_BEGIN}\n{body}\n{MARKS_END}{tail}", encoding="utf-8")
    assert check_chart(source)["ok"]
    bundle = render_and_inspect_chart(source, str(tmp_path / "out"), renderer="matplotlib", dimensions=result["dimensions"])
    assert Path(bundle["artifact"]["path"]).is_file()
    # A hand-picked hue in the slot is caught on the built figure.
    stray = body.replace("color=colour)", "color='#3366cc')")
    Path(source).write_text(f"{head}{MARKS_BEGIN}\n{stray}\n{MARKS_END}{tail}", encoding="utf-8")
    assert [d["code"] for d in check_chart(source)["deviations"]] == ["COLOUR_NOT_IN_PALETTE"]
    assert re.search(r"1\. Marks use #3366cc", check_chart(source)["fix_list"])


def test_direct_label_room_is_reserved_past_the_last_point(tmp_path: Path) -> None:
    # Eight periods leave too little axis expansion for "Writes: 12%" past the last point.
    rows = [[str(2010 + i), 40 + i, 10 + i] for i in range(8)]
    plain = _scaffold(tmp_path / "plain", identification="axis", plot_data_path=_frame(tmp_path / "plain", rows=rows))
    labelled = _scaffold(
        tmp_path / "labelled", identification="direct_labels", value_labels=4,
        plot_data_path=_frame(tmp_path / "labelled", rows=rows),
    )
    right = lambda r: float(re.search(r"plot.margin = margin\(([^)]*)\)", Path(r["source_path"]).read_text()).group(1).split(",")[1])
    assert right(labelled) > right(plain)


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_stacked_labels_computed_apart_from_the_bars_are_caught(tmp_path: Path) -> None:
    # The haiku failure: a hand cumsum in the opposite order to ggplot's stack, and hex strings
    # mapped through the series colour scale (they fall to its NA grey).
    result = _scaffold(tmp_path, value_labels=4, zero_baseline=True)
    _fill(
        result["source_path"],
        """chart_marks <- function(d) {
  d <- d[order(d$category, d$order), ]
  d$mid <- ave(d$value, d$category, FUN = cumsum) - d$value / 2
  d$ink <- "#FFFFFF"
  list(
    geom_col(aes(x = category, y = value, fill = series)),
    geom_text(data = d, aes(x = category, y = mid, label = fmt_value(value), colour = ink), size = label_size)
  )
}""",
    )
    codes = {d["code"] for d in check_chart(result["source_path"])["deviations"]}
    assert codes == {"COLOUR_UNMAPPED", "LABEL_ON_WRONG_MARK", "STACK_ORDER"}
    _fill(
        result["source_path"],
        """chart_marks <- function(d) {
  list(
    geom_col(aes(x = category, y = value, fill = series), position = stack),
    geom_text(aes(x = category, y = value, label = fmt_value(value), group = series),
              position = stack_mid, colour = "#FFFFFF", size = label_size)
  )
}""",
    )
    assert check_chart(result["source_path"])["ok"]


def test_returned_frame_matches_the_drawn_margin(tmp_path: Path) -> None:
    from dataviz_mcp.frame import reserve_frame

    rows = [[str(2010 + i), 40 + i, 10 + i] for i in range(8)]
    frame = reserve_frame(title="t", width_px=1200, height_px=700, dpi=144)
    result = _scaffold(
        tmp_path, frame=frame, identification="direct_labels", value_labels=4,
        layout={"width_px": 1200, "height_px": 700, "dpi": 144},
        plot_data_path=_frame(tmp_path, rows=rows),
    )
    drawn = result["frame"]
    extra = drawn["plot_margin_px"]["right"] - frame["plot_margin_px"]["right"]
    assert extra > 0
    assert drawn["plot_area"]["width"] == round(frame["plot_area"]["width"] - extra, 1)


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_default_stack_runs_against_the_series_order(tmp_path: Path) -> None:
    # ggplot's default stack puts the first series furthest from the baseline.
    result = _scaffold(tmp_path, zero_baseline=True, orientation="horizontal")
    _fill(
        result["source_path"],
        "chart_marks <- function(d) list(geom_col(aes(x = category, y = value, fill = series), "
        "position = position_stack(vjust = 0.5)))",
    )
    assert [d["code"] for d in check_chart(result["source_path"])["deviations"]] == ["STACK_ORDER"]
    _fill(
        result["source_path"],
        "chart_marks <- function(d) list(geom_col(aes(x = category, y = value, fill = series), position = stack))",
    )
    assert check_chart(result["source_path"])["ok"]


def test_matplotlib_stack_helper_keeps_series_order(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, renderer="matplotlib", orientation="horizontal", zero_baseline=True)
    source = result["source_path"]
    _fill(source, "def chart_marks(ax, rows):\n    stack(ax, rows)")
    assert check_chart(source)["ok"]
    # Drawing the series in reverse puts the last series at the baseline.
    _fill(
        source,
        """def chart_marks(ax, rows):
    base = {}
    for name in reversed(list(PALETTE)):
        for row in rows:
            if row['series'] == name:
                x = pos(row)
                ax.barh(x, row['value'], left=base.get(x, 0.0), color=PALETTE[name])
                base[x] = base.get(x, 0.0) + row['value']""",
    )
    assert [d["code"] for d in check_chart(source)["deviations"]] == ["STACK_ORDER"]

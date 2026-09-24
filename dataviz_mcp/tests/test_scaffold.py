from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from dataviz_mcp import handoff
from dataviz_mcp.color_math import _contrast_ratio, hue_delta
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
    # Only the declared axis title is drawn; no legend without a legend strategy; no value limits.
    assert 'x = "Period"' in source and "y = NULL" in source
    assert 'legend.position = "none"' in source
    assert "scale_y_continuous(labels = fmt_value)" in source
    # The category axis keeps the planned order whatever order a layer trains it in.
    assert 'scale_x_discrete(limits = function(x) intersect(c("Tokens", "Cost"), x))' in source
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
    assert 'scale_x_discrete(limits = function(x) rev(intersect(c("Tokens", "Cost"), x)))' in source
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
    # A series colour that already reads as text is used as is; one too light for words is
    # darkened to text contrast in its own hue, so the key still matches the marks.
    assert "<span style='color:#0072B2'>Reads</span>" in source
    writes = re.search(r"<span style='color:(#[0-9a-fA-F]{6})'>Writes</span>", source)[1]
    assert writes.lower() != "#d55e00" and _contrast_ratio(writes, "#FFFFFF") >= 4.5
    assert abs(hue_delta(writes, "#D55E00")) < 3
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
def test_value_left_off_the_value_axis_is_caught(tmp_path: Path) -> None:
    # A slopegraph that builds but draws flat: y is a constant, the value only in the labels.
    result = _scaffold(tmp_path)
    _fill(
        result["source_path"],
        """chart_marks <- function(d) {
  list(
    geom_line(aes(x = category, y = 1, group = series, colour = series)),
    geom_text(aes(x = category, y = 1, label = fmt_value(value), colour = series), size = label_size)
  )
}""",
    )
    codes = [d["code"] for d in check_chart(result["source_path"])["deviations"]]
    assert codes == ["VALUE_NOT_ON_POSITION"]


def test_matplotlib_value_left_off_the_value_axis_is_caught(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, renderer="matplotlib")
    source = result["source_path"]
    _fill(
        source,
        """def chart_marks(ax, rows):
    for name, colour in PALETTE.items():
        pts = [pos(r) for r in rows if r['series'] == name]
        ax.plot(pts, [1] * len(pts), color=colour)""",
    )
    assert [d["code"] for d in check_chart(source)["deviations"]] == ["VALUE_NOT_ON_POSITION"]


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
    # The unmapped hex falls to the scale's NA grey, which also fails against the fills; the
    # label placed on the other series' segment is also far from its own.
    assert codes == {"COLOUR_UNMAPPED", "LABEL_ON_WRONG_MARK", "LABEL_OFF_ITS_MARK", "STACK_ORDER",
                     "LOW_CONTRAST_ON_MARK"}
    _fill(
        result["source_path"],
        """chart_marks <- function(d) {
  list(
    geom_col(aes(x = category, y = value, fill = series), position = stack),
    geom_text(aes(x = category, y = value, label = fmt_value(value), group = series,
                  colour = on_fill_ink(series)), position = stack_mid, size = label_size)
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


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_text_on_a_mark_is_judged_against_its_fill(tmp_path: Path) -> None:
    # White reads on the blue but not on the orange; the scaffold's ink reads on both.
    result = _scaffold(tmp_path, zero_baseline=True)
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert 'on_ink <- c("Reads" = "#ffffff", "Writes" = "#1a1a1a")' in source
    bars = "geom_col(aes(x = category, y = value, fill = series), position = stack)"
    white = (f"chart_marks <- function(d) list({bars}, geom_text(aes(x = category, y = value, "
             "label = fmt_value(value), group = series), position = stack_mid, colour = '#FFFFFF', size = label_size))")
    _fill(result["source_path"], white)
    report = check_chart(result["source_path"])
    assert [d["code"] for d in report["deviations"]] == ["LOW_CONTRAST_ON_MARK"]
    assert "#ffffff on #D55E00".lower() in report["fix_list"].lower()
    _fill(result["source_path"], white.replace("colour = '#FFFFFF', ", "").replace(
        "group = series)", "group = series, colour = on_fill_ink(series))"))
    assert check_chart(result["source_path"])["ok"]


def test_matplotlib_on_mark_ink(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, renderer="matplotlib", zero_baseline=True)
    source = result["source_path"]
    labelled = """def chart_marks(ax, rows):
    for row, x, mid, ink in stack(ax, rows):
        ax.text(x, mid, fmt_value(row['value']), color=INK_CHOICE, ha='center', va='center', fontsize=LABEL_PT)"""
    _fill(source, labelled.replace("INK_CHOICE", "ink"))
    assert check_chart(source)["ok"]
    _fill(source, labelled.replace("INK_CHOICE", "'#ffffff'"))
    assert [d["code"] for d in check_chart(source)["deviations"]] == ["LOW_CONTRAST_ON_MARK"]


# ---- label attachment and the surface behind text (canonical first-pass failures) ----

TINY = [["cacheRead", 95.0], ["cacheWrite", 4.2], ["output", 0.5], ["input", 0.3]]


def _single(tmp_path: Path, rows=TINY, **kwargs) -> dict:
    path = prepare_plot_data(str(tmp_path), "Kind", ["Share"], columns=["Kind", "Share"], rows=rows)["plot_data_path"]
    return scaffold_chart(
        str(tmp_path), path, {"title": "Cache reads dominate"},
        layout={"width_px": 1200, "height_px": 700, "dpi": 144},
        colours={"ordered_palette": ["#247A52"]}, orientation="horizontal", zero_baseline=True, **kwargs,
    )


def _codes(source: str) -> list[str]:
    return [d["code"] for d in check_chart(source)["deviations"]]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_value_past_the_bar_end_reads_on_the_page_not_the_fill(tmp_path: Path) -> None:
    # The label anchors at the bar's end but its glyphs run outward onto the page, so the bar
    # colour is legible there; judging it by its anchor called it green-on-green.
    result = _single(tmp_path)
    outside = """chart_marks <- function(d) list(
  geom_col(aes(x = category, y = value), fill = ink, width = 0.7),
  geom_text(aes(x = category, y = value, label = fmt_value(value)), colour = ink, size = label_size, hjust = -0.1)
)"""
    _fill(result["source_path"], outside)
    assert check_chart(result["source_path"])["ok"]
    # Centred on the bars, the same ink is on its own fill.
    _fill(result["source_path"], outside.replace("hjust = -0.1", "hjust = 0.5, position = position_stack(vjust = 0.5)"))
    assert _codes(result["source_path"]) == ["LOW_CONTRAST_ON_MARK"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_on_fill_ink_spilling_off_a_short_bar_is_caught_on_the_page(tmp_path: Path) -> None:
    result = _single(tmp_path)
    _fill(result["source_path"], """chart_marks <- function(d) list(
  geom_col(aes(x = category, y = value), fill = ink, width = 0.7),
  geom_text(aes(x = category, y = value, label = fmt_value(value)), colour = on_fill_ink(), size = label_size, hjust = 1.1)
)""")
    report = check_chart(result["source_path"])
    assert [d["code"] for d in report["deviations"]] == ["LOW_CONTRAST_ON_PAGE"]
    # The long bars hold their white labels; only the shortest spill onto the page.
    assert "'95.0'" not in report["fix_list"] and "'0.3'" in report["fix_list"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_bar_values_put_each_value_where_it_reads(tmp_path: Path) -> None:
    result = _single(tmp_path)
    _fill(result["source_path"], """chart_marks <- function(d) list(
  geom_col(aes(x = category, y = value), fill = ink, width = 0.7),
  bar_values(aes(x = category, y = value, label = fmt_value(value)))
)""")
    assert check_chart(result["source_path"])["ok"]
    bundle = render_and_inspect_chart(result["source_path"], str(tmp_path / "render"), renderer="ggplot2",
                                      dimensions=result["dimensions"])
    inspection = json.loads(Path(bundle["inspection_path"]).read_text())
    assert not inspection["low_contrast_elements"]
    metadata = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    ink = {e["text"]: e["colour"].lower() for e in metadata["elements"] if e["role"] == "data_label"}
    # Inside the long bar in white; past the ends of the short ones in dark ink.
    assert ink["95.0"].startswith("#ffffff") and ink["0.3"].startswith("#1a1a1a")


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_grouped_labels_are_matched_by_identity_not_by_the_printed_number(tmp_path: Path) -> None:
    rows = [["Total", 70398, 77264], ["Network", 7413, 7256]]
    path = prepare_plot_data(str(tmp_path), "Line", ["Q1'24", "Q1'25"], columns=["Line", "Q1'24", "Q1'25"],
                             rows=rows)["plot_data_path"]
    result = scaffold_chart(str(tmp_path), path, {"title": "t"}, layout={"width_px": 1200, "height_px": 600, "dpi": 144},
                            colours=PALETTE, orientation="horizontal", zero_baseline=True)
    bars = "geom_col(aes(x = category, y = value, fill = series, group = series), position = position_dodge(width = 0.8), width = 0.8)"
    # A label carrying its period ("Q1'24: $70,398") is not a number to parse: its first digit is
    # the quarter. Matched by observation, it is on its own bar.
    label = "label = paste0(series, ': $', fmt_value(value))"
    _fill(result["source_path"], f"chart_marks <- function(d) list({bars}, bar_values(aes(x = category, y = value, "
          f"fill = series, group = series, {label}), position = position_dodge(width = 0.8)))")
    assert check_chart(result["source_path"])["ok"]
    # Labels left undodged sit on the boundary of the touching pair, over one period's bar: the
    # fix names the bars' own dodge.
    _fill(result["source_path"], f"chart_marks <- function(d) list({bars}, geom_text(aes(x = category, y = value, "
          f"group = series, {label}), colour = on_fill_ink(), hjust = 1.1, size = label_size))")
    report = check_chart(result["source_path"])
    assert "LABEL_ON_WRONG_MARK" in [d["code"] for d in report["deviations"]]
    assert "position_dodge(width = 0.8)" in report["fix_list"] and "stack" not in report["fix_list"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_stacking_line_labels_detaches_them_from_their_lines(tmp_path: Path) -> None:
    rows = [[str(2010 + i), 40 + i, 10 + i] for i in range(6)]
    result = _scaffold(tmp_path, plot_data_path=_frame(tmp_path, rows=rows))
    end = "d[d$category == tail(levels(d$category), 1), ]"
    labels = (f"geom_text(data = {end}, aes(x = category, y = value, label = series, colour = series, group = series), "
              "size = label_size, hjust = 0POSITION)")
    body = ("chart_marks <- function(d) list(geom_line(aes(x = category, y = value, colour = series, group = series)), "
            + labels + ")")
    _fill(result["source_path"], body.replace("POSITION", ""))
    assert check_chart(result["source_path"])["ok"]
    _fill(result["source_path"], body.replace("POSITION", ", position = stack_mid"))
    report = check_chart(result["source_path"])
    assert {d["code"] for d in report["deviations"]} == {"LABEL_OFF_ITS_MARK"}
    assert "drop that adjustment" in report["fix_list"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_a_faint_background_band_is_not_a_mark(tmp_path: Path) -> None:
    # A shaded projection band behind the lines is neither a bar to match labels to nor a fill
    # that the labels must contrast with - its 4% tint leaves the page behind them.
    rows = [[str(2010 + i), 40 + i, 10 + i] for i in range(6)]
    result = _scaffold(tmp_path, plot_data_path=_frame(tmp_path, rows=rows))
    band = """chart_marks <- function(d) list(
  BAND,
  geom_line(aes(x = category, y = value, colour = series, group = series)),
  geom_text(data = d[d$category == tail(levels(d$category), 1), ],
            aes(x = category, y = value, label = fmt_value(value), colour = series), size = label_size, hjust = 0)
)"""
    _fill(result["source_path"], band.replace("BAND", "annotate('rect', xmin = 3.5, xmax = Inf, ymin = -Inf, ymax = Inf, fill = ink, alpha = 0.045)"))
    assert check_chart(result["source_path"])["ok"]
    # The same band drawn as a finite tile twice the data's height sets the axis instead.
    _fill(result["source_path"], band.replace("BAND", "geom_tile(data = d[d$series == 'Reads' & as.integer(d$category) > 3, ], "
                                              "aes(x = category, y = 50), inherit.aes = FALSE, width = 1, height = 100, fill = ink, alpha = 0.045)"))
    assert _codes(result["source_path"]) == ["DECORATION_STRETCHES_AXIS"]


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_value_span_is_compared_in_the_value_scale_space(tmp_path: Path) -> None:
    rows = [["A", 1, 10], ["B", 100, 1000], ["C", 10000, 100000]]
    result = _scaffold(tmp_path, plot_data_path=_frame(tmp_path, rows=rows))
    sidecar = Path(result["source_path"] + ".scaffold.json")
    record = json.loads(sidecar.read_text())
    # A consumer that puts the value axis on a log scale extends the scaffold record itself.
    record["tail"] = record["tail"].replace("scale_y_continuous(labels = fmt_value)",
                                            'scale_y_continuous(labels = fmt_value, transform = "log10")')
    sidecar.write_text(json.dumps(record))
    source = Path(result["source_path"])
    source.write_text(source.read_text().replace("scale_y_continuous(labels = fmt_value)",
                                                 'scale_y_continuous(labels = fmt_value, transform = "log10")'))
    _fill(result["source_path"], GOOD_MARKS)
    assert check_chart(result["source_path"])["ok"]


def test_long_panel_headings_wrap_to_their_panel(tmp_path: Path) -> None:
    names = ["Cereals", "Vegetable oils, oilseeds and products (oil eq.)", "Meat"]
    rows = [[str(year), name, 10.0] for name in names for year in (1970, 2000)]
    path = prepare_plot_data(str(tmp_path), "Year", ["Share"], columns=["Year", "Food", "Share"], rows=rows,
                             facet="Food")["plot_data_path"]
    result = scaffold_chart(str(tmp_path), path, {"title": "t"},
                            layout={"width_px": 1230, "height_px": 712, "dpi": 144, "facet_ncol": 3, "facet_nrow": 1},
                            colours={"ordered_palette": ["#000000"]}, x_kind="continuous")
    source = Path(result["source_path"]).read_text()
    wrap = int(re.search(r"label_wrap_gen\(width = (\d+)\)", source).group(1))
    assert 8 <= wrap < len(names[1])


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_end_labels_spread_crowded_line_names_apart(tmp_path: Path) -> None:
    # Six lines ending within a label's height of each other: their names spread apart along the
    # value axis, in order, instead of printing over each other at the last points.
    names = [f"Model {c}" for c in "ABCDEF"]
    rows = [[str(2020 + t)] + [10 + t + 0.2 * k for k in range(6)] for t in range(5)]
    path = prepare_plot_data(str(tmp_path), "Year", names, columns=["Year", *names], rows=rows)["plot_data_path"]
    result = scaffold_chart(str(tmp_path), path, {"title": "t"}, layout={"width_px": 1000, "height_px": 600, "dpi": 144},
                            colours={"ordered_palette": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00"]})
    _fill(result["source_path"], """chart_marks <- function(d) list(
  geom_line(aes(x = category, y = value, colour = series, group = series)),
  end_labels(aes(x = category, y = value, label = series, colour = series), data = d[d$category == tail(levels(d$category), 1), ])
)""")
    assert check_chart(result["source_path"])["ok"]
    bundle = render_and_inspect_chart(result["source_path"], str(tmp_path / "render"), renderer="ggplot2",
                                      dimensions=result["dimensions"])
    report = json.loads(Path(bundle["inspection_path"]).read_text())
    assert not report["text_text_collisions"]
    metadata = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    tops = {e["text"]: e["bbox"]["y"] for e in metadata["elements"] if e["text"] in names}
    assert sorted(tops, key=tops.get) == list(reversed(names))


# ---- lenient routing, interval frames, label measures, regions ----


def test_routing_words_are_read_leniently_not_refused(tmp_path: Path) -> None:
    result = _scaffold(tmp_path, identification="direct labels", x_kind="Discrete", value_encoding="length",
                       value_labels="8 labels", zero_baseline="yes", public_copy={"title": ""})
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert "limits = c(0, NA)" in source
    assert result["value_axis_hidden"]
    # Only the word it could not read, and the missing title, are reported.
    assert any("value_encoding 'length'" in w for w in result["warnings"])
    assert any("no title" in w for w in result["warnings"])
    assert not any("zero_baseline" in w or "identification" in w for w in result["warnings"])


def test_check_reports_a_hand_written_chart(tmp_path: Path) -> None:
    source = tmp_path / "chart.R"
    source.write_text("build_chart <- function() ggplot2::ggplot()\n", encoding="utf-8")
    result = check_chart(str(source))
    assert not result["ok"] and [d["code"] for d in result["deviations"]] == ["UNSCAFFOLDED_BUILD"]


SEGMENTS = [["tokens", "reads", 0, 95, 95], ["tokens", "writes", 95, 100, None],
            ["dollars", "reads", 0, 50.2, 50.2], ["dollars", "writes", 50.2, 100, 49.8]]


def _segments(tmp_path: Path, **kwargs) -> dict:
    frame = prepare_plot_data(
        str(tmp_path / "data"), x="panel", series="part", start="from", end="to",
        columns=["panel", "part", "from", "to", "printed"], rows=SEGMENTS,
        labels={"share": {"column": "printed", "suffix": "%"}},
    )
    return scaffold_chart(
        str(tmp_path), frame["plot_data_path"], {"title": "Reads are most tokens but half the cost"},
        layout={"width_px": 1200, "height_px": 600, "dpi": 144}, colours=PALETTE,
        orientation="horizontal", zero_baseline=True, **kwargs,
    )


def test_label_measure_gets_its_own_formatter(tmp_path: Path) -> None:
    result = _segments(tmp_path)
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert re.search(r'fmt_share <- scales::label_number\(accuracy = [\d.]+, big.mark = ",", prefix = "", suffix = "%"\)', source)
    assert "fmt_share(share)" in result["marks_brief"] and "start" in result["marks_brief"]
    signed = _segments(tmp_path / "signed", label_formats={"share": {"step": 1, "signed": True}})
    assert 'style_positive = "plus"' in Path(signed["source_path"]).read_text(encoding="utf-8")


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_interval_marks_are_checked_against_their_own_ends(tmp_path: Path) -> None:
    result = _segments(tmp_path)
    _fill(result["source_path"], """chart_marks <- function(d) list(
  geom_tile(aes(x = category, y = (start + end) / 2, height = end - start, fill = series), width = 0.6),
  bar_values(aes(x = category, y = end, ymin = start, ymax = end, label = fmt_share(share), fill = series), width = 0.6)
)""")
    assert check_chart(result["source_path"])["ok"]
    # Drawn at a constant instead of between its ends, the marks no longer carry the data.
    _fill(result["source_path"], """chart_marks <- function(d) list(
  geom_tile(aes(x = category, y = 1, fill = series), width = 0.6)
)""")
    assert "VALUE_NOT_ON_POSITION" in _codes(result["source_path"])


REVENUE = [["Q1'24", "Total", 70398, 14], ["Q1'24", "Search", 46156, None], ["Q1'24", "YouTube", 8090, None],
           ["Q1'25", "Total", 77264, 10], ["Q1'25", "Search", 50702, 10], ["Q1'25", "YouTube", 8927, 10]]


def _regions(tmp_path: Path, **layout_kwargs) -> dict:
    frame = prepare_plot_data(
        str(tmp_path / "data"), x="category", value="revenue", series="period",
        columns=["period", "category", "revenue", "growth"], rows=REVENUE,
        labels={"growth": {"column": "growth", "suffix": "%", "signed": True}},
    )
    layout = recommend_layout(y_slots=2, filled_marks=True, title_lines=1, panel_groups=[
        {"role": "total", "n_panels": 1, "y_slots": 1, "filled_marks": True, "categories": ["Total"]},
        {"role": "parts", "n_panels": 1, "y_slots": 2, "filled_marks": True},
    ], **layout_kwargs)
    return scaffold_chart(
        str(tmp_path), frame["plot_data_path"], {"title": "Revenue grew 10%"}, layout=layout,
        colours=PALETTE, orientation="horizontal", zero_baseline=True, value_labels=6,
    )


REGION_MARKS = """chart_marks <- function(d) {
  dodge <- position_dodge(width = 0.8)
  list(
    geom_col(aes(x = category, y = value, fill = series), position = dodge, width = 0.8),
    bar_values(aes(x = category, y = value, label = fmt_value(value), note = fmt_growth(growth), fill = series,
                   group = series), position = dodge, width = 0.8)
  )
}"""


def test_regions_draw_each_panel_group_from_its_own_rows(tmp_path: Path) -> None:
    result = _regions(tmp_path)
    boxes = result["regions"]
    assert [b["role"] for b in boxes] == ["total", "parts"]
    # The region with no category list takes every category the others did not claim.
    assert boxes[0]["categories"] == ["Total"] and boxes[1]["categories"] == ["Search", "YouTube"]
    # Stacked under the one page frame, inside the page margins, the overview the smaller band.
    assert boxes[0]["y"] + boxes[0]["height_px"] == boxes[1]["y"]
    assert boxes[0]["height_px"] < boxes[1]["height_px"]
    source = Path(result["source_path"]).read_text(encoding="utf-8")
    assert "chart_regions <- function()" in source and "patchwork::plot_annotation" in source
    # One measure across the regions: they share the value range.
    assert source.count("limits = c(0.0, 77264.0)") == 1


@pytest.mark.skipif(not R_AVAILABLE, reason="ggplot2+ragg not installed")
def test_region_page_checks_and_renders_with_notes_clear_of_values(tmp_path: Path) -> None:
    result = _regions(tmp_path)
    _fill(result["source_path"], REGION_MARKS)
    assert check_chart(result["source_path"])["ok"]
    rendered = render_and_inspect_chart(
        result["source_path"], str(tmp_path / "render"), renderer="ggplot2", dimensions=result["dimensions"],
    )
    codes = {d["code"] for d in json.loads(Path(rendered["inspection_path"]).read_text())["defects"]}
    assert not codes & {"TEXT_TEXT_COLLISION", "REDUNDANT_COLOUR", "TEXT_CLIPPED"}


def test_regions_without_categories_stay_one_grid(tmp_path: Path) -> None:
    frame = prepare_plot_data(str(tmp_path / "data"), x="category", value="revenue", series="period",
                              columns=["period", "category", "revenue", "growth"], rows=REVENUE)
    layout = recommend_layout(y_slots=2, panel_groups=[{"role": "a", "n_panels": 1}, {"role": "b", "n_panels": 1}])
    result = scaffold_chart(str(tmp_path), frame["plot_data_path"], {"title": "t"}, layout=layout, colours=PALETTE)
    assert result["regions"] == [] and any("categories" in w for w in result["warnings"])

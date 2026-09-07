"""R-first table construction from a measured plan, with a Python fallback.

The constructor (``r/table_from_plan.R``) applies the plan's measured geometry verbatim, so a
build model consumes the reservation instead of re-deriving row positions and the frame - the
failure mode where a hand-rolled table ignores measured heights and clips.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONSTRUCTOR = Path(__file__).parent / "r" / "table_from_plan.R"


def table_constructor_path() -> str:
    """Absolute path of the shared R constructor, for a build script to ``source()``."""
    return str(_CONSTRUCTOR.resolve())


def write_table_build_source(
    plan: dict[str, Any] | str | Path,
    out_path: str | Path,
    page: int = 1,
    build_function: str = "build_table",
) -> str:
    """Write an .R or .py build file that renders ``plan`` through the shared constructor.

    ``plan`` is a recommend_table_layout result (dict) or a path to its JSON. Returns the build
    file path, ready for ``render_and_inspect_chart(..., content="table", build_function=...)``.
    """
    out_path = Path(out_path)
    if isinstance(plan, dict):
        plan_path = out_path.with_suffix(".plan.json")
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
    else:
        plan_path = Path(plan)
    if page < 1:
        raise ValueError("page is 1-based and must be >= 1")
    if out_path.suffix.lower() == ".py":
        source = (
            "from dataviz_mcp.table_builder import build_table_from_plan\n"
            f"def {build_function}():\n"
            f"    return build_table_from_plan({str(plan_path.resolve())!r}, page={page})\n"
        )
    elif out_path.suffix.lower() == ".r":
        source = (
            f"source({json.dumps(table_constructor_path())})\n"
            f"{build_function} <- function() "
            f"build_table_from_plan({json.dumps(str(plan_path.resolve()))}, {int(page)}L)\n"
        )
    else:
        raise ValueError("Table build source must end in .R or .py")
    out_path.write_text(source, encoding="utf-8")
    return str(out_path)


def _plan_page(plan: dict[str, Any] | str | Path, page: int):
    if not isinstance(plan, dict):
        plan = json.loads(Path(plan).read_text(encoding="utf-8"))
    if not 1 <= page <= len(plan["pages"]):
        raise ValueError("page must identify an existing page (1-based)")
    return plan, plan["pages"][page - 1]


def build_table_from_plan(plan: dict[str, Any] | str | Path, page: int = 1):
    """Python fallback: apply measured pixel geometry without shrinking or rewrapping."""
    from matplotlib import pyplot as plt
    from matplotlib.patches import Rectangle

    plan, pg = _plan_page(plan, page)
    dpi = float(plan["dpi"])
    columns = pg["columns"]
    start, end = pg["rows"]
    widths = [float(plan["col_widths_px"][j]) for j in columns]
    width = max(sum(widths), float(pg["width_px"]))
    # Match the R constructor when a frame band sets a wider page than its columns.
    surplus = (width - sum(widths)) / len(widths)
    widths = [w + surplus for w in widths]
    bands = plan.get("frame_bands", [])
    top = [b for role in ("title", "subtitle") for b in bands if b["role"] == role]
    bottom = [b for b in bands if b["role"] == "notes"]
    heights = [float(plan["header_height_px"])] + [float(h) for h in plan["row_heights_px"][start:end]]
    height = sum(heights) + sum(float(b["height_px"]) for b in top + bottom)
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    family = plan.get("font_family", "sans")
    if family == "sans":
        family = "sans-serif"

    def cell(text, x, y, w, h, size, bold=False, left=False, role="table_cell"):
        container = Rectangle((x / width, 1 - (y + h) / height), w / width, h / height,
                              transform=fig.transFigure, facecolor="none", edgecolor="none")
        fig.add_artist(container)
        inset = float(plan["padding_x_px"]) if left else w / 2
        label = fig.text((x + inset) / width, 1 - (y + h / 2) / height, text,
                         fontsize=size, fontfamily=family, fontweight="bold" if bold else "normal",
                         color="#222222", ha="left" if left else "center", va="center",
                         multialignment="left" if left else "center")
        label.set_gid(f"{role}:cell-{len(fig.texts)}")
        # Inspection measures this rendered container, not an unverified copied plan bbox.
        label._dataviz_cell = container

    y = 0.0
    for band in top:
        cell(band["text"], 0, y, width, band["height_px"], band["font_pt"],
             band.get("bold", False), left=True, role=band["role"])
        y += band["height_px"]
    for row, h in enumerate(heights):
        x = 0.0
        for col, w in zip(columns, widths):
            text = plan["headers"][col] if row == 0 else plan["cells"][col][start + row - 1]
            cell(text, x, y, w, h, plan["header_pt"] if row == 0 else plan["body_pt"], row == 0)
            x += w
        y += h
    for band in bottom:
        cell(band["text"], 0, y, width, band["height_px"], band["font_pt"],
             band.get("bold", False), left=True, role="footer")
        y += band["height_px"]
    return fig


def render_table_from_plan(
    plan: dict[str, Any] | str | Path,
    output_dir: str,
    page: int = 1,
    artifact_name: str = "table.png",
) -> dict[str, Any]:
    """Use R when its constructor dependencies exist; otherwise use Python. Never retry a failed R build."""
    from .rendering import probe_renderers, render_and_inspect_chart

    plan, pg = _plan_page(plan, page)
    capability = probe_renderers()["table_rendering"]
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    suffix = ".R" if capability["r_available"] else ".py"
    build = write_table_build_source(plan, destination / ("table_build" + suffix), page=page)
    dimensions = {"width_px": pg["width_px"], "height_px": pg["height_px"], "dpi": plan["dpi"]}
    delivery = plan.get("delivery", {})
    dimensions.update({k: delivery[k] for k in ("display_width_px", "minimum_text_size_pt") if k in delivery})
    if "minimum_text_px" in delivery:
        dimensions["minimum_text_size_px"] = delivery["minimum_text_px"]
    return render_and_inspect_chart(build, output_dir, dimensions=dimensions,
                                    artifact_name=artifact_name, build_function="build_table", content="table")

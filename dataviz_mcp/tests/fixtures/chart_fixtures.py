from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def _base():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    fig.subplots_adjust(left=0.10, right=0.92, top=0.84, bottom=0.16)
    x = np.arange(10)
    y = np.array([2.0, 2.5, 3.1, 3.6, 4.2, 4.8, 5.3, 5.9, 6.5, 7.0])
    (line,) = ax.plot(x, y, color="#245b78", linewidth=2)
    line.set_gid("series:main")
    ax.set(xlim=(0, 9), ylim=(0, 9), title="Deterministic geometry fixture")
    ax.spines[["top", "right"]].set_visible(False)
    return fig, ax, x, y


def _annotation(ax, identifier, text, xy, xytext, **kwargs):
    annotation = ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        textcoords="offset points",
        ha=kwargs.pop("ha", "center"),
        va=kwargs.pop("va", "center"),
        fontsize=11,
        annotation_clip=False,
        **kwargs,
    )
    annotation.set_gid(f"annotation:{identifier}")
    return annotation


def annotation_over_line():
    fig, ax, x, y = _base()
    _annotation(ax, "on-line", "Label on line", (x[5], y[5]), (0, 0))
    return fig, {"fixture": "annotation_over_line"}


def two_annotations_overlap():
    fig, ax, x, y = _base()
    _annotation(ax, "first", "First annotation", (x[4], y[4]), (30, 30))
    _annotation(ax, "second", "Second annotation", (x[4], y[4]), (30, 30))
    return fig, {"fixture": "two_annotations_overlap"}


def annotation_outside_canvas():
    fig, ax, x, y = _base()
    _annotation(ax, "outside", "Outside", (x[-1], y[-1]), (180, 0), ha="left")
    return fig, {"fixture": "annotation_outside_canvas"}


def clipped_annotation():
    fig, ax, x, y = _base()
    annotation = _annotation(
        ax,
        "clipped",
        "Clipped at plot edge",
        (x[-1], y[-1]),
        (5, 0),
        ha="left",
    )
    annotation.set_clip_on(True)
    return fig, {"fixture": "clipped_annotation"}


def long_unwrapped_annotation():
    fig, ax, x, y = _base()
    _annotation(
        ax,
        "long",
        "This annotation is deliberately far too long to remain on one unwrapped line",
        (x[3], y[3]),
        (80, 90),
    )
    return fig, {"fixture": "long_unwrapped_annotation"}


def clean_chart():
    fig, ax, x, y = _base()
    _annotation(ax, "clean", "Clear label", (x[4], y[4]), (0, 55))
    return fig, {"fixture": "clean_chart"}


def line_with_gap():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    fig.subplots_adjust(left=0.10, right=0.92, top=0.84, bottom=0.16)
    (line,) = ax.plot([0, 1, 2, 3, 4], [2, 3, np.nan, 5, 6], linewidth=2)
    line.set_gid("series:gapped")
    ax.set(xlim=(0, 4), ylim=(0, 8), title="Missing values break the path")
    _annotation(ax, "in-gap", "Gap label", (2, 4), (0, 0))
    return fig, {"fixture": "line_with_gap"}


def unsupported_bar_marks():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    ax.bar([1, 2, 3], [2, 4, 3])
    ax.set_title("Bar geometry is not yet captured")
    return fig, {"fixture": "unsupported_bar_marks"}


def title_subtitle_collision():
    fig, ax, x, y = _base()
    title = fig.suptitle("A title that occupies the hierarchy zone", y=0.95, fontsize=16)
    title.set_gid("title:main")
    subtitle = fig.text(
        0.5,
        0.95,
        "A subtitle placed on the same baseline",
        ha="center",
        va="center",
        fontsize=12,
    )
    subtitle.set_gid("subtitle:main")
    return fig, {"fixture": "title_subtitle_collision"}


def low_contrast_annotation():
    fig, ax, x, y = _base()
    _annotation(ax, "faint", "Faint label", (x[4], y[4]), (0, 55), color="#b8b8b8")
    return fig, {"fixture": "low_contrast_annotation"}


def label_over_bar():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    bars = ax.bar([1, 2, 3], [2, 4, 3], color="#245b78")
    bars[1].set_gid("mark:middle-bar")
    label = ax.text(2, 2, "Accidental overlap", ha="center", va="center")
    label.set_gid("label:bar-label")
    return fig, {"fixture": "label_over_bar"}


def incomplete_direct_labels():
    fig, ax, x, y = _base()
    for index in (2, 7):
        label = ax.text(x[index], y[index] + 0.4, f"Series {index}")
        label.set_gid(f"label:series-{index}")
    return fig, {
        "fixture": "incomplete_direct_labels",
        "inspection_contract": {
            "direct_labels": [
                {"axes_id": "axes-1", "role": "label", "expected_count": 3}
            ]
        },
    }


def all_marks_labelled():
    fig, ax, x, y = _base()
    for index in range(len(x)):
        label = ax.text(x[index], y[index] + 0.3, f"{y[index]:.1f}", fontsize=8)
        label.set_gid(f"label:point-{index}")
    return fig, {
        "fixture": "all_marks_labelled",
        "inspection_contract": {
            "direct_labels": [
                {"axes_id": None, "role": "label", "expected_count": len(x)}
            ]
        },
    }


def faceted_bars_all_labelled():
    # Two panels, every bar directly labelled with its value and a numeric y axis on each panel,
    # but NO inspection_contract - the geometry fallback must still flag the redundant value axis
    # per panel.
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.5), dpi=100)
    heights = ([2, 4, 3], [5, 1, 4])
    for panel, (ax, hs) in enumerate(zip(axes, heights)):
        bars = ax.bar(["A", "B", "C"], hs, color="#245b78")
        for index, (bar, value) in enumerate(zip(bars, hs)):
            bar.set_gid(f"mark:p{panel}-bar{index}")
            label = ax.text(bar.get_x() + bar.get_width() / 2, value + 0.2, f"{value}", fontsize=8)
            label.set_gid(f"label:p{panel}-bar{index}")
    return fig, {"fixture": "faceted_bars_all_labelled"}


def coloured_facets_with_legend():
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.5), dpi=100)
    x = np.arange(10)
    (north,) = axes[0].plot(x, x, color="#245b78", linewidth=2, label="North")
    north.set_gid("series:north")
    (south,) = axes[1].plot(x, x[::-1], color="#c8102e", linewidth=2, label="South")
    south.set_gid("series:south")
    axes[0].set_title("North")
    axes[1].set_title("South")
    axes[0].legend()
    return fig, {"fixture": "coloured_facets_with_legend"}


def rainbow_bars_with_legend():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    categories = ["A", "B", "C"]
    bars = ax.bar(categories, [2, 4, 3], color=["#245b78", "#c8102e", "#e0a458"])
    ax.legend(bars, categories)
    return fig, {"fixture": "rainbow_bars_with_legend"}


def focal_bar_highlight():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    categories = ["A", "B", "C", "D"]
    grey = "#c9ccce"
    ax.bar(categories, [2, 3, 5, 1], color=[grey, grey, "#245b78", grey])
    return fig, {"fixture": "focal_bar_highlight"}


COFFEE_YEARS = np.arange(2016, 2026)
COFFEE_PRICES = np.array([1.45, 1.38, 1.24, 1.12, 1.28, 2.31, 2.27, 1.89, 2.72, 3.05])


def _coffee_base():
    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=120)
    fig.subplots_adjust(left=0.09, right=0.96, top=0.82, bottom=0.16)
    (line,) = ax.plot(
        COFFEE_YEARS,
        COFFEE_PRICES,
        color="#2f6b4f",
        linewidth=2.5,
        marker="o",
        markersize=4,
    )
    line.set_gid("series:global-coffee-price")
    ax.set(
        xlim=(2015.7, 2025.3),
        ylim=(0.8, 3.5),
        title="Coffee prices rose sharply after 2020",
        ylabel="Illustrative price index",
    )
    ax.set_xticks(COFFEE_YEARS)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.7)
    return fig, ax


def coffee_bad():
    fig, ax = _coffee_base()
    for identifier, label, year in (
        ("brazil-drought", "Brazil drought", 2021),
        ("shipping", "Shipping disruption", 2022),
        ("vietnam-heat", "Vietnam heat", 2024),
    ):
        price = float(COFFEE_PRICES[np.where(COFFEE_YEARS == year)][0])
        _annotation(ax, identifier, label, (year, price), (0, 0))
    return fig, {"fixture": "coffee_bad", "repair_scope": "annotation placement only"}


def coffee_fixed():
    fig, ax = _coffee_base()
    placements = (
        ("brazil-drought", "Brazil drought", 2021, (-55, 50), "right"),
        ("shipping", "Shipping disruption", 2022, (28, -48), "left"),
        ("vietnam-heat", "Vietnam heat", 2024, (-10, 54), "center"),
    )
    for identifier, label, year, offset, alignment in placements:
        price = float(COFFEE_PRICES[np.where(COFFEE_YEARS == year)][0])
        _annotation(ax, identifier, label, (year, price), offset, ha=alignment)
    return fig, {"fixture": "coffee_fixed", "repair_scope": "annotation placement only"}

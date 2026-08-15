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

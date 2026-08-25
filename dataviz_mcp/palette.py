"""Colour selection and validation for charts (and colour-formatted tables).

Two responsibilities:
  * ``recommend_colours`` - pick and assign colours for a specific graph from an
    available set (brand palette, colours from the prompt/context, or defaults),
    maximising contrast + distinctness. Even when colours are given, a specific
    chart still needs a decision on which to use and how to assign them.
  * ``validate_palette`` - score a proposed/assigned palette against WCAG contrast,
    adjacent-series distinctness, colour-vision-deficiency (CVD), and grayscale.

Targets are soft: findings are reported, not hard-blocked. WCAG is a diagnostic.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from .color_math import (
    contrast_ratio_rgb,
    grayscale_value,
    hue_delta,
    hue_lightness,
    lightness_delta,
    simulate_cvd,
    _contrast_ratio,
)

# Colour-blind-safe fallback when no brand or context colours are supplied (Okabe-Ito).
OKABE_ITO = [
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
    "#000000",
]

_CVD_KINDS = ("deuteranope", "protanope", "tritanope")


def _separation(first: str, second: str) -> float:
    """Perceptual separation scalar (~0 = confusable). Lightness-weighted because
    hue collapses under CVD and grayscale; lightness survives both."""
    d_light = lightness_delta(first, second)
    d_hue = hue_delta(first, second)
    if d_light is None or d_hue is None:
        return 0.0
    return d_light + 0.4 * (d_hue / 180.0)


def _pair_report(first: str, second: str) -> dict[str, Any]:
    hl_a, hl_b = hue_lightness(first), hue_lightness(second)
    ratio = _contrast_ratio(first, second)
    return {
        "contrast_ratio": round(ratio, 3) if ratio is not None else None,
        "hue_delta_deg": round(hue_delta(first, second) or 0.0, 1),
        "lightness_delta": round(lightness_delta(first, second) or 0.0, 3),
        "separation": round(_separation(first, second), 3),
        "_hl": (hl_a, hl_b),
    }


def _nudge(report: dict[str, Any]) -> str:
    if report["lightness_delta"] < report["hue_delta_deg"] / 180.0:
        return "increase the lightness difference (lighten one, darken the other)"
    return "shift one hue further away, or add a lightness difference"


def validate_palette(
    colours: Sequence[str],
    background: str = "#FFFFFF",
    text_colours: Optional[Sequence[str]] = None,
    min_contrast_text: float = 4.5,
    min_contrast_mark: float = 3.0,
    min_separation: float = 0.18,
    min_gray_delta: float = 20.0,
) -> dict[str, Any]:
    """Score a palette. Returns a verdict plus ranked findings, each with a nudge."""
    findings: list[dict[str, Any]] = []

    # 1. Marks vs background.
    for colour in colours:
        ratio = _contrast_ratio(colour, background)
        if ratio is None:
            findings.append({"rule": "parse", "colours": [colour], "detail": "unparseable colour"})
        elif ratio < min_contrast_mark:
            findings.append(
                {
                    "rule": "mark_vs_background",
                    "colours": [colour],
                    "contrast_ratio": round(ratio, 3),
                    "target": min_contrast_mark,
                    "nudge": "darken or lighten this colour away from the background",
                }
            )

    # 1b. Text vs background (optional).
    for colour in text_colours or []:
        ratio = _contrast_ratio(colour, background)
        if ratio is not None and ratio < min_contrast_text:
            findings.append(
                {
                    "rule": "text_vs_background",
                    "colours": [colour],
                    "contrast_ratio": round(ratio, 3),
                    "target": min_contrast_text,
                    "nudge": "use a darker/lighter text colour",
                }
            )

    # 2. Adjacent-series distinctness (normal vision).
    for i in range(len(colours)):
        for j in range(i + 1, len(colours)):
            report = _pair_report(colours[i], colours[j])
            report.pop("_hl", None)
            if report["separation"] < min_separation:
                findings.append(
                    {
                        "rule": "series_distinctness",
                        "colours": [colours[i], colours[j]],
                        **report,
                        "nudge": _nudge(report),
                    }
                )

    # 3. CVD simulation.
    for kind in _CVD_KINDS:
        simulated = {c: simulate_cvd(c, kind) for c in colours}
        for i in range(len(colours)):
            for j in range(i + 1, len(colours)):
                a, b = simulated[colours[i]], simulated[colours[j]]
                if a is None or b is None:
                    continue
                ratio = contrast_ratio_rgb(a, b)
                euclid = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
                if ratio < 1.15 and euclid < 40:
                    findings.append(
                        {
                            "rule": f"cvd_{kind}",
                            "colours": [colours[i], colours[j]],
                            "cvd_contrast": round(ratio, 3),
                            "cvd_rgb_distance": round(euclid, 1),
                            "nudge": "separate this pair on lightness so it survives colour blindness",
                        }
                    )

    # 4. Grayscale.
    grays = {c: grayscale_value(c) for c in colours}
    for i in range(len(colours)):
        for j in range(i + 1, len(colours)):
            a, b = grays[colours[i]], grays[colours[j]]
            if a is None or b is None:
                continue
            if abs(a - b) < min_gray_delta:
                findings.append(
                    {
                        "rule": "grayscale",
                        "colours": [colours[i], colours[j]],
                        "gray_delta": round(abs(a - b), 1),
                        "target": min_gray_delta,
                        "nudge": "add a lightness difference so the pair separates in grayscale",
                    }
                )

    verdict = "pass" if not findings else "soft_fail"
    return {
        "verdict": verdict,
        "n_colours": len(colours),
        "background": background,
        "findings": findings,
    }


def recommend_colours(
    available: Optional[Sequence[str]],
    n_series: int,
    background: str = "#FFFFFF",
    focal: Optional[str] = None,
    series: Optional[Sequence[str]] = None,
    current_assignment: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Pick and assign `n_series` colours for one graph from the `available` set.

    `n_series` is the palette size - the maximum number of series that share a single
    panel (so small multiples with k lines per panel pass k, not the total category
    count). The returned palette is **ordered and prefix-nested**: it is built by
    farthest-first traversal, so the first m colours are themselves a good m-colour
    palette. A panel that needs fewer series than the maximum uses the first that many
    colours, and the assignment stays consistent across panels.

    Chooses greedily to maximise the minimum pairwise separation while keeping every
    colour readable against the background. If `focal` is given it is pinned to the first
    series (focal-colour-plus-grey lives in the skill; here focal just anchors the
    assignment). If the available set cannot supply `n_series` usable colours, the
    shortfall and suggested additions are reported.

    The recommender is **identity-aware** when the caller names its categories. Pass
    `series` (category names, one per assignment slot) to label the output; the count-only
    path is unchanged when it is omitted. Pass `current_assignment` (category -> existing
    colour) to anchor identity: categories whose existing colour already reads well and
    stays distinct from the rest are kept verbatim, so a caller can be the single source
    of truth *and* preserve the prior category->colour mapping. Only colours that fail
    contrast or collide with another category are moved, and every move is disclosed in
    `remapped` (with the reason) so a downstream check can tell a preserved identity from
    a deliberate improvement. `preserved` is True when nothing moved.
    """
    if current_assignment:
        return _recommend_preserving(
            available, n_series, background, focal, series, current_assignment
        )

    pool = list(available) if available else list(OKABE_ITO)
    # Keep only colours that read against the background; remember what was dropped.
    usable, dropped = [], []
    for colour in pool:
        ratio = _contrast_ratio(colour, background)
        if ratio is not None and ratio >= 3.0:
            if colour not in usable:
                usable.append(colour)
        else:
            dropped.append(colour)

    chosen: list[str] = []
    if focal and _contrast_ratio(focal, background):
        chosen.append(focal)
        usable = [c for c in usable if c != focal]

    while len(chosen) < n_series and usable:
        if not chosen:
            # Seed with the highest-background-contrast colour.
            best = max(usable, key=lambda c: _contrast_ratio(c, background) or 0.0)
        else:
            best = max(usable, key=lambda c: min(_separation(c, picked) for picked in chosen))
        chosen.append(best)
        usable = [c for c in usable if c != best]

    shortfall = n_series - len(chosen)
    suggestions: list[str] = []
    if shortfall > 0:
        # Top up from Okabe-Ito colours not already chosen and readable on the background.
        for colour in OKABE_ITO:
            if len(suggestions) >= shortfall:
                break
            if colour in chosen:
                continue
            ratio = _contrast_ratio(colour, background)
            if ratio is not None and ratio >= 3.0:
                suggestions.append(colour)

    assignment = [
        {
            "series_index": index,
            **({"series": series[index]} if series and index < len(series) else {}),
            "colour": colour,
        }
        for index, colour in enumerate(chosen)
    ]
    validation = validate_palette(chosen, background=background) if chosen else {"verdict": "pass", "findings": []}

    rationale_parts = [
        f"Chose {len(chosen)} of {n_series} colours from "
        f"{'the supplied set' if available else 'the Okabe-Ito default'} by max-min separation on a {background} background."
    ]
    if focal:
        rationale_parts.append(f"Pinned focal {focal} to series 0.")
    if dropped:
        rationale_parts.append(f"Dropped {len(dropped)} low-contrast colour(s): {', '.join(dropped)}.")
    if shortfall > 0:
        rationale_parts.append(
            f"Available set is {shortfall} short for {n_series} series; "
            f"add/substitute: {', '.join(suggestions) or 'nudge existing colours apart'}."
        )

    return {
        "assignment": assignment,
        "ordered_palette": chosen,
        "chosen": chosen,
        "prefix_nested": True,
        "preserved": False,
        "remapped": [],
        "n_series": n_series,
        "shortfall": shortfall,
        "suggested_additions": suggestions,
        "dropped_low_contrast": dropped,
        "validation": validation,
        "rationale": " ".join(rationale_parts)
        + " Palette is ordered and prefix-nested: a panel with fewer series uses the first that many colours.",
    }


def _recommend_preserving(
    available: Optional[Sequence[str]],
    n_series: int,
    background: str,
    focal: Optional[str],
    series: Optional[Sequence[str]],
    current_assignment: dict[str, str],
) -> dict[str, Any]:
    """Identity-anchored assignment: keep each category on its existing colour unless that
    colour fails contrast or collides with another category, moving only the losers."""
    categories = list(series) if series else list(current_assignment.keys())
    current = {cat: current_assignment.get(cat) for cat in categories}

    # A category is a "loser" (must move) if its colour is unreadable on the background, or
    # if it is the lower-background-contrast member of a confusable pair. Preserve the rest.
    def bg_contrast(colour: Optional[str]) -> float:
        ratio = _contrast_ratio(colour, background) if colour else None
        return ratio if ratio is not None else 0.0

    losers: list[str] = []
    reasons: dict[str, str] = {}
    for cat in categories:
        colour = current[cat]
        if colour is None or bg_contrast(colour) < 3.0:
            if cat not in losers:
                losers.append(cat)
                reasons[cat] = "existing colour is missing or too low-contrast on the background"

    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            a, b = categories[i], categories[j]
            ca, cb = current[a], current[b]
            if ca is None or cb is None:
                continue
            if _separation(ca, cb) < 0.18:
                # Move the lower-background-contrast member; keep the more legible one put.
                loser, keeper = (a, b) if bg_contrast(ca) <= bg_contrast(cb) else (b, a)
                if loser not in losers and keeper not in losers:
                    losers.append(loser)
                    reasons[loser] = f"confusable with '{keeper}' ({current[loser]} vs {current[keeper]})"

    kept = {cat: current[cat] for cat in categories if cat not in losers}
    # Replacement pool: supplied set (or Okabe-Ito), readable, not already held by a kept category.
    held = set(kept.values())
    pool, dropped = [], []
    for colour in (list(available) if available else list(OKABE_ITO)):
        if bg_contrast(colour) >= 3.0:
            if colour not in pool and colour not in held:
                pool.append(colour)
        else:
            dropped.append(colour)

    remapped: list[dict[str, Any]] = []
    shortfall = 0
    for cat in categories:
        if cat not in losers:
            continue
        anchors = list(kept.values()) + [entry["to"] for entry in remapped]
        candidates = [c for c in pool if c not in anchors]
        if not candidates:
            shortfall += 1
            kept[cat] = current[cat]  # nothing usable left; keep the flawed colour, flagged by shortfall
            continue
        replacement = (
            max(candidates, key=lambda c: min((_separation(c, a) for a in anchors), default=bg_contrast(c)))
            if anchors
            else max(candidates, key=bg_contrast)
        )
        remapped.append({"series": cat, "from": current[cat], "to": replacement, "reason": reasons[cat]})
        kept[cat] = replacement

    final = [kept[cat] for cat in categories]
    assignment = [
        {"series_index": index, "series": cat, "colour": kept[cat]}
        for index, cat in enumerate(categories)
    ]
    validation = validate_palette(final, background=background) if final else {"verdict": "pass", "findings": []}

    rationale_parts = [
        f"Anchored {len(categories)} categories to their existing colours; "
        f"kept {len(categories) - len(remapped)} verbatim."
    ]
    if remapped:
        rationale_parts.append(
            "Remapped "
            + ", ".join(f"'{e['series']}' {e['from']}->{e['to']}" for e in remapped)
            + " (disclosed for identity checks)."
        )
    else:
        rationale_parts.append("Prior category->colour mapping preserved exactly.")
    if shortfall:
        rationale_parts.append(f"{shortfall} category(ies) had no usable replacement; flawed colour kept.")

    return {
        "assignment": assignment,
        "ordered_palette": final,
        "chosen": final,
        "prefix_nested": False,
        "preserved": not remapped,
        "remapped": remapped,
        "n_series": n_series,
        "shortfall": shortfall,
        "suggested_additions": [],
        "dropped_low_contrast": dropped,
        "validation": validation,
        "rationale": " ".join(rationale_parts),
    }


def extract_palette_from_image(
    image_path: str,
    max_colours: int = 8,
    ignore_near_white_black: bool = True,
) -> dict[str, Any]:
    """Sample dominant hues from a source chart image as a repair *prior*.

    Downsamples, quantises, drops the background and near-neutral ink, and returns
    the dominant colours ranked by pixel share as hex strings.
    """
    from PIL import Image

    try:
        image = Image.open(image_path).convert("RGB")
    except (FileNotFoundError, OSError) as exc:
        return {"error": f"could not open image: {exc}", "colours": []}

    image.thumbnail((240, 240))
    quantised = image.quantize(colors=max(max_colours * 4, 16))
    palette = quantised.getpalette() or []
    counts = quantised.getcolors() or []
    total = sum(count for count, _ in counts) or 1

    ranked = []
    for count, index in sorted(counts, key=lambda item: item[0], reverse=True):
        red, green, blue = palette[index * 3 : index * 3 + 3]
        if ignore_near_white_black and _is_near_neutral(red, green, blue):
            continue
        ranked.append(
            {
                "hex": f"#{red:02X}{green:02X}{blue:02X}",
                "share": round(count / total, 4),
            }
        )
        if len(ranked) >= max_colours:
            break

    return {
        "image_path": image_path,
        "colours": [entry["hex"] for entry in ranked],
        "detail": ranked,
        "note": "Dominant source hues - use as a prior; brand and accessibility may override.",
    }


def _is_near_neutral(red: int, green: int, blue: int) -> bool:
    """Near-white, near-black, or low-saturation grey (background / ink, not a series hue)."""
    if max(red, green, blue) > 235 and min(red, green, blue) > 235:
        return True
    if max(red, green, blue) < 30:
        return True
    return (max(red, green, blue) - min(red, green, blue)) < 18

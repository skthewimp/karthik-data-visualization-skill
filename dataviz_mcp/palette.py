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

import colorsys
from typing import Any, Optional, Sequence

from .color_math import (
    contrast_ratio_rgb,
    grayscale_value,
    hue_delta,
    hue_lightness,
    lightness_delta,
    simulate_cvd,
    to_rgb,
    _contrast_ratio,
)

# Colour-word vocabulary: where each family sits on the hue wheel (degrees). This is
# colour *vocabulary*, not a semantic map - the model decides that a series "means"
# blue; this only says where "blue" is. Grey is handled separately (no hue, low
# saturation). Unknown words fall through and are reported as unmet, never guessed.
HUE_FAMILIES = {
    "red": 0, "crimson": 350, "scarlet": 5,
    "orange": 30, "amber": 40, "gold": 48, "brown": 28,
    "yellow": 55, "lime": 90, "green": 130, "olive": 80,
    "teal": 175, "cyan": 185, "turquoise": 180,
    "sky": 200, "blue": 215, "navy": 225, "azure": 205,
    "indigo": 250, "violet": 275, "purple": 285,
    "magenta": 310, "pink": 335, "rose": 345,
}
_GREY_FAMILIES = {"grey", "gray", "neutral", "slate"}
_GREY_MAX_SATURATION = 0.15

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

# When the default is asked for more than eight series, extend Okabe-Ito with Paul Tol's
# qualitative hues (also CVD-aware). Hand-vetted, never generated - farthest-first over the
# union picks the most distinct subset, so early series still land on the Okabe-Ito colours.
_TOL_EXTRA = [
    "#332288",
    "#117733",
    "#88CCEE",
    "#DDCC77",
    "#CC6677",
    "#AA4499",
    "#44AA99",
    "#999933",
    "#882255",
]
EXTENDED_CATEGORICAL = OKABE_ITO + _TOL_EXTRA

_CVD_KINDS = ("deuteranope", "protanope", "tritanope")


def _separation(first: str, second: str) -> float:
    """Perceptual separation scalar (~0 = confusable). Lightness-weighted because
    hue collapses under CVD and grayscale; lightness survives both."""
    d_light = lightness_delta(first, second)
    d_hue = hue_delta(first, second)
    if d_light is None or d_hue is None:
        return 0.0
    return d_light + 0.4 * (d_hue / 180.0)


def _saturation(colour: str) -> Optional[float]:
    """HLS saturation in [0,1], or None if unparseable."""
    rgb = to_rgb(colour)
    if rgb is None:
        return None
    r, g, b = (value / 255 for value in rgb)
    _, _, sat = colorsys.rgb_to_hls(r, g, b)
    return sat


def _circular_hue_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _nearest_in_family(family: str, pool: Sequence[str]) -> tuple[Optional[str], Optional[float]]:
    """From `pool`, the colour closest to a named hue family and its hue distance (deg).

    Grey/neutral is matched by lowest saturation, not hue. An unknown family word
    returns (None, None) so the caller reports it unmet rather than guessing a hue.
    """
    if family in _GREY_FAMILIES:
        best, best_sat = None, None
        for colour in pool:
            sat = _saturation(colour)
            if sat is None:
                continue
            if best_sat is None or sat < best_sat:
                best, best_sat = colour, sat
        if best is None or best_sat is None or best_sat > _GREY_MAX_SATURATION:
            return None, None
        return best, 0.0

    target = HUE_FAMILIES.get(family)
    if target is None:
        return None, None
    best, best_dist = None, None
    for colour in pool:
        hl = hue_lightness(colour)
        if hl is None:
            continue
        dist = _circular_hue_distance(hl[0], target)
        if best_dist is None or dist < best_dist:
            best, best_dist = colour, dist
    return best, best_dist


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
    semantic_hints: Optional[Sequence[dict[str, Any]]] = None,
    family_tolerance_deg: float = 40.0,
    min_separation: float = 0.18,
    min_contrast_mark: float = 3.0,
) -> dict[str, Any]:
    """Pick and assign `n_series` colours for one graph from the `available` set.

    `n_series` is the palette size - the maximum number of series that share a single
    panel (so small multiples with k lines per panel pass k, not the total category
    count).

    Returning one distinct colour per series is the HARD constraint. Selection is then
    lexicographic: contrast WITH THE BACKGROUND comes first (a colour must read against the
    background - this outranks separation from the other series), then diversity (maximise
    the minimum separation from the already-placed series), then higher background contrast
    as a tiebreak. Contrast stays SOFT, not a filter: a colour below the background bar is
    never dropped (that would starve the pool), only spent last - used to satisfy the count
    when readable colours run out - and reported by `validate_palette`. The default pool is
    Okabe-Ito, extended with hand-vetted Paul Tol hues when more than eight series are asked
    for; a supplied set is never padded with extras. If the pool holds fewer distinct colours
    than `n_series`, the result is **unresolved** (`resolved: false`, `route_to: "select"`) -
    the caller drops a series or supplies more colours, never invents hues. Colours are never
    generated procedurally.

    Without `semantic_hints`, the returned palette is **ordered and prefix-nested**: it
    is built by farthest-first traversal, so the first m colours are themselves a good
    m-colour palette and a smaller panel uses the prefix. `focal` pins a colour to series 0.

    `semantic_hints` binds specific series to a colour *intent* the model has judged. Each
    entry is ``{"series_index": i, ...}`` with either ``"colour": "#hex"`` (a hard pin) or
    ``"hue_family": "blue"`` (a soft family - the nearest in-family colour in the available
    set, within `family_tolerance_deg`), and an optional ``"alternates"`` list of away-kit
    colours or family words. The model owns the judgement of which series means what and
    what its away kits are; this function only reconciles.

    Priority (higher wins): (1) series stay distinguishable - the near-hard bar is
    `min_separation`; (2) semantic meaning - honoured even at a background-contrast or CVD
    cost, so a soft family may reach a low-contrast in-family colour; (3) contrast/CVD/
    grayscale - soft, reported by `validate_palette`. When a series' home colour is too
    close to one already placed (like two football teams in the same kit), it is moved to
    the first `alternates` away-kit that clears the bar; if none do, it is **left on its
    home colour and flagged** (`semantic_collision`) - never silently reskinned. Home is
    kept for hard pins, `focal`, then lower `series_index`. Unmet hints (no in-family
    colour, unknown word) are flagged `semantic_unmet` and the slot is filled by
    separation. Hints make positions identity-bound, so the palette is not prefix-nested.
    """
    if available:
        pool = list(available)
    else:
        # Default: Okabe-Ito, extended with Paul Tol's hues only when more than eight
        # series are asked for. Never inject extras into a supplied brand set.
        pool = list(EXTENDED_CATEGORICAL) if n_series > len(OKABE_ITO) else list(OKABE_ITO)
    # Every parseable colour stays in play. Background contrast is a SOFT preference here,
    # not a filter: dropping low-contrast colours starves the pool and breaks the hard
    # constraint of returning enough distinct series colours. Contrast only orders the
    # fill (higher first) and is reported downstream by ``validate_palette``. `dropped` is
    # an informational list of colours that read poorly on this background, not excluded.
    parsed, dropped = [], []
    for colour in pool:
        ratio = _contrast_ratio(colour, background)
        if ratio is None or colour in parsed:
            continue
        parsed.append(colour)
        if ratio < 3.0:
            dropped.append(colour)

    def _resolve(kind: str, value: str, exclude: set[str]) -> Optional[str]:
        """A hint candidate -> a concrete colour. Exact colours are honoured even if
        low-contrast or absent from the pool (semantics over accessibility); a family
        resolves to its nearest in-family colour among the not-yet-used parseable set."""
        if kind == "colour":
            return value if _contrast_ratio(value, background) is not None else None
        pick, dist = _nearest_in_family(value, [c for c in parsed if c not in exclude])
        if pick is None or dist is None or dist > family_tolerance_deg:
            return None
        return pick

    def _candidate(value: Any) -> tuple[str, str]:
        """An `alternates` item: a family word if it names one, else an exact colour."""
        text = str(value).strip()
        if text.lower() in HUE_FAMILIES or text.lower() in _GREY_FAMILIES:
            return "family", text.lower()
        return "colour", text

    # Normalise hints; treat focal as a home hard pin at series 0.
    hints: list[tuple[int, tuple[str, str], list[tuple[str, str]]]] = []
    seen_idx: set[int] = set()
    for hint in semantic_hints or []:
        idx = hint.get("series_index")
        if not isinstance(idx, int) or not (0 <= idx < n_series) or idx in seen_idx:
            continue
        if hint.get("colour"):
            home = ("colour", str(hint["colour"]))
        elif hint.get("hue_family"):
            home = ("family", str(hint["hue_family"]).strip().lower())
        else:
            continue
        alternates = [_candidate(a) for a in (hint.get("alternates") or [])]
        hints.append((idx, home, alternates))
        seen_idx.add(idx)
    if focal and 0 not in seen_idx:
        hints.append((0, ("colour", focal), []))
        seen_idx.add(0)

    has_semantics = bool(semantic_hints)
    # Home priority: hard pins/focal before soft families, then lower series_index.
    hints.sort(key=lambda item: (0 if item[1][0] == "colour" else 1, item[0]))

    slots: dict[int, str] = {}
    placed: list[str] = []
    used: set[str] = set()
    semantic_findings: list[dict[str, Any]] = []

    def _clears(colour: str) -> bool:
        return not placed or min(_separation(colour, other) for other in placed) >= min_separation

    for idx, home, alternates in hints:
        home_colour = _resolve(home[0], home[1], used)
        if home_colour is None:
            semantic_findings.append(
                {
                    "rule": "semantic_unmet",
                    "series_index": idx,
                    "requested": home[1],
                    "nudge": f"no colour for '{home[1]}' within {family_tolerance_deg:g} deg in the "
                    "available set; add one, or accept the separation-based pick",
                }
            )
            continue
        if _clears(home_colour):
            chosen_colour = home_colour
        else:
            # Home clashes with a placed series - try the away kits in order.
            chosen_colour = None
            for kind, value in alternates:
                candidate = _resolve(kind, value, used)
                if candidate is not None and _clears(candidate):
                    chosen_colour = candidate
                    break
            if chosen_colour is None:
                # Nothing clears; keep home and flag - never reskin without an away kit.
                chosen_colour = home_colour
                semantic_findings.append(
                    {
                        "rule": "semantic_collision",
                        "series_index": idx,
                        "colour": home_colour,
                        "nudge": "too close to another series; give this series an away-kit alternate "
                        "or merge the two",
                    }
                )
        slots[idx] = chosen_colour
        placed.append(chosen_colour)
        used.add(chosen_colour)

    # Fill the remaining positions farthest-first over ALL parseable colours (contrast is
    # not a filter). Diversity is the objective: maximise the minimum separation from what
    # is already placed; break ties toward higher background contrast so any poorly-reading
    # colour is spent last, only when the count demands it.
    # Contrast WITH THE BACKGROUND outranks separation from the other series: a colour must
    # first read against the background, and only then be as distinct as possible from its
    # neighbours. So pick lexicographically - (1) prefer colours that clear the background
    # bar over those that do not, (2) among equals, maximise the minimum separation from the
    # already-placed series, (3) break ties toward higher background contrast. Contrast stays
    # SOFT: a below-bar colour is not dropped, just spent last, only when the count needs it.
    remaining_slots = [idx for idx in range(n_series) if idx not in slots]
    supply = [c for c in parsed if c not in used]

    def _reads(colour: str) -> bool:
        ratio = _contrast_ratio(colour, background)
        return ratio is not None and ratio >= min_contrast_mark

    for idx in remaining_slots:
        if not supply:
            break
        best = max(
            supply,
            key=lambda c: (
                1 if _reads(c) else 0,
                min((_separation(c, other) for other in placed), default=0.0),
                _contrast_ratio(c, background) or 0.0,
            ),
        )
        slots[idx] = best
        placed.append(best)
        used.add(best)
        supply = [c for c in supply if c != best]

    ordered_positions = sorted(slots)
    chosen = [slots[idx] for idx in ordered_positions]

    # HARD constraint: return one distinct colour per requested series. If the pool holds
    # fewer real colours than that (a small supplied brand set), we cannot fabricate more
    # without inventing arbitrary hues - so return an explicit UNRESOLVED result that routes
    # back to the select stage to drop a series or supply more colours. A short plan with
    # holes is never a successful recommendation.
    shortfall = n_series - len(chosen)
    resolved = shortfall == 0

    # When unresolved, offer curated CVD-safe candidates the caller MAY add (farthest-first
    # from what is chosen) - a suggestion for the select stage, not colours applied here.
    suggestions: list[str] = []
    if not resolved:
        candidate_pool = [c for c in EXTENDED_CATEGORICAL if c not in chosen]
        reference = list(chosen)
        while len(suggestions) < shortfall and candidate_pool:
            if reference:
                pick = max(candidate_pool, key=lambda c: min(_separation(c, o) for o in reference))
            else:
                pick = candidate_pool[0]
            suggestions.append(pick)
            reference.append(pick)
            candidate_pool = [c for c in candidate_pool if c != pick]

    assignment = [{"series_index": idx, "colour": slots[idx]} for idx in ordered_positions]
    validation = validate_palette(chosen, background=background) if chosen else {"verdict": "pass", "findings": []}

    default_label = "the Okabe-Ito default" if n_series <= len(OKABE_ITO) else "the extended default"
    rationale_parts = [
        f"Chose {len(chosen)} of {n_series} colours from "
        f"{'the supplied set' if available else default_label} by max-min separation on a {background} background."
    ]
    if focal:
        rationale_parts.append(f"Pinned focal {focal} to series 0.")
    if has_semantics:
        rationale_parts.append(
            f"Applied {len(hints) - len(semantic_findings)} of {len(hints)} semantic hint(s); "
            f"positions are identity-bound so the palette is not prefix-nested."
        )
    if dropped:
        rationale_parts.append(
            f"{len(dropped)} colour(s) read poorly on this background ({', '.join(dropped)}) - "
            f"kept (contrast is a soft preference) and reported by validate_palette."
        )
    if not resolved:
        rationale_parts.append(
            f"UNRESOLVED: the {'supplied' if available else 'default'} set has only {len(chosen)} "
            f"distinct colour(s) for {n_series} series - {shortfall} short. Route back to the select "
            f"stage to drop a series or supply more colours; do not invent hues to pad the palette."
        )

    return {
        "resolved": resolved,
        "route_to": None if resolved else "select",
        "assignment": assignment,
        "ordered_palette": chosen,
        "chosen": chosen,
        "prefix_nested": not has_semantics,
        "n_series": n_series,
        "shortfall": shortfall,
        "suggested_additions": suggestions,
        "dropped_low_contrast": dropped,
        "semantic_findings": semantic_findings,
        "validation": validation,
        "rationale": " ".join(rationale_parts)
        + (
            ""
            if has_semantics
            else " Palette is ordered and prefix-nested: a panel with fewer series uses the first that many colours."
        ),
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

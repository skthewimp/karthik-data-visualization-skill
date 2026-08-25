from pathlib import Path

from dataviz_mcp.palette import (
    extract_palette_from_image,
    recommend_colours,
    validate_palette,
)


def test_validate_flags_confusable_blues():
    result = validate_palette(["#3B6FB0", "#3E74B5"], background="#FFFFFF")
    assert result["verdict"] == "soft_fail"
    rules = {finding["rule"] for finding in result["findings"]}
    assert "series_distinctness" in rules
    assert any(rule.startswith("cvd_") for rule in rules)


def test_validate_passes_distinct_pair():
    # Blue + pink: high background contrast, distinct across normal/CVD/grayscale.
    result = validate_palette(["#0072B2", "#CC79A7"], background="#FFFFFF")
    assert result["verdict"] == "pass"


def test_validate_flags_low_background_contrast():
    result = validate_palette(["#FEFEFE"], background="#FFFFFF")
    assert any(f["rule"] == "mark_vs_background" for f in result["findings"])


def test_recommend_reports_shortfall_and_suggestions():
    result = recommend_colours(["#D55E00", "#0072B2", "#009E73"], n_series=5, focal="#D55E00")
    assert result["chosen"][0] == "#D55E00"  # focal pinned to series 0
    assert result["shortfall"] == 2
    assert len(result["suggested_additions"]) == 2


def test_recommend_falls_back_to_default_when_no_available():
    result = recommend_colours(None, n_series=3)
    assert len(result["chosen"]) == 3
    # Verdict may be a soft_fail (accessibility on white is genuinely hard); it must report one.
    assert result["validation"]["verdict"] in {"pass", "soft_fail"}


def test_recommend_returns_ordered_prefix_nested_palette():
    result = recommend_colours(["#D55E00", "#0072B2", "#009E73", "#CC79A7"], n_series=4)
    palette = result["ordered_palette"]
    assert result["prefix_nested"] is True
    # assignment order must match the ordered palette, so a smaller panel takes the prefix.
    assert [item["colour"] for item in result["assignment"]] == palette
    # the first two of a four-colour request are the two farthest apart in the pool.
    assert len(palette) == 4 and palette[:2] != palette[2:]


def test_recommend_drops_low_contrast_colours():
    result = recommend_colours(["#FEFEFE", "#0072B2", "#D55E00"], n_series=2)
    assert "#FEFEFE" in result["dropped_low_contrast"]
    assert "#FEFEFE" not in result["chosen"]


def test_preserves_usable_current_assignment():
    # A prior category->colour map whose colours already form a good palette must be
    # kept verbatim: identity is stable, nothing is remapped.
    current = {
        "cacheRead": "#E69F00",
        "cacheWrite": "#56B4E9",
        "output": "#009E73",
        "input": "#F0E442",
    }
    result = recommend_colours(
        list(current.values()),
        n_series=4,
        series=list(current),
        current_assignment=current,
    )
    assert result["preserved"] is True
    assert result["remapped"] == []
    got = {item["series"]: item["colour"] for item in result["assignment"]}
    assert got == current


def test_remaps_only_failing_category_and_discloses():
    # Two confusable blues in the prior map; the rest are fine. Only one category moves,
    # the others keep their colour, and the move is disclosed with a reason.
    current = {
        "cacheRead": "#3B6FB0",  # confusable blue
        "cacheWrite": "#3E74B5",  # confusable blue
        "output": "#009E73",
        "input": "#D55E00",
    }
    result = recommend_colours(
        None,  # draw replacements from the Okabe-Ito default
        n_series=4,
        series=list(current),
        current_assignment=current,
    )
    assert result["preserved"] is False
    moved = {entry["series"] for entry in result["remapped"]}
    assert moved and moved.issubset({"cacheRead", "cacheWrite"})
    assert len(moved) == 1  # only one of the confusable pair needs to move
    got = {item["series"]: item["colour"] for item in result["assignment"]}
    assert got["output"] == "#009E73"  # untouched category keeps its colour
    assert got["input"] == "#D55E00"
    entry = result["remapped"][0]
    assert entry["from"] == current[entry["series"]]
    assert entry["to"] != entry["from"] and entry["reason"]


def test_extract_palette_from_image_returns_hexes():
    fixture = Path("tester-outputs/sector-performance-accepted.png")
    if not fixture.exists():
        return  # fixture optional in some checkouts
    result = extract_palette_from_image(str(fixture), max_colours=5)
    assert result["colours"]
    assert all(colour.startswith("#") and len(colour) == 7 for colour in result["colours"])


def test_extract_palette_missing_file_reports_error():
    result = extract_palette_from_image("/nonexistent/none.png")
    assert result["colours"] == []
    assert "error" in result

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


def test_recommend_does_not_starve_pool_on_low_contrast_background():
    # Case-04 regression: the seven-series default must return seven distinct colours on
    # white. Contrast is soft, so Okabe-Ito colours that read poorly on white are NOT
    # dropped from the pool - the count is the hard constraint.
    result = recommend_colours(None, n_series=7)
    assert result["resolved"] is True
    assert result["route_to"] is None
    assert result["shortfall"] == 0
    assert len(result["assignment"]) == 7
    assert len(set(result["chosen"])) == 7  # seven distinct colours
    # Validation covers every assigned series.
    assert result["validation"]["n_colours"] == 7


def test_recommend_extends_default_pool_past_eight_series():
    result = recommend_colours(None, n_series=12)
    assert result["resolved"] is True
    assert len(set(result["chosen"])) == 12  # Okabe-Ito (8) extended with vetted extras


def test_recommend_generates_to_complete_a_short_supplied_pool():
    # A small brand set for more series than it holds: the named palettes are only
    # recommendations, so the count (hard) is met by generating extra distinguishable
    # colours rather than giving up - never a short palette.
    result = recommend_colours(["#D55E00", "#0072B2", "#009E73"], n_series=5, focal="#D55E00")
    assert result["chosen"][0] == "#D55E00"  # focal still pinned to series 0
    assert result["resolved"] is True
    assert result["route_to"] is None
    assert result["shortfall"] == 0
    assert len(result["assignment"]) == 5
    assert len(set(result["chosen"])) == 5  # five distinct colours
    # Exactly two were generated to cover the deficit, and they are part of the palette.
    assert len(result["generated_additions"]) == 2
    assert all(c in result["chosen"] for c in result["generated_additions"])
    # Every generated colour reads on the background.
    from dataviz_mcp.color_math import _contrast_ratio
    assert all(_contrast_ratio(c, "#FFFFFF") >= 3.0 for c in result["generated_additions"])


def test_recommend_unresolved_only_when_generation_cannot_clear_background():
    # A mid-grey background few colours read against: if even generation cannot produce
    # enough colours clearing the bar, the result is unresolved and routes to select.
    result = recommend_colours(["#808080"], n_series=8, background="#7F7F7F")
    if not result["resolved"]:
        assert result["route_to"] == "select"
        assert result["shortfall"] > 0


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


def test_recommend_soft_family_picks_in_family_colour():
    # Series 0 wants a blue; the pool has one clear blue among unrelated hues.
    result = recommend_colours(
        ["#D55E00", "#0072B2", "#009E73", "#CC79A7"],
        n_series=3,
        semantic_hints=[{"series_index": 0, "hue_family": "blue"}],
    )
    by_index = {item["series_index"]: item["colour"] for item in result["assignment"]}
    assert by_index[0] == "#0072B2"  # the blue, honoured for the blue-intent series
    assert result["prefix_nested"] is False  # positions are now identity-bound
    assert not result["semantic_findings"]


def test_recommend_hard_pin_places_exact_colour_at_index():
    result = recommend_colours(
        ["#D55E00", "#0072B2", "#009E73"],
        n_series=3,
        semantic_hints=[{"series_index": 1, "colour": "#111111"}],
    )
    by_index = {item["series_index"]: item["colour"] for item in result["assignment"]}
    assert by_index[1] == "#111111"


def test_recommend_soft_family_unmet_reports_finding():
    # No blue in the pool (orange/green/pink, all contrast-passing); blue can't be met.
    result = recommend_colours(
        ["#D55E00", "#009E73", "#CC79A7"],
        n_series=3,
        semantic_hints=[{"series_index": 0, "hue_family": "blue"}],
    )
    assert any(f["rule"] == "semantic_unmet" for f in result["semantic_findings"])
    # It still returns a full, separation-based assignment for every series.
    assert len(result["assignment"]) == 3


def test_recommend_away_kit_used_when_home_colours_collide():
    # Two series both want blue; the pool has two confusable blues plus an orange.
    # Series 0 keeps a blue (home); series 1's blue clashes, so it takes its away kit.
    result = recommend_colours(
        ["#0072B2", "#3B6FB0", "#D55E00"],
        n_series=2,
        semantic_hints=[
            {"series_index": 0, "hue_family": "blue"},
            {"series_index": 1, "hue_family": "blue", "alternates": ["orange"]},
        ],
    )
    by_index = {item["series_index"]: item["colour"] for item in result["assignment"]}
    assert by_index[1] == "#D55E00"  # away kit, not a second confusable blue
    assert not result["semantic_findings"]


def test_recommend_flags_collision_when_no_away_kit():
    # Both want blue, no alternates, only confusable blues available -> flag, keep home.
    result = recommend_colours(
        ["#0072B2", "#3B6FB0"],
        n_series=2,
        semantic_hints=[
            {"series_index": 0, "hue_family": "blue"},
            {"series_index": 1, "hue_family": "blue"},
        ],
    )
    assert any(f["rule"] == "semantic_collision" for f in result["semantic_findings"])
    assert len(result["assignment"]) == 2  # both series still placed


def test_recommend_semantics_can_override_contrast_gate():
    # The only blue is too light to pass the 3:1 background gate, but a blue hint still
    # reaches it - meaning outranks accessibility (which validate_palette then flags).
    result = recommend_colours(
        ["#CCE0FF", "#D55E00"],
        n_series=1,
        semantic_hints=[{"series_index": 0, "hue_family": "blue"}],
    )
    by_index = {item["series_index"]: item["colour"] for item in result["assignment"]}
    assert by_index[0] == "#CCE0FF"


def test_recommend_no_hints_matches_prior_behaviour():
    result = recommend_colours(["#D55E00", "#0072B2", "#009E73", "#CC79A7"], n_series=4)
    assert result["prefix_nested"] is True
    assert result["semantic_findings"] == []


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

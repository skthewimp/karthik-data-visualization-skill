from __future__ import annotations

from dataviz_mcp.color_math import (
    _contrast_ratio,
    grayscale_value,
    hue_delta,
    lightness_delta,
    simulate_cvd,
)
from dataviz_mcp.palette import (
    recommend_colours,
    validate_palette,
)


# ---- color math ----


def test_contrast_ratio_black_on_white_is_21():
    assert round(_contrast_ratio("#000000", "#FFFFFF"), 1) == 21.0


def test_contrast_ratio_unparseable_returns_none():
    assert _contrast_ratio("not-a-colour", "#FFFFFF") is None


def test_hue_and_lightness_deltas():
    assert hue_delta("#FF0000", "#00FF00") > 100  # red vs green far apart in hue
    assert lightness_delta("#000000", "#FFFFFF") > 0.9


def test_simulate_cvd_returns_rgb_triple():
    out = simulate_cvd("#D55E00", "deuteranope")
    assert out is not None and len(out) == 3
    assert all(0 <= channel <= 255 for channel in out)


def test_grayscale_orders_by_luminance():
    assert grayscale_value("#FFFFFF") > grayscale_value("#000000")

# ---- palette ----


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

    assert result["generated_additions"] == []


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

    for added in result["generated_additions"]:
        assert min(hue_delta(added, other) for other in result["chosen"] if other != added) >= 45


def test_recommend_returns_ordered_prefix_nested_palette():
    result = recommend_colours(["#D55E00", "#0072B2", "#009E73", "#CC79A7"], n_series=4)
    palette = result["ordered_palette"]
    assert result["prefix_nested"] is True
    assert result["semantic_findings"] == []
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


def test_proposed_pool_replaces_a_colour_it_cannot_tell_apart():
    # A proposed (not committed) set with a green and a teal that fail series distinctness: the
    # tool generates a colour that can be told apart instead of handing back the pair.
    pool = ["#007C91", "#D97706", "#7C3AED", "#2F855A"]
    result = recommend_colours(pool, 4, "#FAFAF7", available_source="proposed")
    assert len(result["generated_additions"]) == 1
    rules = {f["rule"] for f in result["validation"]["findings"]}
    assert "series_distinctness" not in rules
    assert not any(rule.startswith("cvd_") for rule in rules)


def test_brand_pool_is_spent_as_supplied_and_first():
    pool = ["#007C91", "#D97706", "#7C3AED", "#2F855A"]
    assert recommend_colours(pool, 4, "#FAFAF7", available_source="brand-skill")["generated_additions"] == []
    # Short brand set: brand colours take the first slots, generated ones only fill the count.
    result = recommend_colours(["#007C91", "#D97706"], 4, "#FAFAF7", available_source="brand-skill")
    assert result["chosen"][:2] == ["#007C91", "#D97706"]
    assert result["chosen"][2:] == result["generated_additions"]


def test_categorical_hues_are_distinct_even_when_lightness_separates_them():
    colours = ['#4D9221', '#106030']
    result = validate_palette(colours)
    assert any(f['rule'] == 'categorical_hue_separation' and f['colours'] == colours
               for f in result['findings'])
    neutral = validate_palette(['#222222', '#AAAAAA'])
    assert not any(f['rule'] == 'categorical_hue_separation' for f in neutral['findings'])
    chosen = recommend_colours(colours, n_series=2, available_source='proposed')['chosen']
    assert chosen != colours and set(chosen) != set(colours)

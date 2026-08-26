"""Tests for the tolerant structured-text handoff parser."""

from __future__ import annotations

from pathlib import Path

from dataviz_mcp import handoff

KEYS = ("builder", "needs_annotations", "needs_explainer", "needs_color_plan")


def test_parses_fenced_routing_block_after_prose():
    text = (
        "## DESIGN\nDirect-labelled lines.\n\n"
        "```routing\nbuilder: table\nneeds_annotations: yes\n"
        "needs_explainer: no\nneeds_color_plan: YES\n```\n"
    )
    routing = handoff.parse_routing(text, KEYS)
    assert routing == {
        "builder": "table",
        "needs_annotations": True,
        "needs_explainer": False,
        "needs_color_plan": True,
    }


def test_parses_bare_marker_block_and_stops_at_next_heading():
    text = (
        "---ROUTING---\nbuilder: chart\nneeds_annotations: true\n\n"
        "## NOTES\nneeds_explainer: this prose must not be parsed as a flag\n"
    )
    routing = handoff.parse_routing(text, KEYS)
    assert routing["builder"] == "chart"
    assert routing["needs_annotations"] is True
    # The heading ends the block, so the prose line does not flip needs_explainer.
    assert routing["needs_explainer"] is False


def test_json_fallback_for_strong_model_output():
    text = '```json\n{"builder": "table", "needs_annotations": true,}\n```'
    routing = handoff.parse_routing(text, KEYS)
    assert routing["builder"] == "table"
    assert routing["needs_annotations"] is True


def test_json_fallback_extracts_outermost_object_amid_prose():
    text = 'Here is the plan:\n{"builder": "chart", "needs_color_plan": 1}\nThanks!'
    routing = handoff.parse_routing(text, KEYS)
    assert routing["builder"] == "chart"
    assert routing["needs_color_plan"] is True


def test_garbled_input_degrades_to_defaults():
    routing = handoff.parse_routing("nothing structured here", KEYS)
    assert routing == {
        "builder": "chart",
        "needs_annotations": False,
        "needs_explainer": False,
        "needs_color_plan": False,
    }


def test_unknown_builder_value_falls_back_to_chart():
    routing = handoff.parse_routing("```routing\nbuilder: sankey\n```", ("builder",))
    assert routing["builder"] == "chart"


def test_bool_token_coercion():
    for token in ("yes", "y", "true", "1", "on"):
        assert handoff.coerce_bool(token) is True
    for token in ("no", "n", "false", "0", "off", "none", ""):
        assert handoff.coerce_bool(token) is False
    assert handoff.coerce_bool("maybe") is None


def test_parse_routing_reads_from_path(tmp_path: Path):
    artifact = tmp_path / "select-01.md"
    artifact.write_text("```routing\nbuilder: table\n```\n", encoding="utf-8")
    routing = handoff.parse_routing(artifact, ("builder",))
    assert routing["builder"] == "table"


def test_parse_routing_missing_path_defaults(tmp_path: Path):
    routing = handoff.parse_routing(tmp_path / "absent.md", ("builder",))
    assert routing["builder"] == "chart"


def test_expected_sections_lists_top_level_properties():
    schema = {"properties": {"a": {}, "b": {}, "c": {}}}
    assert handoff.expected_sections(schema) == ("a", "b", "c")
    assert handoff.expected_sections(None) == ()


def test_render_handoff_spec_includes_sections_and_routing_keys():
    spec = handoff.render_handoff_spec(("key_messages", "diagnosis"), ("builder",))
    assert "`## KEY MESSAGES`" in spec
    assert "`## DIAGNOSIS`" in spec
    assert "```routing" in spec
    assert "builder: <value>" in spec


def test_render_handoff_spec_without_routing_has_no_block():
    spec = handoff.render_handoff_spec(("row_grain",))
    assert "```routing" not in spec

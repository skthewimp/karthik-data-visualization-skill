"""Contract tests for the staged pipeline definitions.

The load-bearing guarantee is that each stage carries only its own skills - the fix for
the context rot the old whole-repository bundle caused.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dataviz_mcp import stage_contracts as sc


REPO_ROOT = Path(__file__).resolve().parents[2]

ALL_SKILLS = {
    path.parent.parent.name
    for path in REPO_ROOT.glob("*/codex/SKILL.md")
}


def _all_stages():
    for name in ("repair", "story"):
        for stage in sc.pipeline(name):
            yield name, stage


def test_pipelines_have_expected_stage_order() -> None:
    assert tuple(s.stage_id for s in sc.REPAIR_PIPELINE) == (
        "diagnose",
        "select",
        "build",
        "refine",
    )
    assert tuple(s.stage_id for s in sc.STORY_PIPELINE) == (
        "discover",
        "contract",
        "clean",
        "facts",
        "select",
        "build",
        "refine",
    )


def test_diagnose_stage_carries_only_its_skills() -> None:
    """The context-rot regression guard: no unrelated skill leaks into a stage."""
    diagnose = sc.stage("repair", "diagnose")
    bundle, sources = sc.stage_skill_bundle(diagnose, repository_root=REPO_ROOT)

    assert set(diagnose.skill_names()) == {
        "dataviz-brief",
        "dataviz-extract",
        "dataviz-critique",
    }
    # Every carried skill is present...
    for name in diagnose.skill_names():
        assert f"{name}/codex/SKILL.md" in sources
    # ...and no other skill's source is present.
    for name in ALL_SKILLS - set(diagnose.skill_names()):
        assert f"{name}/codex/SKILL.md" not in bundle


@pytest.mark.parametrize("pipeline_name,stage", list(_all_stages()))
def test_every_stage_bundles_only_named_skills(pipeline_name, stage) -> None:
    # Resolve a builder for build stages so bundling is well-defined.
    builder = "chart" if stage.builder_skills else None
    active = tuple(stage.conditional_skills)  # exercise all conditionals at once
    names = set(stage.skill_names(builder=builder, active_conditions=active))
    _bundle, sources = sc.stage_skill_bundle(
        stage, builder=builder, active_conditions=active, repository_root=REPO_ROOT
    )
    carried = {Path(s).parent.parent.name for s in sources}
    assert carried == names
    # Nothing outside the named set leaked in.
    assert not (carried - ALL_SKILLS - {name for name in names if name not in ALL_SKILLS})


def test_build_stage_swaps_builder_skill() -> None:
    build = sc.stage("repair", "build")
    chart = set(build.skill_names(builder="chart"))
    table = set(build.skill_names(builder="table"))
    assert "karthik-data-visualization" in chart
    assert "karthik-data-visualization" not in table
    assert "karthik-table-style" in table
    assert "karthik-table-style" not in chart
    # A build stage without a builder choice is an error, not a silent all-skills bundle.
    with pytest.raises(ValueError):
        build.skill_names()


def test_build_conditionals_load_only_when_active() -> None:
    build = sc.stage("repair", "build")
    without = set(build.skill_names(builder="chart"))
    assert "chart-annotations" not in without
    with_ann = set(
        build.skill_names(builder="chart", active_conditions=("chart-annotations",))
    )
    assert "chart-annotations" in with_ann


def test_stage_adapter_includes_guardrails_and_focus() -> None:
    diagnose = sc.stage("repair", "diagnose")
    adapter, sources, revision = sc.build_stage_adapter(diagnose, repository_root=REPO_ROOT)
    assert "untrusted content" in adapter
    assert "diagnose-and-extract stage" in adapter
    assert sources
    # revision is a git sha or None; when present it is hex-ish and non-empty.
    assert revision is None or revision.strip()


def test_facts_stage_is_a_named_placeholder() -> None:
    facts = sc.stage("story", "facts")
    assert facts.skills == ()
    bundle, sources = sc.stage_skill_bundle(facts, repository_root=REPO_ROOT)
    assert sources == ()
    assert bundle == ""


def test_missing_builder_choice_raises() -> None:
    build = sc.stage("story", "build")
    with pytest.raises(ValueError):
        sc.stage_skill_bundle(build, repository_root=REPO_ROOT)


def test_select_output_drives_builder_enum() -> None:
    assert sc.SELECT_SCHEMA["properties"]["builder"]["enum"] == ["chart", "table"]


def test_recommend_colours_returns_one_colour_per_series() -> None:
    """colour_groups is the palette size, so a k-series plan yields k assigned colours."""
    from dataviz_mcp.palette import recommend_colours

    available = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for n_series in (1, 2, 3, 4):
        result = recommend_colours(available, n_series=n_series)
        assert result["n_series"] == n_series
        assert len(result["assignment"]) == n_series
        assert len(result["chosen"]) == n_series


def test_build_result_can_record_recommendations_used() -> None:
    props = sc.BUILD_SCHEMA["properties"]
    assert "recommendations_used" in props
    used = props["recommendations_used"]
    # Every numeric display group must get a precision decision: number_formats required.
    assert used["required"] == ["number_formats"]


def test_select_carries_exact_lookup_decision_upstream() -> None:
    """The exact-vs-spread call is made at select, per numeric display group, not at build."""
    props = sc.SELECT_SCHEMA["properties"]
    assert "number_display_groups" in props
    assert "number_display_groups" in sc.SELECT_SCHEMA["required"]
    item = props["number_display_groups"]["items"]
    assert "exact_lookup_required" in item["required"]
    assert item["properties"]["exact_lookup_required"]["type"] == "boolean"
    # A group's decision is auditable: a reason is required either way.
    assert "reason" in item["required"]
    assert item["properties"]["reason"]["minLength"] == 1


def test_acceptance_checks_split_fidelity_from_external_validation() -> None:
    """Every check declares whether it is answerable in-run or needs external ground truth."""
    for schema in (sc.SELECT_SCHEMA, sc.REPAIR_PIPELINE[1].output_schema):
        item = schema["properties"]["acceptance_checks"]["items"]
        assert "validation_type" in item["required"]
        assert item["properties"]["validation_type"]["enum"] == [
            "source_fidelity",
            "external_validation",
        ]


def test_missing_external_validation_never_blocks_delivery() -> None:
    """An unavailable external validation is disclosed in a footnote, not a blocking failure."""
    build = " ".join(sc.stage("repair", "build").instructions.split())
    refine = " ".join(sc.stage("repair", "refine").instructions.split())
    # Build delivers and discloses rather than demanding the missing source.
    assert "DELIVERED regardless" in build
    assert "external_validation" in build
    # Refine reserves `blocked` for a genuine inability to produce any artifact.
    assert "residual_limitations" in refine
    assert "Reserve the ``blocked`` verdict" in refine


def test_only_select_stages_declare_routing_fields() -> None:
    """The driver parses routing only from select; other handoffs are pure content."""
    for pipeline_name, stage in _all_stages():
        if stage.stage_id == "select":
            assert stage.routing_fields == sc._SELECT_ROUTING_FIELDS
        else:
            assert stage.routing_fields == ()


def test_handoff_spec_lists_content_sections_and_routing_block() -> None:
    select = sc.stage("repair", "select")
    spec = select.handoff_spec()
    # Content sections come from the schema, minus the routing scalars.
    assert "`## DESIGN`" in spec
    assert "`## ACCEPTANCE CHECKS`" in spec
    # Routing scalars appear only in the routing block, never as a prose section.
    assert "`## BUILDER`" not in spec
    assert "```routing" in spec
    for field in sc._SELECT_ROUTING_FIELDS:
        assert f"{field}: <value>" in spec


def test_diagnose_handoff_spec_has_no_routing_block() -> None:
    spec = sc.stage("repair", "diagnose").handoff_spec()
    assert "`## KEY MESSAGES`" in spec
    assert "```routing" not in spec


def test_adapters_drop_the_return_json_schema_instruction() -> None:
    """The handoff is structured text now; no stage should still demand JSON to a schema."""
    for _pipeline_name, stage in _all_stages():
        assert "against the required schema" not in stage.instructions


def test_stage_adapter_includes_handoff_format_and_spec() -> None:
    diagnose = sc.stage("repair", "diagnose")
    adapter, _sources, _revision = sc.build_stage_adapter(diagnose, repository_root=REPO_ROOT)
    assert "structured text, not JSON" in adapter
    assert "`## KEY MESSAGES`" in adapter


def test_number_format_cannot_record_a_silent_exact_override() -> None:
    """An exact-digit override must carry its flag and a non-empty reason - never silent."""
    entry = (
        sc.BUILD_SCHEMA["properties"]["recommendations_used"]
        ["properties"]["number_formats"]["items"]
    )
    assert "exact_override" in entry["required"]
    assert "reason" in entry["required"]
    assert entry["properties"]["reason"]["minLength"] == 1

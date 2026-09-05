"""Contract tests for the staged pipeline definitions.

The load-bearing guarantee is that each stage carries only its own skills - the fix for
the context rot the old whole-repository bundle caused.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dataviz_mcp import stage_contracts as sc


REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_stages():
    # Shared stage objects need only one bundle check across both pipelines.
    seen = set()
    for name in ("repair", "story"):
        for stage in sc.pipeline(name):
            if id(stage) not in seen:
                seen.add(id(stage))
                yield name, stage


_CONSTRUCT_TAIL = ("insight", "select", "idea", "build", "execution", "explain")


def test_pipelines_have_expected_stage_order() -> None:
    assert tuple(s.stage_id for s in sc.REPAIR_PIPELINE) == ("diagnose", *_CONSTRUCT_TAIL)
    assert tuple(s.stage_id for s in sc.STORY_PIPELINE) == (
        "discover",
        "contract",
        "clean",
        *_CONSTRUCT_TAIL,
    )


def test_both_front_halves_share_one_construct_tail() -> None:
    """The literal coalescing: the post-insight stages are the SAME objects in both."""
    for stage_id in ("select", "idea", "build", "execution", "explain"):
        assert sc.stage("repair", stage_id) is sc.stage("story", stage_id)
    # insight is parameterised only by the artifact that feeds it; everything else matches.
    repair_insight = sc.stage("repair", "insight")
    story_insight = sc.stage("story", "insight")
    assert repair_insight.skills == story_insight.skills == ("karthik-evidence-builder",)
    assert repair_insight.instructions == story_insight.instructions
    assert repair_insight.output_schema is story_insight.output_schema is sc.INSIGHT_SCHEMA
    assert repair_insight.input_schema is sc.DIAGNOSE_SCHEMA
    assert story_insight.input_schema is sc.CLEAN_SCHEMA


@pytest.mark.parametrize("pipeline_name,stage", list(_all_stages()))
def test_every_stage_bundles_only_named_skills(pipeline_name, stage) -> None:
    # Resolve a builder for build stages so bundling is well-defined.
    builder = "chart" if stage.builder_skills else None
    active = tuple(stage.conditional_skills)  # exercise all conditionals at once
    if builder:
        active = active + tuple(stage.builder_conditional_skills.get(builder, {}))
    names = set(stage.skill_names(builder=builder, active_conditions=active))
    _bundle, sources = sc.stage_skill_bundle(
        stage, builder=builder, active_conditions=active, repository_root=REPO_ROOT
    )
    carried = {Path(s).parent.parent.name for s in sources}
    assert carried == names


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


def test_annotations_are_chart_only_never_dragged_into_a_table_build() -> None:
    """The build call differs by what is built: on-chart marks can't enter a table build."""
    build = sc.stage("story", "build")
    # Even asked for, chart-annotations does not load for a table - a table has no on-chart
    # marks, so the skill is not offered to that builder at all.
    table = set(build.skill_names(builder="table", active_conditions=("chart-annotations",)))
    assert "chart-annotations" not in table
    assert "karthik-table-style" in table
    assert "karthik-data-visualization" not in table
    # The same request loads it for a chart.
    chart = set(build.skill_names(builder="chart", active_conditions=("chart-annotations",)))
    assert "chart-annotations" in chart


def test_explainer_is_a_render_independent_stage_not_a_build_skill() -> None:
    """The note is written from the finding, not the pixels - so it never rides in build."""
    build = sc.stage("story", "build")
    for builder in ("chart", "table"):
        loaded = set(
            build.skill_names(builder=builder, active_conditions=("chart-explainer",))
        )
        assert "chart-explainer" not in loaded
    explain = sc.stage("story", "explain")
    assert explain.skills == ("chart-explainer",)
    # Reads the plan (select) and the finding (insight); never the build/render artifact.
    assert explain.input_schema is sc.SELECT_SCHEMA
    assert explain.also_reads == ("insight",)
    assert "build" not in explain.also_reads


def test_precision_and_colour_skills_are_not_carried_into_build() -> None:
    """Both are decided at select and resolved by a tool; build applies, never re-decides."""
    build = sc.stage("story", "build")
    for builder in ("chart", "table"):
        loaded = set(
            build.skill_names(
                builder=builder,
                active_conditions=("dataviz-precision", "dataviz-color", "chart-explainer"),
            )
        )
        assert "dataviz-precision" not in loaded
        assert "dataviz-color" not in loaded
    # The signals survive - needs_*_plan still tell the driver to resolve format / palette.
    props = sc.SELECT_SCHEMA["properties"]
    assert "needs_precision_plan" in props
    assert "needs_color_plan" in props


def test_stage_adapter_includes_guardrails_and_focus() -> None:
    diagnose = sc.stage("repair", "diagnose")
    adapter, sources, revision = sc.build_stage_adapter(diagnose, repository_root=REPO_ROOT)
    assert "untrusted content" in adapter
    assert "diagnose-and-extract stage" in adapter
    assert diagnose.handoff_spec() in adapter
    assert sources
    # revision is a git sha or None; when present it is hex-ish and non-empty.
    assert revision is None or revision.strip()


def test_insight_artifact_is_carried_across_the_gate_to_idea_and_build() -> None:
    """The plan must survive the idea gate: idea and build explicitly also read insight.

    The idea gate emits a critique, not a plan, so a mechanical harness that fed each stage
    only its predecessor's output would lose the headline claim at the gate - it would reach
    select and then vanish. ``also_reads`` closes that on a weak-model driver.
    """
    for pipeline_name in ("repair", "story"):
        idea = sc.stage(pipeline_name, "idea")
        build = sc.stage(pipeline_name, "build")
        assert "insight" in idea.also_reads
        assert "insight" in build.also_reads
    # select reads insight as its direct input, so it needs no also_reads.
    assert sc.stage("story", "select").input_schema is sc.INSIGHT_SCHEMA
    assert sc.stage("story", "select").also_reads == ()


def test_missing_builder_choice_raises() -> None:
    build = sc.stage("story", "build")
    with pytest.raises(ValueError):
        sc.stage_skill_bundle(build, repository_root=REPO_ROOT)


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

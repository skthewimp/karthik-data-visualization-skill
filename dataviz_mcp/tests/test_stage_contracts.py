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
    if builder:
        active = active + tuple(stage.builder_conditional_skills.get(builder, {}))
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


def test_select_carries_the_colour_decision_not_the_hexes() -> None:
    """The colour plan (source, focal, semantic meaning) is decided at select, resolved later."""
    colour_plan = sc.SELECT_SCHEMA["properties"]["colour_plan"]
    assert "colour_plan" in sc.SELECT_SCHEMA["required"]
    props = colour_plan["properties"]
    assert set(props) == {
        "available_source",
        "available_colours",
        "focal_series",
        "semantic_assignments",
    }
    # available_source is the one required call; the rest are populated only when colour has work.
    assert colour_plan["required"] == ["available_source"]


def test_stage_adapter_includes_guardrails_and_focus() -> None:
    diagnose = sc.stage("repair", "diagnose")
    adapter, sources, revision = sc.build_stage_adapter(diagnose, repository_root=REPO_ROOT)
    assert "untrusted content" in adapter
    assert "diagnose-and-extract stage" in adapter
    assert sources
    # revision is a git sha or None; when present it is hex-ish and non-empty.
    assert revision is None or revision.strip()


def test_insight_stage_has_a_real_skill() -> None:
    """The old skill-less facts placeholder is gone: insight loads the evidence builder."""
    insight = sc.stage("story", "insight")
    assert insight.skills == ("karthik-evidence-builder",)
    _bundle, sources = sc.stage_skill_bundle(insight, repository_root=REPO_ROOT)
    assert sources == ("karthik-evidence-builder/codex/SKILL.md",)


def test_insight_names_the_headline_claim_before_build() -> None:
    """The headline is decided at insight, not improvised at build."""
    props = sc.INSIGHT_SCHEMA["properties"]
    assert "headline_claim" in props
    assert "headline_claim" in sc.INSIGHT_SCHEMA["required"]
    assert "candidate_annotations" in props


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


def test_build_derives_text_placement_and_keeps_data_out_of_layout() -> None:
    """Existing text blocks trigger placement; data coordinates never reserve chrome."""
    build = " ".join(sc.stage("repair", "build").instructions.split())
    assert "presence of such blocks is the trigger" in build
    assert "every reader-facing text block whose words and anchor are already known" in build
    assert "series/category, on-mark data, and axis label" in build
    assert "must not invent a universal character count" in build
    assert "compact key or footnote" in build
    assert "Never change a quantitative scale merely to reserve room" in build
    assert "never reserve the same room" in build


def test_acceptance_checks_split_fidelity_from_external_validation() -> None:
    """Every check declares whether it is answerable in-run or needs external ground truth."""
    for schema in (sc.SELECT_SCHEMA, sc.stage("repair", "select").output_schema):
        item = schema["properties"]["acceptance_checks"]["items"]
        assert "validation_type" in item["required"]
        assert item["properties"]["validation_type"]["enum"] == [
            "source_fidelity",
            "external_validation",
        ]


def test_missing_external_validation_never_blocks_delivery() -> None:
    """An unavailable external validation is disclosed in a footnote, not a blocking failure."""
    build = " ".join(sc.stage("repair", "build").instructions.split())
    execution = " ".join(sc.stage("repair", "execution").instructions.split())
    # Build delivers and discloses rather than demanding the missing source.
    assert "DELIVERED regardless" in build
    assert "external_validation" in build
    # Execution reserves `blocked` for a genuine inability to produce any artifact.
    assert "residual_limitations" in execution
    assert "Reserve the ``blocked`` verdict" in execution


def test_no_construct_stage_hardcodes_an_iteration_cap() -> None:
    """Iteration budget is the driver's, not a fixed pass count baked into a stage."""
    for pipeline_name, stage in _all_stages():
        text = stage.instructions.lower()
        assert "cap the loop at two passes" not in text
        assert "cap at two passes" not in text
    # The execution gate says so explicitly.
    execution = sc.stage("repair", "execution").instructions
    assert "driver's budget" in execution


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

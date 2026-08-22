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

from __future__ import annotations

# ---- from test_stage_contracts.py ----

"""Contract tests for the staged pipeline definitions.

The load-bearing guarantee is that each stage carries only its own skills - the fix for
the context rot the old whole-repository bundle caused.
"""


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


def test_build_loads_only_its_builder_and_active_conditions() -> None:
    build = sc.stage("story", "build")
    for builder, skill in (("chart", "karthik-data-visualization"), ("table", "karthik-table-style")):
        assert set(build.skill_names(builder=builder)) == {skill}
        active = ("chart-annotations", "dataviz-precision", "dataviz-color", "chart-explainer")
        expected = {skill, "chart-annotations"} if builder == "chart" else {skill}
        assert set(build.skill_names(builder=builder, active_conditions=active)) == expected
    with pytest.raises(ValueError):
        sc.stage_skill_bundle(build, repository_root=REPO_ROOT)
    assert {"needs_precision_plan", "needs_color_plan"} <= sc.SELECT_SCHEMA["properties"].keys()


def test_selection_and_review_share_live_constraints_without_workflow_leakage(tmp_path) -> None:
    selector = tmp_path / "dataviz-selector/codex/SKILL.md"
    reviewer = tmp_path / "dataviz-idea-critique/codex/SKILL.md"
    selector.parent.mkdir(parents=True)
    reviewer.parent.mkdir(parents=True)
    reviewer.write_text("# Review\nJudge the supplied plan.")
    for rule in ("First constraint.", "Changed constraint."):
        selector.write_text(
            f"# Selector\n## Form constraints\n{rule}\n"
            "### Details\nShared detail.\n## Workflow\nSelection-only procedure.\n"
        )
        select, _ = sc.stage_skill_bundle(sc.stage("repair", "select"), repository_root=tmp_path)
        idea, sources = sc.stage_skill_bundle(sc.stage("repair", "idea"), repository_root=tmp_path)
        assert rule in select and rule in idea
        assert "Shared detail." in idea
        assert "Selection-only procedure." in select
        assert "Selection-only procedure." not in idea
        assert "dataviz-selector/codex/SKILL.md" in sources


@pytest.mark.parametrize("body", ["## Renamed\nRule", "## Form constraints\nA\n## Form constraints\nB"])
def test_review_fails_if_shared_constraints_are_missing_or_ambiguous(tmp_path, body) -> None:
    for name, text in (("dataviz-selector", body), ("dataviz-idea-critique", "Review")):
        path = tmp_path / name / "codex/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(text)
    with pytest.raises(RuntimeError, match="exactly one"):
        sc.stage_skill_bundle(sc.stage("repair", "idea"), repository_root=tmp_path)


def test_explainer_is_a_render_independent_stage_not_a_build_skill() -> None:
    """The note is written from the finding, not the pixels - so it never rides in build."""
    explain = sc.stage("story", "explain")
    assert explain.skills == ("chart-explainer",)
    # Reads the plan (select) and the finding (insight); never the build/render artifact.
    assert explain.input_schema is sc.SELECT_SCHEMA
    assert explain.also_reads == ("insight",)
    assert "build" not in explain.also_reads


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

# ---- from test_benchmark.py ----

import json
from pathlib import Path

from dataviz_mcp.benchmark import (
    REGRESSION_FAMILIES,
    benchmark_case_records,
    compare_benchmark_runs,
    load_case_corpus,
)


def test_corpus_loader_is_read_only_and_deduplicates_case_ids(tmp_path: Path) -> None:
    roots = [tmp_path / "one", tmp_path / "two"]
    for root in roots:
        case_dir = root / "cases" / "case-a"
        case_dir.mkdir(parents=True)
        (case_dir / "case.json").write_text(
            json.dumps({"case_id": "case-a", "iterations": [], "evaluations": []}),
            encoding="utf-8",
        )
    before = [(path, path.stat().st_mtime_ns) for path in tmp_path.rglob("case.json")]
    cases = load_case_corpus(*roots)
    after = [(path, path.stat().st_mtime_ns) for path in tmp_path.rglob("case.json")]
    assert len(cases) == 1
    assert before == after
    report = benchmark_case_records(cases)
    assert report["cases"] == 1
    assert report["regression_families"] == list(REGRESSION_FAMILIES)


def test_benchmark_comparison_requires_complete_replay_and_no_false_pass_increase() -> None:
    baseline = [
        {"case_id": "a", "evaluations": [{"verdict": "Revise"}, {"verdict": "Send"}]},
        {"case_id": "b", "evaluations": [{"verdict": "Revise"}, {"verdict": "Send"}]},
    ]
    replay = [
        {"case_id": "a", "evaluations": [{"verdict": "Send", "open_required_actions": []}]},
        {"case_id": "b", "evaluations": [{"verdict": "Send", "open_required_actions": []}]},
    ]
    comparison = compare_benchmark_runs(baseline, replay)
    assert comparison["cycle_reduction"] == 2
    assert comparison["false_passes_not_increased"] is True
    assert comparison["acceptance_met"] is True
    assert compare_benchmark_runs(baseline, replay[:1])["acceptance_met"] is False

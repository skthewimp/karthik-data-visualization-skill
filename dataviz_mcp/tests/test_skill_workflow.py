from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_skill(name: str, surface: str) -> str:
    return (ROOT / name / surface / "SKILL.md").read_text(encoding="utf-8")


def test_generation_uses_metadata_without_forcing_a_weaker_renderer() -> None:
    for surface in ("codex", "claude"):
        orchestrator = read_skill("dataviz-orchestrator", surface)
        assert "When the chosen renderer has a metadata-producing capability" in orchestrator
        assert "Do not bypass supported metadata generation" in orchestrator
        assert "Do not translate a sound ggplot2 chart into Matplotlib" in orchestrator
        assert "record uncovered geometry as unknown" in orchestrator
        assert "matching render/inspection records" in orchestrator

        visualizer = read_skill("karthik-data-visualization", surface)
        assert "prefer R/ggplot2 when it is available" in visualizer
        assert "default Matplotlib aesthetics fail this skill" in visualizer

        evaluator = read_skill("dataviz-eval", surface)
        assert "require its artifact hash to match this export" in evaluator
        assert "cannot be overridden by a clean-looking overview" in evaluator
        assert "cannot by itself support a pass" in evaluator


def test_repair_skill_is_portable_and_orders_inspection_before_review() -> None:
    for surface in ("codex", "claude"):
        fixer = read_skill("dataviz-fix", surface)
        assert "${CODEX_HOME:-$HOME/.codex}" in fixer
        assert "$HOME/.claude/skills/dataviz-fix" in fixer
        assert "${HERMES_SKILL_DIR}/scripts/case_manager.py" in fixer
        assert '--session "${CASE_SESSION}"' in fixer
        assert '--case "${CASE_ID}"' in fixer

        iterate = fixer.index('python3 "${CASE_MANAGER}" iterate')
        inspect = fixer.index('python3 "${CASE_MANAGER}" inspect')
        review = fixer.index('python3 "${CASE_MANAGER}" review-request')
        assert iterate < inspect < review
        assert "--bundle-manifest" in fixer[iterate:inspect]
        assert "Pass known mechanical defects into the review and minimum pass set" in fixer


def test_public_entrypoint_explains_installation_and_renderer_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Start here: agents and LLMs" in readme
    assert "Installing the skills does not register the MCP server" in readme
    assert "currently a **Matplotlib geometry adapter**" in readme
    assert "prefer R/ggplot2 when it is available" in readme
    assert "git clone https://github.com/skthewimp/karthik-data-visualization-skill.git" in readme

    sync_help = (ROOT / "sync.sh").read_text(encoding="utf-8")
    assert "--surface all|codex|claude|hermes" in sync_help

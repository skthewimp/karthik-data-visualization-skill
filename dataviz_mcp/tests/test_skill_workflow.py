from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_skill(name: str, surface: str) -> str:
    return (ROOT / name / surface / "SKILL.md").read_text(encoding="utf-8")


def test_generation_requires_metadata_render_before_exact_artifact_inspection() -> None:
    for surface in ("codex", "claude"):
        orchestrator = read_skill("dataviz-orchestrator", surface)
        assert "render the exact deliverable through the metadata-producing capability" in orchestrator
        assert "Do not bypass the metadata-producing renderer" in orchestrator
        assert "matching render/inspection records" in orchestrator

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

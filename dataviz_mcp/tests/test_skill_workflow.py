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
        assert "## Repair implementation contract" in visualizer
        assert "references/ggplot2-repair-patterns.md" in visualizer

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
        assert "Always load `dataviz-critique`" in fixer
        assert "design-contract" in fixer
        assert "revision-contract" in fixer
        assert "renderer-selection" in fixer
        assert "An unexplained Matplotlib selection is invalid" in fixer
        assert "independent pre-build plan audit" in fixer

        critique = read_skill("dataviz-critique", surface)
        assert "## Structured repair brief" in critique
        assert '"highest_consequence_findings"' in critique
        assert '"required_delivered_outcomes"' in critique
        assert '"source_inventory"' in critique
        assert '"layout_risks"' in critique

        visualizer = read_skill("karthik-data-visualization", surface)
        assert "one preservation mapping for every required source item" in visualizer
        assert "a layout plan for the declared delivery size" in visualizer
        assert "independent plan audit" in visualizer

        evaluator = read_skill("dataviz-eval", surface)
        assert "one contract stack for the exact replacement artifact" in evaluator
        assert "every panel" in evaluator
        assert "neighbouring zones" in evaluator
        assert "Audit the pre-build plan itself against the source" in evaluator


def test_public_entrypoint_explains_installation_and_renderer_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Start here: agents and LLMs" in readme
    assert "Installing the skills does not register the MCP server" in readme
    assert "chooses ggplot2 first" in readme
    assert "Use Matplotlib only" in readme
    assert "git clone https://github.com/skthewimp/karthik-data-visualization-skill.git" in readme

    sync_help = (ROOT / "sync.sh").read_text(encoding="utf-8")
    assert "--surface all|codex|claude|hermes" in sync_help


def test_maintainer_publish_rule_is_persistent_and_third_party_safe() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "completed changes" in agents
    assert "push it to GitHub" in agents
    assert "Deploy directly from the current Hermes checkout" in agents
    assert "Do not SSH back into the same host through an alias" in agents
    assert "Third-party clones and forks must not push" in agents
    assert "Do not force-push" in agents
    assert "An explicit instruction not to commit, push, or deploy overrides" in agents
    assert "Read and follow [`AGENTS.md`](AGENTS.md)" in claude

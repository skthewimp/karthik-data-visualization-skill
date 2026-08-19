from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_skill(name: str, surface: str) -> str:
    return (ROOT / name / surface / "SKILL.md").read_text(encoding="utf-8")


def test_generation_inspects_without_blocking_delivery() -> None:
    for surface in ("codex", "claude"):
        orchestrator = read_skill("dataviz-orchestrator", surface)
        assert "When the chosen renderer has a metadata-producing capability" in orchestrator
        assert "Do not translate a sound ggplot2 chart into Matplotlib" in orchestrator
        assert "record uncovered geometry as unknown" in orchestrator
        assert "An unavailable optional evaluator must not suppress it" in orchestrator

        visualizer = read_skill("karthik-data-visualization", surface)
        assert "prefer R/ggplot2 when it is available" in visualizer
        assert "default Matplotlib aesthetics fail this skill" in visualizer
        assert "## Optional audited repair contract" in visualizer
        assert "references/ggplot2-repair-patterns.md" in visualizer


def test_repair_skill_delivers_before_optional_review() -> None:
    for surface in ("codex", "claude"):
        fixer = read_skill("dataviz-fix", surface)
        assert "A valid rendered candidate must be delivered" in fixer
        assert "Do not load `dataviz-eval` by default" in fixer
        assert "two rendered candidates" in fixer
        assert "ten elapsed minutes" in fixer
        assert "If the MCP tool fails, use the local renderer directly" in fixer

        critique = read_skill("dataviz-critique", surface)
        assert "## Optional structured repair brief" in critique
        assert "only when the user explicitly requests an audited workflow" in critique

        visualizer = read_skill("karthik-data-visualization", surface)
        assert "Do not write a design contract in the default output-first" in visualizer
        assert "do not delay chart code for a contract or plan audit" in visualizer


def test_public_entrypoint_explains_installation_and_renderer_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Start here: agents and LLMs" in readme
    assert "Installing the skills does not register the MCP server" in readme
    assert "chooses ggplot2 first" in readme
    assert "Use Matplotlib only" in readme
    assert "git clone https://github.com/skthewimp/karthik-data-visualization-skill.git" in readme

    sync_help = (ROOT / "sync.sh").read_text(encoding="utf-8")
    assert "--surface all|codex|claude" in sync_help


def test_maintainer_publish_rule_is_persistent_and_third_party_safe() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "completed changes" in agents
    assert "push it to GitHub" in agents
    assert "Third-party clones and forks must not push" in agents
    assert "Do not force-push" in agents
    assert "An explicit instruction not to commit or push overrides" in agents
    assert "Read and follow [`AGENTS.md`](AGENTS.md)" in claude

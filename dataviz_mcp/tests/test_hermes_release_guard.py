from __future__ import annotations

import hashlib
import json
from pathlib import Path

from dataviz_mcp.hermes_release_guard import (
    find_released_artifact,
    is_chart_repair_request,
    on_pre_llm_call,
    on_transform_llm_output,
    register,
)


def _write_case(root: Path, session: str, artifact: Path, **changes) -> Path:
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    data = {
        "session_id": session,
        "creator": "main:creator",
        "state": "user_review",
        "best_candidate": {
            "verdict": "Send",
            "artifact": {"path": str(artifact), "sha256": digest},
        },
        "evaluations": [
            {
                "verdict": "Send",
                "reviewer": "reviewer-1",
                "reviewer_role": "independent",
                "codes": [],
                "required_actions": [],
            }
        ],
    }
    data.update(changes)
    case = root / "cases" / "case-1"
    case.mkdir(parents=True)
    (case / "case.json").write_text(json.dumps(data), encoding="utf-8")
    return case


def test_detects_generic_chart_repairs_without_matching_one_domain():
    assert is_chart_repair_request("Please redesign this rainfall chart")
    assert is_chart_repair_request("The dashboard legend is still wrong", continuing=True)
    assert not is_chart_repair_request("Explain what this chart says")
    assert not is_chart_repair_request("This is good")
    assert not is_chart_repair_request("Improve this portrait")


def test_plugin_registers_both_enforcement_hooks():
    class Context:
        hooks = []

        def register_hook(self, name, callback):
            self.hooks.append((name, callback))

    context = Context()
    register(context)
    assert [name for name, _ in context.hooks] == [
        "pre_llm_call",
        "transform_llm_output",
    ]


def test_release_requires_matching_session_state_review_and_hash(tmp_path):
    artifact = tmp_path / "chart.png"
    artifact.write_bytes(b"reviewed chart")
    cases = tmp_path / "cases"
    _write_case(tmp_path, "guard-session", artifact)

    assert (
        find_released_artifact(
            "guard-session", f"MEDIA:{artifact}", root=cases
        )
        == artifact
    )
    assert find_released_artifact("other-session", f"MEDIA:{artifact}", root=cases) is None

    altered = tmp_path / "altered.png"
    altered.write_bytes(b"different chart")
    assert find_released_artifact("guard-session", f"MEDIA:{altered}", root=cases) is None


def test_release_rejects_non_send_or_non_independent_review(tmp_path):
    artifact = tmp_path / "chart.png"
    artifact.write_bytes(b"chart")
    cases = tmp_path / "cases"
    case = _write_case(tmp_path, "guard-session", artifact)
    data = json.loads((case / "case.json").read_text())
    data["state"] = "revise"
    (case / "case.json").write_text(json.dumps(data))
    assert find_released_artifact("guard-session", f"MEDIA:{artifact}", root=cases) is None

    data["state"] = "user_review"
    data["evaluations"][0]["reviewer_role"] = "creator"
    (case / "case.json").write_text(json.dumps(data))
    assert find_released_artifact("guard-session", f"MEDIA:{artifact}", root=cases) is None


def test_hooks_fail_closed_when_agent_skips_case(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    context = on_pre_llm_call(
        session_id="hermes-session-skip",
        user_message="Fix this sales chart",
    )
    assert context and "--session 'hermes-guard-" in context["context"]
    blocked = on_transform_llm_output(
        session_id="hermes-session-skip",
        response_text="Done. MEDIA:/tmp/unreviewed.png",
    )
    assert blocked and blocked.startswith("Chart withheld")


def test_hooks_allow_exact_reviewed_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    context = on_pre_llm_call(
        session_id="hermes-session-pass",
        user_message="Improve this population graph",
    )
    case_session = context["context"].split("--session '", 1)[1].split("'", 1)[0]
    artifact = tmp_path / "reviewed.png"
    artifact.write_bytes(b"reviewed")
    _write_case(tmp_path / "dataviz-fix", case_session, artifact)

    assert (
        on_transform_llm_output(
            session_id="hermes-session-pass",
            response_text=f"Repaired chart.\nMEDIA:{artifact}",
        )
        is None
    )

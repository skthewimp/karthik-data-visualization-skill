import hashlib
from pathlib import Path

from dataviz_mcp.public_repair_contract import (
    CREATOR_INSTRUCTIONS,
    DEFAULT_INDEPENDENT_REVIEW,
    DEFAULT_REPAIR_STAGES,
    DELIVERY_AUDIT_INSTRUCTIONS,
    PLAN_AUDITOR_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    PUBLIC_CREATOR_SKILL_FINGERPRINT,
    PUBLIC_CREATOR_SKILL_PATHS,
    PUBLIC_CREATOR_SKILL_SOURCE,
    PUBLIC_CREATOR_SKILL_SOURCES,
    REPAIR_PLAN_SCHEMA,
    REVIEWER_INSTRUCTIONS,
    _skill_body,
)


def test_public_repair_contract_is_output_first_by_default() -> None:
    creator = " ".join(CREATOR_INSTRUCTIONS.split())
    assert DEFAULT_REPAIR_STAGES == ("creator",)
    assert DEFAULT_INDEPENDENT_REVIEW is False
    assert PUBLIC_CREATOR_SKILL_SOURCE == "repository"
    assert PUBLIC_CREATOR_SKILL_SOURCES == PUBLIC_CREATOR_SKILL_PATHS
    assert "single creator in the public chart-repair runtime" in creator
    assert "Do not try to invoke them, spawn another agent" in creator
    assert "/mnt/data/repaired.png" in creator
    assert "optional audited stage" in PLANNER_INSTRUCTIONS
    assert "optional audited stage" in PLAN_AUDITOR_INSTRUCTIONS
    assert "optional audited stage" in REVIEWER_INSTRUCTIONS
    assert "optional audited stage" in DELIVERY_AUDIT_INSTRUCTIONS


def test_public_creator_bundle_is_built_from_every_canonical_skill() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    for relative in PUBLIC_CREATOR_SKILL_PATHS:
        source = _skill_body(
            (repository_root / relative).read_text(encoding="utf-8")
        )
        assert f"## Canonical skill source: {relative}" in CREATOR_INSTRUCTIONS
        assert source in CREATOR_INSTRUCTIONS
    assert PUBLIC_CREATOR_SKILL_FINGERPRINT == hashlib.sha256(
        CREATOR_INSTRUCTIONS.encode("utf-8")
    ).hexdigest()


def test_audited_plan_schema_does_not_require_one_chart_family() -> None:
    inventory = REPAIR_PLAN_SCHEMA["properties"]["source_inventory"]
    assert "displayed_content" in inventory["properties"]
    assert "time_periods" not in inventory["properties"]
    layout = REPAIR_PLAN_SCHEMA["properties"]["layout_plan"]
    assert set(layout["required"]) == {"delivery_condition", "regions", "layout_risks"}

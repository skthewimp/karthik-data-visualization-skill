from dataviz_mcp.public_repair_contract import (
    CREATOR_INSTRUCTIONS,
    DEFAULT_INDEPENDENT_REVIEW,
    DEFAULT_REPAIR_STAGES,
    DELIVERY_AUDIT_INSTRUCTIONS,
    PLAN_AUDITOR_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    REPAIR_PLAN_SCHEMA,
    REVIEWER_INSTRUCTIONS,
)


def test_public_repair_contract_is_output_first_by_default() -> None:
    creator = " ".join(CREATOR_INSTRUCTIONS.split())
    assert DEFAULT_REPAIR_STAGES == ("creator",)
    assert DEFAULT_INDEPENDENT_REVIEW is False
    assert "Build and return a real repaired artifact" in creator
    assert "Never invent missing values" in creator
    assert "Do not use image generation" in creator
    assert "Do not impose a fixed candidate count or elapsed-time limit" in creator
    assert "run one concise internal critique" in creator
    assert "do not fill a quota" in creator
    assert "typography hierarchy and whether any identification or scale" in creator
    assert "one focused revision pass" in creator
    assert "Do not start an independent review or recursive critique loop" in creator
    assert "optional audited stage" in PLANNER_INSTRUCTIONS
    assert "optional audited stage" in PLAN_AUDITOR_INSTRUCTIONS
    assert "optional audited stage" in REVIEWER_INSTRUCTIONS
    assert "optional audited stage" in DELIVERY_AUDIT_INSTRUCTIONS


def test_audited_plan_schema_does_not_require_one_chart_family() -> None:
    inventory = REPAIR_PLAN_SCHEMA["properties"]["source_inventory"]
    assert "displayed_content" in inventory["properties"]
    assert "time_periods" not in inventory["properties"]
    layout = REPAIR_PLAN_SCHEMA["properties"]["layout_plan"]
    assert set(layout["required"]) == {"delivery_condition", "regions", "layout_risks"}

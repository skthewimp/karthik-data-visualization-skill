from dataviz_mcp.public_repair_contract import (
    CREATOR_INSTRUCTIONS,
    DEFAULT_INDEPENDENT_REVIEW,
    DEFAULT_REPAIR_STAGES,
    DELIVERY_AUDIT_INSTRUCTIONS,
    PLAN_AUDITOR_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    REVIEWER_INSTRUCTIONS,
)


def test_public_repair_contract_is_output_first_by_default() -> None:
    assert DEFAULT_REPAIR_STAGES == ("creator",)
    assert DEFAULT_INDEPENDENT_REVIEW is False
    assert "Build and return a real repaired artifact" in CREATOR_INSTRUCTIONS
    assert "Never invent missing values" in CREATOR_INSTRUCTIONS
    assert "Do not use image generation" in CREATOR_INSTRUCTIONS
    assert "Do not impose a fixed candidate count or elapsed-time limit" in CREATOR_INSTRUCTIONS
    assert "run one concise internal critique" in CREATOR_INSTRUCTIONS
    assert "typography hierarchy and whether any identification or scale" in CREATOR_INSTRUCTIONS
    assert "one focused revision pass" in CREATOR_INSTRUCTIONS
    assert "Do not start an independent review or recursive" in CREATOR_INSTRUCTIONS
    assert "critique loop" in CREATOR_INSTRUCTIONS
    assert "optional audited stage" in PLANNER_INSTRUCTIONS
    assert "optional audited stage" in PLAN_AUDITOR_INSTRUCTIONS
    assert "optional audited stage" in REVIEWER_INSTRUCTIONS
    assert "optional audited stage" in DELIVERY_AUDIT_INSTRUCTIONS

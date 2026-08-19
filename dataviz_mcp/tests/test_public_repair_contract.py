from dataviz_mcp.public_repair_contract import (
    CREATOR_INSTRUCTIONS,
    DELIVERY_AUDIT_INSTRUCTIONS,
    DELIVERY_AUDIT_SCHEMA,
    PLAN_AUDIT_SCHEMA,
    PLAN_AUDITOR_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    REPAIR_PLAN_SCHEMA,
    REVIEWER_INSTRUCTIONS,
    REVIEW_SCHEMA,
)


def test_public_repair_contract_preserves_the_screenshot_evidence_boundary() -> None:
    assert "Inventory the source before diagnosing it" in PLANNER_INSTRUCTIONS
    assert "source_inventory" in REPAIR_PLAN_SCHEMA["required"]
    assert "layout_plan" in REPAIR_PLAN_SCHEMA["required"]
    assert "acceptance_checks" in REPAIR_PLAN_SCHEMA["required"]
    assert REPAIR_PLAN_SCHEMA["additionalProperties"] is False
    assert "independent pre-build auditor" in PLAN_AUDITOR_INSTRUCTIONS
    assert "inventory_coverage" in PLAN_AUDIT_SCHEMA["required"]
    assert "diagnosis_coverage" in PLAN_AUDIT_SCHEMA["required"]
    assert "preservation_coverage" in PLAN_AUDIT_SCHEMA["required"]
    assert "layout_coverage" in PLAN_AUDIT_SCHEMA["required"]
    assert PLAN_AUDIT_SCHEMA["additionalProperties"] is False
    assert "Never invent missing values" in CREATOR_INSTRUCTIONS
    assert "Do not use image generation" in CREATOR_INSTRUCTIONS
    assert "perceptually unchanged chart is a failed repair" in CREATOR_INSTRUCTIONS
    assert "fresh, independent reviewer" in REVIEWER_INSTRUCTIONS
    assert "material_improvement" in REVIEW_SCHEMA["required"]
    assert "material_changes" in REVIEW_SCHEMA["required"]
    assert "plan_compliance" in REVIEW_SCHEMA["required"]
    assert "regressions" in REVIEW_SCHEMA["required"]
    assert "delivery" in REVIEW_SCHEMA["required"]
    assert REVIEW_SCHEMA["additionalProperties"] is False
    assert "axes or ticks intruding into section headings" in DELIVERY_AUDIT_INSTRUCTIONS
    assert "visual_integrity" in DELIVERY_AUDIT_SCHEMA["required"]
    assert DELIVERY_AUDIT_SCHEMA["additionalProperties"] is False

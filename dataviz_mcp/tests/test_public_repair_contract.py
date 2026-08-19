from dataviz_mcp.public_repair_contract import (
    CREATOR_INSTRUCTIONS,
    REVIEWER_INSTRUCTIONS,
    REVIEW_SCHEMA,
)


def test_public_repair_contract_preserves_the_screenshot_evidence_boundary() -> None:
    assert "Never invent missing values" in CREATOR_INSTRUCTIONS
    assert "Do not use image generation" in CREATOR_INSTRUCTIONS
    assert "fresh, independent reviewer" in REVIEWER_INSTRUCTIONS
    assert REVIEW_SCHEMA["additionalProperties"] is False

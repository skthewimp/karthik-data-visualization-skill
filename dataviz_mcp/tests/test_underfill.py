from dataviz_mcp.inspection import _underfill_defect


def test_underfilled_canvas_flagged_low_when_only_empty():
    defect = _underfill_defect(0.12, has_undersized_text=False)
    assert defect is not None
    assert defect["code"] == "UNDERFILLED_CANVAS"
    assert defect["severity"] == "low"


def test_underfilled_canvas_escalates_when_text_also_tiny():
    defect = _underfill_defect(0.12, has_undersized_text=True)
    assert defect["severity"] == "medium"  # empty + tiny = the mobile-table redesign case


def test_full_canvas_is_not_flagged():
    assert _underfill_defect(0.55, has_undersized_text=True) is None


def test_missing_ratio_is_not_flagged():
    assert _underfill_defect(None, has_undersized_text=True) is None

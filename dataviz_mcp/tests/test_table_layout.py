import pytest

from dataviz_mcp.table_layout import recommend_table_layout


def test_wrapping_pagination_preserves_content_and_type():
    cols = [{"header": "Name", "identifier": True, "max_width_px": 120,
             "cells": ["A much longer name", "B", "C", "D"]}]
    cols += [{"header": "Metric " + str(i), "cells": ["100", "20", "3", "0"]}
             for i in range(4)]
    out = recommend_table_layout(cols, delivery={"max_width_px": 300, "max_height_px": 180})
    assert out["status"] == "split"
    assert out["body_pt"] == 11
    assert out["row_heights_px"][0] > out["row_heights_px"][1]
    seen = set()
    for page in out["pages"]:
        assert 0 in page["columns"]
        assert page["width_px"] <= 300 and page["height_px"] <= 180
        for c in page["columns"]:
            for r in range(*page["rows"]):
                seen.add((c, r))
    assert seen == {(c, r) for c in range(5) for r in range(4)}
    assert out["cells"][0][0].replace("\n", " ") == cols[0]["cells"][0]


def test_display_floor_and_unbreakable_content():
    out = recommend_table_layout([{"header": "Value", "cells": ["W" * 100]}],
        delivery={"display_width_px": 400, "minimum_text_px": 16, "max_width_px": 1600})
    assert out["status"] == "cannot_fit"
    assert out["body_pt"] >= 11
    assert out["cells"][0][0] == "W" * 100


def test_treatment_requires_shared_scale_semantics_not_column_counts():
    cols = [{"header": "Value", "cells": ["-3", "10"]}]
    with pytest.raises(ValueError, match="commensurability"):
        recommend_table_layout(cols, treatment={"kind": "shading", "scope": "table"})
    plan = {"kind": "bar", "scope": "column", "domain": [-3, 10], "baseline": 0}
    out = recommend_table_layout(cols * 4, treatment=plan)
    assert out["treatment"] == plan

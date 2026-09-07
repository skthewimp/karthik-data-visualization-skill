"""Bridge from a recommend_table_layout plan to a rendered table via the shared R constructor.

The constructor (``r/table_from_plan.R``) applies the plan's measured geometry verbatim, so a
build model consumes the reservation instead of re-deriving row positions and the frame - the
failure mode where a hand-rolled table ignores measured heights and clips.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONSTRUCTOR = Path(__file__).parent / "r" / "table_from_plan.R"


def table_constructor_path() -> str:
    """Absolute path of the shared R constructor, for a build script to ``source()``."""
    return str(_CONSTRUCTOR.resolve())


def write_table_build_source(
    plan: dict[str, Any] | str | Path,
    out_path: str | Path,
    page: int = 1,
    build_function: str = "build_table",
) -> str:
    """Write an .R build file that renders ``plan`` through the shared constructor.

    ``plan`` is a recommend_table_layout result (dict) or a path to its JSON. Returns the build
    file path, ready for ``render_and_inspect_chart(..., content="table", build_function=...)``.
    """
    out_path = Path(out_path)
    if isinstance(plan, dict):
        plan_path = out_path.with_suffix(".plan.json")
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
    else:
        plan_path = Path(plan)
    if page < 1:
        raise ValueError("page is 1-based and must be >= 1")
    out_path.write_text(
        f"source({json.dumps(table_constructor_path())})\n"
        f"{build_function} <- function() "
        f"build_table_from_plan({json.dumps(str(plan_path.resolve()))}, {int(page)}L)\n",
        encoding="utf-8",
    )
    return str(out_path)

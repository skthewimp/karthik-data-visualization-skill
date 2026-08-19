from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REGRESSION_FAMILIES = (
    "illegible heatmaps and redundant colour encodings",
    "slopegraph selection, aspect ratio, and endpoint labels",
    "redundant axes after direct labelling",
    "incomplete legend replacement",
    "whitespace and label-to-mark distance",
    "title, subtitle, panel-heading, and legend collisions",
    "low-contrast colours",
    "ambiguous measures, units, periods, universes, and claims",
    "unsupported reconstruction of screenshot-only data",
    "generic Matplotlib appearance when ggplot2 was available",
)


def load_case_corpus(*roots: str | Path) -> list[dict[str, Any]]:
    """Load repair cases read-only, de-duplicated by case id."""
    cases: dict[str, dict[str, Any]] = {}
    for root_value in roots:
        root = Path(root_value).expanduser().resolve()
        if not root.is_dir():
            continue
        for case_path in sorted(root.glob("cases/*/case.json")):
            try:
                case = json.loads(case_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(case, dict):
                continue
            case_id = str(case.get("case_id") or case_path.parent.name)
            cases[case_id] = {**case, "_case_path": str(case_path)}
    return [cases[key] for key in sorted(cases)]


def benchmark_case_records(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize workflow evidence without judging old artifacts retroactively."""
    cycles = [len(case.get("evaluations", [])) for case in cases]
    complete = [case for case in cases if case.get("state") in ("accepted", "accepted_with_override")]
    send_events = [
        evaluation
        for case in cases
        for evaluation in case.get("evaluations", [])
        if evaluation.get("verdict") == "Send"
    ]
    return {
        "cases": len(cases),
        "accepted_cases": len(complete),
        "iterations": sum(len(case.get("iterations", [])) for case in cases),
        "evaluation_cycles": sum(cycles),
        "mean_evaluation_cycles": round(sum(cycles) / len(cycles), 3) if cycles else 0.0,
        "cases_with_critique_before_first_build": sum(
            bool(case.get("critiques"))
            and bool(case.get("iterations"))
            and case["iterations"][0].get("critique") == case["critiques"][0].get("number")
            for case in cases
        ),
        "cases_with_design_contract": sum(bool(case.get("design_contracts")) for case in cases),
        "send_events": len(send_events),
        "send_with_open_actions": sum(bool(item.get("open_required_actions")) for item in send_events),
        "regression_families": list(REGRESSION_FAMILIES),
        "source_paths": [case["_case_path"] for case in cases],
        "interpretation": (
            "Historical cases are a baseline corpus. Replay through schema 14 is required to "
            "measure false-Send rate and cycle reduction; this summary does not relabel them."
        ),
    }


def compare_benchmark_runs(
    baseline_cases: list[dict[str, Any]], replay_cases: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare matched corpus runs without silently treating missing replays as wins."""
    baseline_by_id = {str(case.get("case_id")): case for case in baseline_cases}
    replay_by_id = {str(case.get("case_id")): case for case in replay_cases}
    matched_ids = sorted(baseline_by_id.keys() & replay_by_id.keys())
    missing_replays = sorted(baseline_by_id.keys() - replay_by_id.keys())

    def cycle_count(case: dict[str, Any]) -> int:
        return len(case.get("evaluations", []))

    def false_sends(case: dict[str, Any]) -> int:
        return sum(
            evaluation.get("verdict") == "Send"
            and (
                bool(evaluation.get("open_required_actions"))
                or any(
                    item.get("result") != "Pass"
                    for field in (
                        "semantic_checks",
                        "carry_forward_checks",
                        "acceptance_checks",
                        "critique_checks",
                    )
                    for item in (
                        evaluation.get(field, {}).values()
                        if isinstance(evaluation.get(field), dict)
                        else evaluation.get(field, [])
                    )
                )
            )
            for evaluation in case.get("evaluations", [])
        )

    baseline_cycles = sum(cycle_count(baseline_by_id[item]) for item in matched_ids)
    replay_cycles = sum(cycle_count(replay_by_id[item]) for item in matched_ids)
    baseline_false_sends = sum(false_sends(baseline_by_id[item]) for item in matched_ids)
    replay_false_sends = sum(false_sends(replay_by_id[item]) for item in matched_ids)
    complete = bool(matched_ids) and not missing_replays
    return {
        "baseline_cases": len(baseline_by_id),
        "matched_cases": len(matched_ids),
        "missing_replays": missing_replays,
        "baseline_evaluation_cycles": baseline_cycles,
        "replay_evaluation_cycles": replay_cycles,
        "cycle_reduction": baseline_cycles - replay_cycles,
        "baseline_false_sends": baseline_false_sends,
        "replay_false_sends": replay_false_sends,
        "fewer_cycles": complete and replay_cycles < baseline_cycles,
        "false_passes_not_increased": complete and replay_false_sends <= baseline_false_sends,
        "acceptance_met": (
            complete
            and replay_cycles < baseline_cycles
            and replay_false_sends <= baseline_false_sends
        ),
    }

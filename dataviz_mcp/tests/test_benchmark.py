from __future__ import annotations

import json
from pathlib import Path

import pytest

from dataviz_mcp.benchmark import (
    REGRESSION_FAMILIES,
    benchmark_case_records,
    compare_benchmark_runs,
    load_case_corpus,
)


def test_corpus_loader_is_read_only_and_deduplicates_case_ids(tmp_path: Path) -> None:
    roots = [tmp_path / "one", tmp_path / "two"]
    for root in roots:
        case_dir = root / "cases" / "case-a"
        case_dir.mkdir(parents=True)
        (case_dir / "case.json").write_text(
            json.dumps({"case_id": "case-a", "iterations": [], "evaluations": []}),
            encoding="utf-8",
        )
    before = [(path, path.stat().st_mtime_ns) for path in tmp_path.rglob("case.json")]
    cases = load_case_corpus(*roots)
    after = [(path, path.stat().st_mtime_ns) for path in tmp_path.rglob("case.json")]
    assert len(cases) == 1
    assert before == after
    report = benchmark_case_records(cases)
    assert report["cases"] == 1
    assert report["regression_families"] == list(REGRESSION_FAMILIES)
    assert len(report["regression_families"]) == 10


def test_benchmark_comparison_requires_complete_replay_and_no_false_pass_increase() -> None:
    baseline = [
        {"case_id": "a", "evaluations": [{"verdict": "Revise"}, {"verdict": "Send"}]},
        {"case_id": "b", "evaluations": [{"verdict": "Revise"}, {"verdict": "Send"}]},
    ]
    replay = [
        {"case_id": "a", "evaluations": [{"verdict": "Send", "open_required_actions": []}]},
        {"case_id": "b", "evaluations": [{"verdict": "Send", "open_required_actions": []}]},
    ]
    comparison = compare_benchmark_runs(baseline, replay)
    assert comparison["cycle_reduction"] == 2
    assert comparison["false_passes_not_increased"] is True
    assert comparison["acceptance_met"] is True
    assert compare_benchmark_runs(baseline, replay[:1])["acceptance_met"] is False


@pytest.mark.skipif(
    not Path("/home/karthik/.hermes/dataviz-fix/cases").is_dir(),
    reason="Hermes benchmark corpus is not present",
)
def test_all_available_hermes_cases_form_the_local_benchmark_corpus() -> None:
    cases = load_case_corpus(
        "/home/karthik/.hermes/dataviz-fix",
        "/home/karthik/.hermes/dataviz-fix-cases",
    )
    report = benchmark_case_records(cases)
    assert report["cases"] >= 27
    assert len(report["source_paths"]) == report["cases"]

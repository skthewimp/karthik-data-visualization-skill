#!/usr/bin/env python3
"""Persist dataviz repair cases without deleting or overwriting artifacts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from secrets import token_hex


CLASSIFICATIONS = (
    "execution-miss",
    "missing-rule",
    "ambiguous-rule",
    "conflicting-rule",
    "tooling",
    "input-data",
)

VERDICTS = ("Send", "Revise", "Redesign", "Not evaluable")
GATE_NAMES = (
    "Evidence",
    "Question",
    "Insight",
    "Visual reasoning",
    "Information fit",
    "Delivery",
)
GATE_RESULTS = ("Pass", "Concern", "Fail", "Unknown")
GATE_RESULT_ALIASES = {"match": "Pass", "partial": "Concern", "mismatch": "Fail"}
CORE_GATE_NAMES = ("Evidence", "Visual reasoning", "Information fit", "Delivery")
RELEASE_CHECK_NAMES = (
    "Visual integrity",
    "Relationship traceability",
    "Spatial economy",
    "Encoding semantics",
    "Delivery robustness",
)
PRESENTATION_CHECK_NAMES = (
    "Colour distinction",
    "Copy style",
)
DELIVERABLE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".pdf")
SCHEMA_VERSION = 16
DEFAULT_MAX_ITERATIONS = None
DEFAULT_MAX_STALLED_EVALUATIONS = None
ACTIVE_STATES = (
    "critique",
    "design",
    "build",
    "blind_review",
    "context_reveal",
    "revise",
    "redesign",
    "user_review",
)
PAUSED_STATES = ("blocked", "stopped")
TERMINAL_STATES = ("accepted", "accepted_with_override")
STOP_KINDS = (
    "user_stop",
    "iteration_budget",
    "time_budget",
    "token_budget",
    "cost_budget",
    "no_progress",
    "missing_context",
    "missing_evidence",
    "renderer_failure",
    "other",
)
RESULT_RANK = {"Fail": 0, "Unknown": 0, "Concern": 1, "Pass": 2}
CONTEXT_FIELDS = (
    "audience",
    "purpose",
    "question",
    "hypothesis",
    "message",
    "medium",
    "dimensions",
    "expansion_available",
    "source_notes",
    "preserve",
    "accessibility",
    "brand",
    "tooling",
    "output_constraints",
)
CONTEXT_SOURCES = ("user", "inferred", "unknown")
SEMANTIC_DIMENSIONS = (
    "measure",
    "time_context",
    "universe_denominator",
    "claim_strength",
    "audience_units",
)
SEMANTIC_PREFLIGHT_RESULTS = ("clear", "repair", "unknown")
CRITIQUE_SEVERITIES = ("fatal", "major", "minor")
INTERVENTIONS = ("repair", "redesign")
RENDERERS = ("ggplot2", "matplotlib")
BUDGET_STOP_KINDS = (
    "iteration_budget",
    "time_budget",
    "token_budget",
    "cost_budget",
)
_ACTION_TOPIC_PATTERNS = {
    "delivery-scale": r"\b(delivery|chat|preview|display|canvas|viewport|width|size|scale|thumbnail|compact)\b",
    "collision": r"\b(collid|collision|overlap|occlud|touch|crowd|intersect)\w*\b",
    "label-association": r"\b(direct label|label.{0,20}(mark|bar|point|line|series)|traceab|association|distance)\b",
    "legend": r"\b(legend|key)\b",
    "axis": r"\b(axis|axes|tick)\b",
    "title": r"\btitle\b",
    "subtitle": r"\bsubtitle\b",
    "source-note": r"\b(source|footnote|footer|note)\b",
    "contrast": r"\b(contrast|colour|color|grayscale|vision deficien)\w*\b",
    "whitespace": r"\b(whitespace|white space|unused space|plot utilization|plot utilisation)\b",
    "period": r"\b(period|date|year|month|quarter|time frame|timeframe)\b",
    "measure": r"\b(measure|metric|unit|rate|count|percent|percentage)\b",
    "universe": r"\b(universe|denominator|population|sample|scope)\b",
    "claim": r"\b(claim|causal|comparison|baseline)\b",
}
_ACTION_STOP_WORDS = {
    "a", "all", "an", "and", "are", "as", "at", "be", "by", "current",
    "does", "for", "from", "in", "is", "it", "named", "of", "on", "or",
    "pass", "reader", "readers", "required", "that", "the", "their", "this",
    "to", "with",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def root_dir() -> Path:
    override = os.getenv("DATAVIZ_FIX_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".local" / "share" / "dataviz-fix"


def safe_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-.")
    return (clean or "default")[:120]


def csv_items(value: str) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def parse_gate_results(value: str) -> dict[str, str]:
    aliases = {re.sub(r"[^a-z]+", "", name.lower()): name for name in GATE_NAMES}
    results: dict[str, str] = {}
    for item in csv_items(value):
        raw_name, separator, raw_result = item.partition("=")
        if not separator:
            raise SystemExit(f"Invalid gate result {item!r}; expected Gate=Result")
        name = aliases.get(re.sub(r"[^a-z]+", "", raw_name.lower()))
        if name is None:
            raise SystemExit(f"Unknown gate {raw_name!r}; choose from {', '.join(GATE_NAMES)}")
        result = next((choice for choice in GATE_RESULTS if choice.lower() == raw_result.strip().lower()), None)
        if result is None:
            raise SystemExit(f"Unknown result {raw_result!r}; choose from {', '.join(GATE_RESULTS)}")
        if name in results:
            raise SystemExit(f"Duplicate gate result for {name}")
        results[name] = result
    missing = [name for name in GATE_NAMES if name not in results]
    if missing:
        raise SystemExit(f"Missing gate results: {', '.join(missing)}")
    return {name: results[name] for name in GATE_NAMES}


def validate_ratings(
    raw: object,
    names: tuple[str, ...],
    field: str,
    include_required: bool = False,
    require_stress_test: bool = False,
) -> dict[str, dict[str, object]]:
    if not isinstance(raw, dict):
        raise SystemExit(f"Review report {field!r} must be an object")
    ratings: dict[str, dict[str, object]] = {}
    for name in names:
        item = raw.get(name)
        if not isinstance(item, dict):
            raise SystemExit(f"Review report missing {field}.{name}")
        result = item.get("result")
        if isinstance(result, str):
            result = GATE_RESULT_ALIASES.get(result.strip().lower(), result)
        evidence = item.get("evidence")
        if result not in GATE_RESULTS:
            raise SystemExit(
                f"Invalid {field}.{name}.result {result!r}; choose from {', '.join(GATE_RESULTS)}"
            )
        if not isinstance(evidence, str) or not evidence.strip():
            raise SystemExit(f"Review report {field}.{name}.evidence must be non-empty")
        rating: dict[str, object] = {"result": result, "evidence": evidence.strip()}
        if require_stress_test:
            stress_test = item.get("stress_test")
            if not isinstance(stress_test, str) or not stress_test.strip():
                raise SystemExit(
                    f"Review report {field}.{name}.stress_test must name the most failure-prone element, pair, or region inspected"
                )
            rating["stress_test"] = stress_test.strip()
        if include_required:
            required = item.get("required")
            if not isinstance(required, bool):
                raise SystemExit(f"Review report {field}.{name}.required must be true or false")
            if name in CORE_GATE_NAMES and not required:
                raise SystemExit(f"Core artifact gate {name} must be required")
            if not required and result != "Unknown":
                raise SystemExit(f"Non-required gate {name} must be Unknown, not {result}")
            rating["required"] = required
        ratings[name] = rating
    extra = sorted(set(raw) - set(names))
    if extra:
        raise SystemExit(f"Unknown {field} entries: {', '.join(extra)}")
    return ratings


def nonempty_text(raw: object, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise SystemExit(f"Review report {field!r} must be non-empty text")
    return raw.strip()


def validate_blind_semantics(raw: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw, dict):
        raise SystemExit("Blind response 'semantics' must be an object")
    semantics: dict[str, dict[str, str]] = {}
    for name in SEMANTIC_DIMENSIONS:
        item = raw.get(name)
        if not isinstance(item, dict):
            raise SystemExit(f"Blind response missing semantics.{name}")
        semantics[name] = {
            "reading": nonempty_text(item.get("reading"), f"semantics.{name}.reading"),
            "uncertainty": nonempty_text(
                item.get("uncertainty"), f"semantics.{name}.uncertainty"
            ),
        }
    extra = sorted(set(raw) - set(SEMANTIC_DIMENSIONS))
    if extra:
        raise SystemExit(f"Unknown blind semantics entries: {', '.join(extra)}")
    return semantics


def validate_blind_response(raw: object, iteration: dict) -> dict:
    if not isinstance(raw, dict):
        raise SystemExit("Blind response must be a JSON object")
    reviewer = nonempty_text(raw.get("reviewer"), "blind_response.reviewer")
    if raw.get("iteration") != iteration["number"]:
        raise SystemExit("Blind response iteration does not match the recorded iteration")
    if raw.get("artifact_sha256") != iteration["artifact"]["sha256"]:
        raise SystemExit("Blind response artifact_sha256 does not match the recorded iteration")
    semantics = raw.get("semantics")
    if semantics is None and not iteration.get("semantic_preflight"):
        # Legacy iterations created before semantic preflight binding remain reviewable.
        semantics = {
            name: {
                "reading": "Not recorded in legacy blind response",
                "uncertainty": "Unknown because this iteration predates structured blind semantics",
            }
            for name in SEMANTIC_DIMENSIONS
        }
    return {
        "reviewer": reviewer,
        "expert": nonempty_text(raw.get("expert"), "blind_response.expert"),
        "audience": nonempty_text(raw.get("audience"), "blind_response.audience"),
        "semantics": validate_blind_semantics(semantics),
    }


def validate_semantic_checks(raw: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw, dict):
        raise SystemExit("Review report 'semantic_checks' must be an object")
    checks: dict[str, dict[str, str]] = {}
    for name in SEMANTIC_DIMENSIONS:
        item = raw.get(name)
        if not isinstance(item, dict):
            raise SystemExit(f"Review report missing semantic_checks.{name}")
        result = item.get("result")
        if result not in GATE_RESULTS:
            raise SystemExit(
                f"Invalid semantic_checks.{name}.result {result!r}; "
                f"choose from {', '.join(GATE_RESULTS)}"
            )
        checks[name] = {
            "result": result,
            "misleading_interpretation": nonempty_text(
                item.get("misleading_interpretation"),
                f"semantic_checks.{name}.misleading_interpretation",
            ),
            "defensible_interpretation": nonempty_text(
                item.get("defensible_interpretation"),
                f"semantic_checks.{name}.defensible_interpretation",
            ),
            "evidence": nonempty_text(
                item.get("evidence"), f"semantic_checks.{name}.evidence"
            ),
        }
    extra = sorted(set(raw) - set(SEMANTIC_DIMENSIONS))
    if extra:
        raise SystemExit(f"Unknown semantic_checks entries: {', '.join(extra)}")
    return checks


def validate_semantic_preflight(raw: object, context_version: int) -> dict:
    if not isinstance(raw, dict):
        raise SystemExit("Semantic preflight report must be a JSON object")
    reported_version = raw.get("context_version")
    if reported_version != context_version:
        raise SystemExit(
            f"Semantic preflight context_version must be {context_version}, "
            f"not {reported_version!r}"
        )
    dimensions = raw.get("dimensions")
    if not isinstance(dimensions, dict):
        raise SystemExit("Semantic preflight report 'dimensions' must be an object")
    validated: dict[str, dict[str, str]] = {}
    for name in SEMANTIC_DIMENSIONS:
        item = dimensions.get(name)
        if not isinstance(item, dict):
            raise SystemExit(f"Semantic preflight missing dimensions.{name}")
        result = item.get("result")
        if result not in SEMANTIC_PREFLIGHT_RESULTS:
            raise SystemExit(
                f"Invalid dimensions.{name}.result {result!r}; "
                f"choose from {', '.join(SEMANTIC_PREFLIGHT_RESULTS)}"
            )
        validated[name] = {
            "result": result,
            "observed": nonempty_text(item.get("observed"), f"dimensions.{name}.observed"),
            "risk": nonempty_text(item.get("risk"), f"dimensions.{name}.risk"),
            "required": nonempty_text(item.get("required"), f"dimensions.{name}.required"),
        }
    extra = sorted(set(dimensions) - set(SEMANTIC_DIMENSIONS))
    if extra:
        raise SystemExit(f"Unknown semantic preflight dimensions: {', '.join(extra)}")
    return {"context_version": context_version, "dimensions": validated}


def text_list(raw: object, field: str, minimum: int = 0) -> list[str]:
    if not isinstance(raw, list) or any(
        not isinstance(item, str) or not item.strip() for item in raw
    ):
        raise SystemExit(f"{field} must be a list of non-empty strings")
    values = [item.strip() for item in raw]
    if len(values) < minimum:
        raise SystemExit(f"{field} requires at least {minimum} item(s)")
    return values


def validate_critique_report(raw: object, context_version: int) -> dict:
    """Validate the mandatory dataviz-critique repair brief."""
    if not isinstance(raw, dict):
        raise SystemExit("Critique report must be a JSON object")
    if raw.get("context_version") != context_version:
        raise SystemExit(f"Critique context_version must be {context_version}")
    findings_raw = raw.get("findings")
    if not isinstance(findings_raw, dict):
        raise SystemExit("Critique report findings must be an object")
    findings: dict[str, list[dict]] = {}
    ids: set[str] = set()
    for severity in CRITIQUE_SEVERITIES:
        items = findings_raw.get(severity)
        if not isinstance(items, list):
            raise SystemExit(f"Critique findings.{severity} must be a list")
        findings[severity] = []
        for item in items:
            if not isinstance(item, dict):
                raise SystemExit(f"Each {severity} critique finding must be an object")
            finding_id = nonempty_text(item.get("id"), f"findings.{severity}.id")
            if finding_id in ids:
                raise SystemExit(f"Duplicate critique finding id {finding_id}")
            ids.add(finding_id)
            findings[severity].append(
                {
                    "id": finding_id,
                    "problem": nonempty_text(item.get("problem"), f"{finding_id}.problem"),
                    "reader_consequence": nonempty_text(
                        item.get("reader_consequence"), f"{finding_id}.reader_consequence"
                    ),
                    "observable_condition": nonempty_text(
                        item.get("observable_condition"), f"{finding_id}.observable_condition"
                    ),
                }
            )
    extra = sorted(set(findings_raw) - set(CRITIQUE_SEVERITIES))
    if extra:
        raise SystemExit("Unknown critique finding severities: " + ", ".join(extra))
    if not ids:
        raise SystemExit("Critique must identify at least one consequential finding")
    highest = text_list(
        raw.get("highest_consequence_findings"),
        "highest_consequence_findings",
        minimum=1,
    )
    if len(set(highest)) != len(highest):
        raise SystemExit("highest_consequence_findings must contain unique ids")
    unknown = [item for item in highest if item not in ids]
    if unknown:
        raise SystemExit("Unknown highest-consequence finding ids: " + ", ".join(unknown))
    intervention = raw.get("intervention")
    if intervention not in INTERVENTIONS:
        raise SystemExit("Critique intervention must be repair or redesign")
    form_questioned = raw.get("form_questioned")
    if not isinstance(form_questioned, bool):
        raise SystemExit("Critique form_questioned must be true or false")
    source_inventory = raw.get("source_inventory")
    if not isinstance(source_inventory, dict):
        raise SystemExit("Critique source_inventory must be an object")
    inventory = {
        "structure": text_list(
            source_inventory.get("structure"), "source_inventory.structure", minimum=1
        ),
        "required_content": text_list(
            source_inventory.get("required_content"),
            "source_inventory.required_content",
            minimum=1,
        ),
        "semantic_mappings": text_list(
            source_inventory.get("semantic_mappings"),
            "source_inventory.semantic_mappings",
            minimum=1,
        ),
        "uncertainties": text_list(
            source_inventory.get("uncertainties"), "source_inventory.uncertainties"
        ),
    }
    extra_inventory = sorted(set(source_inventory) - set(inventory))
    if extra_inventory:
        raise SystemExit(
            "Unknown source_inventory fields: " + ", ".join(extra_inventory)
        )
    return {
        "context_version": context_version,
        "apparent_question": nonempty_text(raw.get("apparent_question"), "apparent_question"),
        "apparent_claim": nonempty_text(raw.get("apparent_claim"), "apparent_claim"),
        "evidence_limitations": text_list(raw.get("evidence_limitations"), "evidence_limitations"),
        "findings": findings,
        "highest_consequence_findings": highest,
        "misleading_reader_interpretation": nonempty_text(
            raw.get("misleading_reader_interpretation"), "misleading_reader_interpretation"
        ),
        "defensible_interpretation": nonempty_text(
            raw.get("defensible_interpretation"), "defensible_interpretation"
        ),
        "intervention": intervention,
        "form_questioned": form_questioned,
        "source_inventory": inventory,
        "layout_risks": text_list(raw.get("layout_risks"), "layout_risks", minimum=1),
        "required_delivered_outcomes": text_list(
            raw.get("required_delivered_outcomes"), "required_delivered_outcomes", minimum=1
        ),
        "preserve": text_list(raw.get("preserve"), "preserve"),
    }


def critique_findings(critique: dict, severities: tuple[str, ...] = ("fatal", "major")) -> list[dict]:
    return [item for severity in severities for item in critique["findings"][severity]]


def validate_design_contract(raw: object, critique: dict) -> dict:
    if not isinstance(raw, dict):
        raise SystemExit("Design contract must be a JSON object")
    if raw.get("critique_number") != critique["number"]:
        raise SystemExit(f"Design contract critique_number must be {critique['number']}")
    requirements = raw.get("requirements")
    if not isinstance(requirements, list):
        raise SystemExit("Design contract requirements must be a list")
    mapped: dict[str, dict] = {}
    for item in requirements:
        if not isinstance(item, dict):
            raise SystemExit("Each design requirement must be an object")
        finding_id = nonempty_text(item.get("finding_id"), "requirements.finding_id")
        if finding_id in mapped:
            raise SystemExit(f"Duplicate design mapping for finding {finding_id}")
        mapped[finding_id] = {
            "finding_id": finding_id,
            "planned_change": nonempty_text(item.get("planned_change"), f"{finding_id}.planned_change"),
            "affected_zones": text_list(item.get("affected_zones"), f"{finding_id}.affected_zones", 1),
            "observable_outcome": nonempty_text(
                item.get("observable_outcome"), f"{finding_id}.observable_outcome"
            ),
        }
    required_ids = [item["id"] for item in critique_findings(critique)]
    missing = [finding_id for finding_id in required_ids if finding_id not in mapped]
    if missing:
        raise SystemExit(
            "Design contract must map every fatal and major critique finding: "
            + ", ".join(missing)
        )
    zones = raw.get("zones")
    zone_names = ("title", "subtitle", "legend", "plot", "annotation", "footer")
    if not isinstance(zones, dict) or any(
        not isinstance(zones.get(name), str) or not zones[name].strip() for name in zone_names
    ):
        raise SystemExit("Design contract must define title, subtitle, legend, plot, annotation, and footer zones")
    selector = raw.get("selector_decision")
    selector_required = critique["form_questioned"] or critique["intervention"] == "redesign"
    if selector_required and not isinstance(selector, dict):
        raise SystemExit("A questioned chart form requires a dataviz-selector decision")
    if isinstance(selector, dict):
        selector = {
            "chart_form": nonempty_text(selector.get("chart_form"), "selector_decision.chart_form"),
            "reason": nonempty_text(selector.get("reason"), "selector_decision.reason"),
            "encoding": nonempty_text(selector.get("encoding"), "selector_decision.encoding"),
            "avoid": nonempty_text(selector.get("avoid"), "selector_decision.avoid"),
        }
    value_precision = raw.get("value_precision")
    if value_precision not in ("exact", "approximate", "mixed"):
        raise SystemExit("Design contract value_precision must be exact, approximate, or mixed")
    dimensions = raw.get("dimensions")
    if not isinstance(dimensions, dict) or not all(
        isinstance(dimensions.get(name), (int, float)) and dimensions[name] > 0
        for name in ("width", "height")
    ):
        raise SystemExit("Design contract dimensions require positive width and height")
    preservation_plan_raw = raw.get("preservation_plan")
    if not isinstance(preservation_plan_raw, list):
        raise SystemExit("Design contract preservation_plan must be a list")
    preservation_plan: list[dict] = []
    mapped_source_items: set[str] = set()
    for item in preservation_plan_raw:
        if not isinstance(item, dict):
            raise SystemExit("Each preservation_plan item must be an object")
        source_item = nonempty_text(item.get("source_item"), "preservation_plan.source_item")
        if source_item in mapped_source_items:
            raise SystemExit(f"Duplicate preservation mapping for {source_item!r}")
        mapped_source_items.add(source_item)
        preservation_plan.append(
            {
                "source_item": source_item,
                "planned_treatment": nonempty_text(
                    item.get("planned_treatment"), f"{source_item}.planned_treatment"
                ),
                "observable_outcome": nonempty_text(
                    item.get("observable_outcome"), f"{source_item}.observable_outcome"
                ),
            }
        )
    required_source_items = list(
        dict.fromkeys(
            critique["source_inventory"]["required_content"]
            + critique["source_inventory"]["semantic_mappings"]
        )
    )
    missing_source_items = [
        item for item in required_source_items if item not in mapped_source_items
    ]
    if missing_source_items:
        raise SystemExit(
            "Design contract must map every required source item and semantic mapping: "
            + ", ".join(missing_source_items)
        )
    layout_plan = raw.get("layout_plan")
    layout_fields = (
        "delivery_size",
        "longest_text",
        "dense_regions",
        "mitigation",
        "preview_check",
    )
    if not isinstance(layout_plan, dict) or any(
        not isinstance(layout_plan.get(name), str) or not layout_plan[name].strip()
        for name in layout_fields
    ):
        raise SystemExit(
            "Design contract layout_plan must define delivery_size, longest_text, "
            "dense_regions, mitigation, and preview_check"
        )
    collision_risks = text_list(
        layout_plan.get("collision_risks"), "layout_plan.collision_risks", minimum=1
    )
    plan_audit_raw = raw.get("plan_audit")
    audit_fields = (
        "inventory_coverage",
        "diagnosis_coverage",
        "preservation_coverage",
        "layout_coverage",
    )
    if not isinstance(plan_audit_raw, dict):
        raise SystemExit("Design contract plan_audit must be an object")
    verdict = nonempty_text(plan_audit_raw.get("verdict"), "plan_audit.verdict")
    if verdict != "Ready" or any(plan_audit_raw.get(name) != "Pass" for name in audit_fields):
        raise SystemExit(
            "Design contract plan_audit must be independently Ready with Pass coverage "
            "for inventory, diagnosis, preservation, and layout"
        )
    required_plan_changes = text_list(
        plan_audit_raw.get("required_plan_changes"),
        "plan_audit.required_plan_changes",
    )
    if required_plan_changes:
        raise SystemExit(
            "Resolve every required_plan_change and rerun the independent plan audit "
            "before attaching the design contract"
        )
    plan_audit = {
        "verdict": verdict,
        "summary": nonempty_text(plan_audit_raw.get("summary"), "plan_audit.summary"),
        **{name: plan_audit_raw[name] for name in audit_fields},
        "required_plan_changes": required_plan_changes,
    }
    return {
        "critique_number": critique["number"],
        "requirements": list(mapped.values()),
        "measure_scope": nonempty_text(raw.get("measure_scope"), "measure_scope"),
        "evidence_scope": nonempty_text(raw.get("evidence_scope"), "evidence_scope"),
        "chart_form": nonempty_text(raw.get("chart_form"), "chart_form"),
        "primary_identification": nonempty_text(
            raw.get("primary_identification"), "primary_identification"
        ),
        "zones": {name: zones[name].strip() for name in zone_names},
        "colour_role": nonempty_text(raw.get("colour_role"), "colour_role"),
        "dimensions": {**dimensions},
        "value_precision": value_precision,
        "selector_decision": selector,
        "preservation_plan": preservation_plan,
        "layout_plan": {
            **{name: layout_plan[name].strip() for name in layout_fields},
            "collision_risks": collision_risks,
        },
        "plan_audit": plan_audit,
    }


def validate_renderer_selection(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise SystemExit("Renderer selection must be a JSON object")
    requested = raw.get("requested")
    selected = raw.get("selected")
    if requested not in ("auto",) + RENDERERS or selected not in RENDERERS:
        raise SystemExit("Renderer selection requested/selected values are invalid")
    probe = raw.get("probe")
    if not isinstance(probe, dict) or not isinstance(probe.get("renderers"), dict):
        raise SystemExit("Renderer selection requires the probe_renderers result")
    ggplot = probe["renderers"].get("ggplot2")
    if not isinstance(ggplot, dict) or not isinstance(ggplot.get("available"), bool):
        raise SystemExit("Renderer probe is missing ggplot2 availability")
    ggplot_supported = raw.get("ggplot2_supported")
    if not isinstance(ggplot_supported, bool):
        raise SystemExit("Renderer selection ggplot2_supported must be true or false")
    reason = (raw.get("reason") or "").strip()
    if requested == "auto" and ggplot["available"] and ggplot_supported and selected != "ggplot2":
        raise SystemExit("Auto renderer must select ggplot2 when the probe succeeds and the adapter supports the output")
    if selected == "matplotlib" and ggplot["available"] and requested != "matplotlib" and not reason:
        raise SystemExit("Matplotlib fallback requires a recorded ggplot2-unavailable or unsupported reason")
    return {
        "requested": requested,
        "selected": selected,
        "ggplot2_supported": ggplot_supported,
        "reason": reason or None,
        "probe": probe,
    }


def validate_review_report(
    report: dict,
    iteration: dict,
    creator: str,
    review_token: str,
    blind_response: dict[str, str],
    blind_response_sha: str,
    carry_forward_actions: list[dict],
    acceptance_checks: list[dict],
    critique_contract: dict | None,
) -> dict:
    if not isinstance(report, dict):
        raise SystemExit("Review report must be a JSON object")
    reviewer = nonempty_text(report.get("reviewer"), "reviewer")
    if reviewer == creator:
        raise SystemExit("Chart creator and release reviewer must be different identities")
    if reviewer != blind_response["reviewer"]:
        raise SystemExit("Review report reviewer does not match the blind reviewer")
    if report.get("reviewer_role") != "independent":
        raise SystemExit("Review report reviewer_role must be 'independent'")
    if report.get("review_token") != review_token:
        raise SystemExit("Review report token does not match the recorded review request")
    if report.get("blind_response_sha256") != blind_response_sha:
        raise SystemExit("Review report blind_response_sha256 does not match the blind response")
    if report.get("iteration") != iteration["number"]:
        raise SystemExit(
            f"Review report iteration must be {iteration['number']}, not {report.get('iteration')!r}"
        )
    expected_sha = iteration["artifact"]["sha256"]
    if report.get("artifact_sha256") != expected_sha:
        raise SystemExit("Review report artifact_sha256 does not match the recorded iteration")
    expected_inspection_sha = iteration.get("inspection", {}).get("sha256")
    if expected_inspection_sha and report.get("deterministic_inspection_sha256") != expected_inspection_sha:
        raise SystemExit(
            "Review report deterministic_inspection_sha256 does not match the recorded inspection"
        )
    expected_context_version = iteration.get("context_version", 1)
    if report.get("context_version") != expected_context_version:
        raise SystemExit(
            f"Review report context_version must be {expected_context_version}, not {report.get('context_version')!r}"
        )

    verdict = report.get("verdict")
    if verdict not in VERDICTS:
        raise SystemExit(f"Invalid review verdict {verdict!r}; choose from {', '.join(VERDICTS)}")
    scope = nonempty_text(report.get("scope"), "scope")
    tested_size = nonempty_text(report.get("tested_size"), "tested_size")
    blind_reads = report.get("blind_reads")
    if not isinstance(blind_reads, dict):
        raise SystemExit("Review report blind_reads must be an object")
    expert = nonempty_text(blind_reads.get("expert"), "blind_reads.expert")
    audience = nonempty_text(blind_reads.get("audience"), "blind_reads.audience")
    if expert != blind_response["expert"] or audience != blind_response["audience"]:
        raise SystemExit("Review report blind reads must match the saved pre-intent blind response")
    blind_semantics = report.get("blind_semantics")
    if blind_semantics != blind_response["semantics"]:
        raise SystemExit(
            "Review report blind semantics must match the saved pre-intent semantic response"
        )
    gates = validate_ratings(report.get("gates"), GATE_NAMES, "gates", include_required=True)
    semantic_checks = validate_semantic_checks(report.get("semantic_checks"))
    release_checks = validate_ratings(
        report.get("release_checks"),
        RELEASE_CHECK_NAMES,
        "release_checks",
        require_stress_test=True,
    )
    raw_presentation_checks = report.get("presentation_checks")
    if iteration.get("presentation_checks_required") or raw_presentation_checks is not None:
        presentation_checks = validate_ratings(
            raw_presentation_checks,
            PRESENTATION_CHECK_NAMES,
            "presentation_checks",
            require_stress_test=True,
        )
    else:
        # Iterations recorded before schema 13 remain reviewable. Every new
        # iteration records presentation_checks_required and cannot bypass them.
        presentation_checks = {}

    raw_carry_checks = report.get("carry_forward_checks", [])
    if not isinstance(raw_carry_checks, list):
        raise SystemExit("Review report carry_forward_checks must be a list")
    expected_by_id = {item["id"]: item for item in carry_forward_actions}
    carry_checks: list[dict] = []
    seen_ids: set[str] = set()
    for item in raw_carry_checks:
        if not isinstance(item, dict):
            raise SystemExit("Each carry_forward_checks item must be an object")
        action_id = item.get("id")
        if action_id not in expected_by_id:
            raise SystemExit(f"Unknown carry-forward action id {action_id!r}")
        if action_id in seen_ids:
            raise SystemExit(f"Duplicate carry-forward action id {action_id!r}")
        result = item.get("result")
        if result not in GATE_RESULTS:
            raise SystemExit(
                f"Invalid carry-forward result {result!r}; choose from {', '.join(GATE_RESULTS)}"
            )
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise SystemExit(f"Carry-forward action {action_id} requires direct observed evidence")
        carry_checks.append(
            {"id": action_id, "result": result, "evidence": evidence.strip()}
        )
        seen_ids.add(action_id)
    missing_carry_ids = [item["id"] for item in carry_forward_actions if item["id"] not in seen_ids]
    if missing_carry_ids:
        raise SystemExit(
            "Review report must recheck every unresolved prior action: "
            + ", ".join(missing_carry_ids)
        )

    raw_acceptance_results = report.get("acceptance_checks", [])
    if not isinstance(raw_acceptance_results, list):
        raise SystemExit("Review report acceptance_checks must be a list")
    expected_acceptance_by_id = {item["id"]: item for item in acceptance_checks}
    acceptance_results: list[dict] = []
    seen_acceptance_ids: set[str] = set()
    for item in raw_acceptance_results:
        if not isinstance(item, dict):
            raise SystemExit("Each acceptance_checks item must be an object")
        check_id = item.get("id")
        if check_id not in expected_acceptance_by_id:
            raise SystemExit(f"Unknown active acceptance check id {check_id!r}")
        if check_id in seen_acceptance_ids:
            raise SystemExit(f"Duplicate active acceptance check id {check_id!r}")
        result = item.get("result")
        if result not in GATE_RESULTS:
            raise SystemExit(
                f"Invalid acceptance-check result {result!r}; choose from {', '.join(GATE_RESULTS)}"
            )
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise SystemExit(f"Acceptance check {check_id} requires direct observed evidence")
        acceptance_results.append(
            {"id": check_id, "result": result, "evidence": evidence.strip()}
        )
        seen_acceptance_ids.add(check_id)
    missing_acceptance_ids = [
        item["id"] for item in acceptance_checks if item["id"] not in seen_acceptance_ids
    ]
    if missing_acceptance_ids:
        raise SystemExit(
            "Review report must test every active user acceptance check: "
            + ", ".join(missing_acceptance_ids)
        )

    expected_critique_ids = (
        [item["id"] for item in critique_findings(critique_contract)]
        if critique_contract
        else []
    )
    raw_critique_checks = report.get("critique_checks", [])
    if not isinstance(raw_critique_checks, list):
        raise SystemExit("Review report critique_checks must be a list")
    critique_checks: list[dict] = []
    seen_critique_ids: set[str] = set()
    for item in raw_critique_checks:
        if not isinstance(item, dict):
            raise SystemExit("Each critique_checks item must be an object")
        finding_id = item.get("id")
        if finding_id not in expected_critique_ids:
            raise SystemExit(f"Unknown active critique finding id {finding_id!r}")
        if finding_id in seen_critique_ids:
            raise SystemExit(f"Duplicate critique finding id {finding_id!r}")
        result = item.get("result")
        if result not in GATE_RESULTS:
            raise SystemExit(f"Invalid critique-check result {result!r}")
        critique_checks.append(
            {
                "id": finding_id,
                "result": result,
                "evidence": nonempty_text(item.get("evidence"), f"critique_checks.{finding_id}.evidence"),
            }
        )
        seen_critique_ids.add(finding_id)
    missing_critique_ids = [
        finding_id for finding_id in expected_critique_ids if finding_id not in seen_critique_ids
    ]
    if missing_critique_ids:
        raise SystemExit(
            "Review report must close every fatal and major critique finding: "
            + ", ".join(missing_critique_ids)
        )

    raw_codes = report.get("codes", [])
    if not isinstance(raw_codes, list) or any(not isinstance(code, str) or not code.strip() for code in raw_codes):
        raise SystemExit("Review report codes must be a list of non-empty strings")
    codes = list(dict.fromkeys(code.strip() for code in raw_codes))
    raw_actions = report.get("required_actions", [])
    if not isinstance(raw_actions, list):
        raise SystemExit("Review report required_actions must be a list")
    required_actions: list[dict] = []
    for index, action in enumerate(raw_actions, start=1):
        if not isinstance(action, dict):
            raise SystemExit("Each required action must be a structured object")
        action_codes = text_list(action.get("codes"), f"required_actions[{index}].codes", 1)
        zones = text_list(
            action.get("affected_zones"),
            f"required_actions[{index}].affected_zones",
            1,
        )
        required_actions.append(
            {
                "target": nonempty_text(action.get("target"), f"required_actions[{index}].target"),
                "from": nonempty_text(action.get("from"), f"required_actions[{index}].from"),
                "to": nonempty_text(action.get("to"), f"required_actions[{index}].to"),
                "why": nonempty_text(action.get("why"), f"required_actions[{index}].why"),
                "codes": action_codes,
                "affected_zones": zones,
            }
        )
    unknown_action_codes = sorted(
        {
            code
            for action in required_actions
            for code in action["codes"]
            if code not in codes
        }
    )
    if unknown_action_codes:
        raise SystemExit(
            "Required-action codes must appear in the evaluation codes list: "
            + ", ".join(unknown_action_codes)
        )
    raw_baseline_concerns = report.get("baseline_concerns", [])
    if not isinstance(raw_baseline_concerns, list) or any(
        not isinstance(item, str) or not item.strip() for item in raw_baseline_concerns
    ):
        raise SystemExit("Review report baseline_concerns must be a list of non-empty strings")
    baseline_concerns = [item.strip() for item in raw_baseline_concerns]

    required_results = [item["result"] for item in gates.values() if item["required"]] + [
        item["result"] for item in release_checks.values()
    ] + [item["result"] for item in presentation_checks.values()] + [
        item["result"] for item in semantic_checks.values()
    ] + [
        item["result"] for item in carry_checks
    ] + [
        item["result"] for item in acceptance_results
    ] + [
        item["result"] for item in critique_checks
    ]
    if verdict == "Send":
        inspection = iteration.get("inspection")
        blocking_defects = (
            inspection.get(
                "blocking_defect_codes",
                inspection.get("defect_codes", []),
            )
            if inspection
            else []
        )
        if blocking_defects:
            raise SystemExit(
                "Send cannot override deterministic inspection defects: "
                + ", ".join(blocking_defects)
            )
        if inspection and inspection.get("checks_complete") and not inspection.get(
            "passes_geometry_checks"
        ):
            raise SystemExit("Send requires complete deterministic geometry checks to pass")
        if any(result != "Pass" for result in required_results):
            raise SystemExit(
                "Send requires every required gate, semantic check, release check, "
                "presentation check, carried action, and acceptance check to Pass"
            )
        if codes or required_actions:
            raise SystemExit("Send cannot include failure codes or required actions")
    elif verdict in ("Revise", "Redesign"):
        if all(result == "Pass" for result in required_results):
            raise SystemExit(f"{verdict} requires at least one non-Pass result")
        if not codes or not required_actions:
            raise SystemExit(f"{verdict} requires failure codes and required actions")
    elif verdict == "Not evaluable" and "Unknown" not in required_results:
        raise SystemExit("Not evaluable requires at least one Unknown result")

    return {
        "reviewer": reviewer,
        "reviewer_role": "independent",
        "review_token": review_token,
        "blind_response_sha256": blind_response_sha,
        "iteration": iteration["number"],
        "artifact_sha256": expected_sha,
        "deterministic_inspection_sha256": expected_inspection_sha,
        "context_version": expected_context_version,
        "scope": scope,
        "tested_size": tested_size,
        "blind_reads": {"expert": expert, "audience": audience},
        "blind_semantics": blind_response["semantics"],
        "gates": gates,
        "semantic_checks": semantic_checks,
        "release_checks": release_checks,
        "presentation_checks": presentation_checks,
        "carry_forward_checks": carry_checks,
        "acceptance_checks": acceptance_results,
        "critique_checks": critique_checks,
        "verdict": verdict,
        "codes": codes,
        "required_actions": required_actions,
        "baseline_concerns": baseline_concerns,
    }


def active_acceptance_checks(data: dict, iteration: dict) -> list[dict]:
    """Return non-superseded user checks active when an iteration was recorded."""
    checks: list[dict] = []
    request_check_count = iteration.get(
        "request_check_count", len(data.get("request_checks", []))
    )
    for item in data.get("request_checks", [])[:request_check_count]:
        checks.append(
            {
                "id": f"r{item['number']}",
                "request_check_number": item["number"],
                "kind": item.get("kind", "change"),
                "text": item.get("text", ""),
                **item["acceptance_check"],
            }
        )
    feedback_count = iteration.get("feedback_count", 0)
    for item in data.get("feedback", [])[:feedback_count]:
        superseded_by = item.get("superseded_by_feedback")
        if superseded_by and superseded_by <= feedback_count:
            continue
        check = item.get("acceptance_check") or {
            "target": "legacy feedback",
            "current": "not structured",
            "required": item.get("text", ""),
            "why": "",
        }
        checks.append(
            {
                "id": f"f{item['number']}",
                "feedback_number": item["number"],
                "text": item.get("text", ""),
                **check,
            }
        )
    return checks


def open_required_actions(data: dict, iteration: dict) -> list[dict]:
    """Return unresolved evaluator actions from the latest prior iteration."""
    previous = next(
        (
            item
            for item in reversed(data.get("evaluations", []))
            if item.get("iteration", 0) < iteration["number"]
            and item.get("context_version", 1) == iteration.get("context_version", 1)
            and not item.get("superseded_at")
        ),
        None,
    )
    if previous is None:
        return []
    superseded_action_ids = {
        action_id
        for item in data.get("feedback", [])[: iteration.get("feedback_count", 0)]
        for action_id in item.get("supersedes_actions", [])
    }
    stored = previous.get("open_required_actions")
    if isinstance(stored, list):
        return [
            copy.deepcopy(item)
            for item in stored
            if item["id"] not in superseded_action_ids
        ]
    return [
        {
            "id": f"e{previous['number']}-a{index}",
            "action": action,
            "source_evaluation": previous["number"],
        }
        for index, action in enumerate(previous.get("required_actions", []), start=1)
        if f"e{previous['number']}-a{index}" not in superseded_action_ids
    ]


def _action_parts(action: object) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Return comparable prose, failure codes, and affected zones for an action."""
    if isinstance(action, dict):
        prose = " ".join(
            str(action.get(name, "")) for name in ("target", "from", "to", "why")
        )
        codes = tuple(sorted(str(item).strip().lower() for item in action.get("codes", []) if str(item).strip()))
        zones = tuple(sorted(str(item).strip().lower() for item in action.get("affected_zones", []) if str(item).strip()))
        return prose, codes, zones
    prose = str(action)
    codes_match = re.search(r"\bCodes?:\s*([^.;]+)", prose, re.IGNORECASE)
    codes = (
        tuple(
            sorted(
                item.strip().lower()
                for item in codes_match.group(1).split(",")
                if item.strip()
            )
        )
        if codes_match
        else ()
    )
    return prose, codes, ()


def action_fingerprint(action: object) -> str:
    """Build a stable semantic fingerprint without using evaluator action ids."""
    prose, codes, zones = _action_parts(action)
    normalized = re.sub(r"[^a-z0-9]+", " ", prose.lower()).strip()
    topics = tuple(
        name
        for name, pattern in _ACTION_TOPIC_PATTERNS.items()
        if re.search(pattern, normalized, re.IGNORECASE)
    )
    tokens = tuple(
        sorted(
            {
                token
                for token in normalized.split()
                if len(token) > 2 and token not in _ACTION_STOP_WORDS
            }
        )
    )
    payload = {
        "codes": codes,
        "zones": zones,
        # The first matching topic is intentionally dominant. Supporting-copy
        # nouns vary as evaluators reword the same delivery or geometry defect.
        "topics": topics[:1],
        "tokens": tokens if not topics else (),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def actions_equivalent(left: object, right: object) -> bool:
    """Match reworded action debt while keeping different chart concerns distinct."""
    if left == right:
        return True
    left_prose, left_codes, left_zones = _action_parts(left)
    right_prose, right_codes, right_zones = _action_parts(right)
    if left_codes and right_codes and set(left_codes).isdisjoint(right_codes):
        return False
    if left_zones and right_zones and set(left_zones).isdisjoint(right_zones):
        return False

    def topics(prose: str) -> set[str]:
        return {
            name
            for name, pattern in _ACTION_TOPIC_PATTERNS.items()
            if re.search(pattern, prose, re.IGNORECASE)
        }

    left_topics = topics(left_prose)
    right_topics = topics(right_prose)
    if left_topics or right_topics:
        semantic_topics = {
            "delivery-scale",
            "collision",
            "label-association",
            "legend",
            "axis",
            "contrast",
            "whitespace",
            "period",
            "measure",
            "universe",
            "claim",
        }
        shared = left_topics & right_topics & semantic_topics
        if left_codes and right_codes and set(left_codes) == set(right_codes):
            return bool(shared)
        return bool(shared) and left_topics == right_topics

    def tokens(prose: str) -> set[str]:
        return {
            token
            for token in re.sub(r"[^a-z0-9]+", " ", prose.lower()).split()
            if len(token) > 2 and token not in _ACTION_STOP_WORDS
        }

    left_tokens = tokens(left_prose)
    right_tokens = tokens(right_prose)
    union = left_tokens | right_tokens
    return bool(union) and len(left_tokens & right_tokens) / len(union) >= 0.5


def update_open_required_actions(
    prior_actions: list[dict],
    carry_checks: list[dict],
    current_actions: list[dict],
    evaluation_number: int,
) -> list[dict]:
    """Keep prior actions open until directly passed, then add new actions."""
    result_by_id = {item["id"]: item["result"] for item in carry_checks}
    open_actions = [
        item for item in prior_actions if result_by_id.get(item["id"]) != "Pass"
    ]
    for index, action in enumerate(current_actions, start=1):
        equivalent = next(
            (item for item in open_actions if actions_equivalent(item["action"], action)),
            None,
        )
        if equivalent is not None:
            equivalent.setdefault("equivalent_reports", []).append(
                {
                    "evaluation": evaluation_number,
                    "reported_action": action,
                }
            )
            continue
        open_actions.append(
            {
                "id": f"e{evaluation_number}-a{index}",
                "action": action,
                "source_evaluation": evaluation_number,
                "fingerprint": action_fingerprint(action),
            }
        )
    return open_actions


def active_user_checks_for_next_build(data: dict) -> list[dict]:
    """Return active checks added after the latest built candidate."""
    if not data.get("iterations"):
        return []
    latest = data["iterations"][-1]
    checks = active_acceptance_checks(
        data,
        {
            **latest,
            "request_check_count": len(data.get("request_checks", [])),
            "feedback_count": len(data.get("feedback", [])),
        },
    )
    built_ids = {
        item["id"]
        for item in active_acceptance_checks(data, latest)
    }
    return [item for item in checks if item["id"] not in built_ids]


def validate_revision_contract(raw: object, data: dict) -> dict:
    if not isinstance(raw, dict):
        raise SystemExit("Revision contract must be a JSON object")
    latest = data["iterations"][-1]
    prior_actions = open_required_actions(
        data,
        {**latest, "number": latest["number"] + 1, "feedback_count": len(data.get("feedback", []))},
    )
    user_checks = active_user_checks_for_next_build(data)
    expected = {item["id"]: "evaluator" for item in prior_actions}
    expected.update({item["id"]: "user" for item in user_checks})
    raw_changes = raw.get("changes")
    if not isinstance(raw_changes, list):
        raise SystemExit("Revision contract changes must be a list")
    changes: list[dict] = []
    seen: set[str] = set()
    for item in raw_changes:
        if not isinstance(item, dict):
            raise SystemExit("Each revision-contract change must be an object")
        source_id = nonempty_text(item.get("source_id"), "changes.source_id")
        if source_id not in expected:
            raise SystemExit(f"Unknown revision source id {source_id}")
        if source_id in seen:
            raise SystemExit(f"Duplicate revision mapping for {source_id}")
        seen.add(source_id)
        changes.append(
            {
                "source_id": source_id,
                "source_type": expected[source_id],
                "planned_change": nonempty_text(item.get("planned_change"), f"{source_id}.planned_change"),
                "affected_zones": text_list(item.get("affected_zones"), f"{source_id}.affected_zones", 1),
                "observable_outcome": nonempty_text(
                    item.get("observable_outcome"), f"{source_id}.observable_outcome"
                ),
            }
        )
    missing = [source_id for source_id in expected if source_id not in seen]
    if missing:
        raise SystemExit(
            "Revision contract must map every open evaluator action and new user check: "
            + ", ".join(missing)
        )
    return {
        "source_iteration": latest["number"],
        "source_evaluation": data["evaluations"][-1]["number"] if data.get("evaluations") else None,
        "changes": changes,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read case file {path}: {exc}") from exc


def infer_legacy_state(data: dict) -> str:
    state = data.get("state")
    if state in TERMINAL_STATES or state in ACTIVE_STATES or state in PAUSED_STATES:
        return state
    if not data.get("iterations"):
        return "build"
    latest_iteration = data["iterations"][-1]["number"]
    evaluation = next(
        (
            item
            for item in reversed(data.get("evaluations", []))
            if item.get("iteration") == latest_iteration
        ),
        None,
    )
    if evaluation is None:
        return "blind_review"
    return {
        "Send": "user_review",
        "Revise": "revise",
        "Redesign": "redesign",
        "Not evaluable": "blocked",
    }.get(evaluation.get("verdict"), "blocked")


def context_field(value: str | None, source: str = "user") -> dict[str, str]:
    clean = (value or "").strip()
    return {
        "value": clean,
        "source": source if clean else "unknown",
        "updated_at": now_iso(),
    }


def initial_context(data: dict) -> dict:
    intake_source = data.get("intake_context_source", "unknown")
    fields = {
        name: context_field(
            data.get(name) if name in ("audience", "medium") else None,
            intake_source,
        )
        for name in CONTEXT_FIELDS
    }
    prompt = (data.get("request") or "").strip()
    return {
        "version": 1,
        "updated_at": data.get("created_at", now_iso()),
        "prompts": (
            [{"number": 1, "at": data.get("created_at", now_iso()), "text": prompt, "source": "user"}]
            if prompt
            else []
        ),
        "fields": fields,
    }


def context_snapshot(context: dict, reason: str) -> dict:
    return {
        "version": context["version"],
        "at": context["updated_at"],
        "reason": reason,
        "prompts": json.loads(json.dumps(context.get("prompts", []))),
        "fields": json.loads(json.dumps(context["fields"])),
    }


def context_at_version(data: dict, version: int) -> dict:
    snapshot = next(
        (item for item in data.get("context_history", []) if item["version"] == version),
        None,
    )
    if snapshot is None:
        raise SystemExit(f"Context version {version} is missing from the case history")
    return snapshot


def semantic_preflight_at_version(data: dict, version: int) -> dict | None:
    return next(
        (
            item
            for item in reversed(data.get("semantic_preflights", []))
            if item.get("context_version") == version
        ),
        None,
    )


def semantic_preflight_for_iteration(data: dict, iteration: dict) -> dict | None:
    number = iteration.get("semantic_preflight")
    if number is not None:
        return next(
            (
                item
                for item in data.get("semantic_preflights", [])
                if item.get("number") == number
            ),
            None,
        )
    return semantic_preflight_at_version(data, iteration.get("context_version", 1))


def critique_for_iteration(data: dict, iteration: dict) -> dict | None:
    number = iteration.get("critique")
    return next(
        (item for item in data.get("critiques", []) if item.get("number") == number),
        None,
    )


def current_critique(data: dict) -> dict:
    critique = next(
        (
            item
            for item in reversed(data.get("critiques", []))
            if item.get("context_version") == data.get("context_version", 1)
        ),
        None,
    )
    if critique is None:
        raise SystemExit("Run dataviz-critique on the source chart and attach its repair brief first")
    return critique


def current_design_contract(data: dict, critique: dict) -> dict:
    contract = next(
        (
            item
            for item in reversed(data.get("design_contracts", []))
            if item.get("critique_number") == critique["number"]
        ),
        None,
    )
    if contract is None:
        raise SystemExit("Attach a complete design contract for the active critique before building")
    return contract


def current_renderer_selection(data: dict) -> dict:
    selection = next(
        (
            item
            for item in reversed(data.get("renderer_selections", []))
            if item.get("context_version") == data.get("context_version", 1)
        ),
        None,
    )
    if selection is None:
        raise SystemExit("Record probe_renderers evidence and renderer selection before building")
    return selection


def require_current_semantic_preflight(data: dict) -> dict:
    preflight = semantic_preflight_at_version(data, data.get("context_version", 1))
    if preflight is None:
        raise SystemExit(
            "Record the five-part semantic preflight for the current context before building"
        )
    return preflight


def upgrade_case(data: dict) -> dict:
    original_state = data.get("state")
    state = infer_legacy_state(data)
    data["schema_version"] = SCHEMA_VERSION
    data["state"] = state
    context = data.setdefault("context", initial_context(data))
    for name in CONTEXT_FIELDS:
        context.setdefault("fields", {}).setdefault(name, context_field(None, "unknown"))
    context.setdefault("prompts", [])
    context.setdefault("version", data.get("context_version", 1))
    context.setdefault("updated_at", data.get("updated_at", now_iso()))
    data["context_version"] = context["version"]
    data.setdefault("context_history", [context_snapshot(context, "Initial or migrated context")])
    limits = data.setdefault("limits", {})
    for name, value in {
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "max_stalled_evaluations": DEFAULT_MAX_STALLED_EVALUATIONS,
        "max_elapsed_seconds": None,
        "max_tokens": None,
        "max_cost_usd": None,
    }.items():
        limits.setdefault(name, value)
    telemetry = data.setdefault("telemetry", {})
    for name, value in {
        "calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "latency_seconds": 0.0,
        "events": [],
    }.items():
        telemetry.setdefault(name, value)
    data.setdefault("stalled_evaluations", 0)
    data.setdefault("stall_keys", [])
    data.setdefault("best_candidate", None)
    data.setdefault("stop", None)
    data.setdefault("limit_authorizations", [])
    data.setdefault("limit_changes", [])
    if "diagnoses" not in data:
        data["diagnoses"] = [data["diagnosis"]] if data.get("diagnosis") else []
    data.setdefault("request_checks", [])
    data.setdefault("semantic_preflights", [])
    data.setdefault("critiques", [])
    data.setdefault("design_contracts", [])
    data.setdefault("revision_contracts", [])
    data.setdefault("renderer_selections", [])
    if "transitions" not in data:
        data["transitions"] = [
            {
                "number": 1,
                "at": data.get("created_at", now_iso()),
                "from": original_state if original_state != state else None,
                "to": state,
                "action": "schema-upgrade" if original_state != state else "start",
                "reason": "Inferred explicit loop state from the existing case record",
                "iteration": data.get("iterations", [{}])[-1].get("number")
                if data.get("iterations")
                else None,
                "artifact_sha256": data.get("iterations", [{}])[-1]
                .get("artifact", {})
                .get("sha256")
                if data.get("iterations")
                else None,
                "context_version": data.get("context_version", 1),
            }
        ]
    return data


def load_case(path: Path) -> dict:
    return upgrade_case(read_json(path))


def require_state(data: dict, allowed: tuple[str, ...], action: str) -> None:
    state = data["state"]
    if state not in allowed:
        choices = ", ".join(allowed)
        raise SystemExit(f"Cannot {action} while case state is {state!r}; expected {choices}")


def transition(
    data: dict,
    target: str,
    action: str,
    reason: str,
    iteration: dict | None = None,
) -> None:
    source = data.get("state")
    latest_evaluation = data.get("evaluations", [])[-1] if data.get("evaluations") else None
    telemetry = data.get("telemetry", {})
    data["state"] = target
    data.setdefault("transitions", []).append(
        {
            "number": len(data["transitions"]) + 1,
            "at": now_iso(),
            "from": source,
            "to": target,
            "action": action,
            "reason": reason,
            "iteration": iteration.get("number") if iteration else None,
            "artifact_sha256": iteration.get("artifact", {}).get("sha256")
            if iteration
            else None,
            "context_version": data.get("context_version", 1),
            "verdict": latest_evaluation.get("verdict") if latest_evaluation else None,
            "usage": {
                "calls": telemetry.get("calls", 0),
                "total_tokens": telemetry.get("total_tokens", 0),
                "cost_usd": telemetry.get("cost_usd", 0.0),
                "latency_seconds": telemetry.get("latency_seconds", 0.0),
            },
        }
    )
    data["updated_at"] = now_iso()


def elapsed_seconds(data: dict) -> float:
    created = datetime.fromisoformat(data["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - created).total_seconds())


def budget_status(data: dict) -> dict:
    limits = data["limits"]
    telemetry = data["telemetry"]
    exhausted: list[str] = []
    if limits.get("max_iterations") is not None and len(data["iterations"]) >= limits["max_iterations"]:
        exhausted.append("iteration_budget")
    if limits.get("max_elapsed_seconds") is not None and elapsed_seconds(data) >= limits["max_elapsed_seconds"]:
        exhausted.append("time_budget")
    if limits.get("max_tokens") is not None and telemetry["total_tokens"] >= limits["max_tokens"]:
        exhausted.append("token_budget")
    if limits.get("max_cost_usd") is not None and telemetry["cost_usd"] >= limits["max_cost_usd"]:
        exhausted.append("cost_budget")
    return {
        "exhausted": exhausted,
        "iterations_used": len(data["iterations"]),
        "iterations_remaining": max(0, limits["max_iterations"] - len(data["iterations"]))
        if limits.get("max_iterations") is not None
        else None,
        "elapsed_seconds": round(elapsed_seconds(data), 3),
        "tokens_used": telemetry["total_tokens"],
        "cost_usd": round(telemetry["cost_usd"], 6),
    }


def stop_case(data: dict, kind: str, reason: str, action: str) -> None:
    target = "blocked" if kind in ("no_progress", "missing_context", "missing_evidence", "renderer_failure") else "stopped"
    data["stop"] = {
        "at": now_iso(),
        "kind": kind,
        "reason": reason,
        "limit_change_count": len(data.get("limit_changes", [])),
        "best_candidate": data.get("best_candidate"),
        "unresolved": {
            "critique_findings": [
                item
                for critique in data.get("critiques", [])[-1:]
                for item in critique_findings(critique)
            ],
            "evaluator_actions": (
                data.get("evaluations", [])[-1].get("open_required_actions", [])
                if data.get("evaluations")
                else []
            ),
            "user_checks": active_user_checks_for_next_build(data),
        },
    }
    transition(data, target, action, reason)


def enforce_build_budget(data: dict, path: Path) -> None:
    status = budget_status(data)
    exhausted = status["exhausted"]
    if not exhausted:
        return
    kind = exhausted[0]
    reason = f"Cannot build another iteration: {kind.replace('_', ' ')} exhausted"
    stop_case(data, kind, reason, "budget-check")
    write_json(path, data)
    raise SystemExit(f"{reason}; adjust limits and resume the case")


def required_results(event: dict) -> list[str]:
    gate_required = event.get("gate_required", {})
    gate_results = [
        result
        for name, result in event.get("gates", {}).items()
        if gate_required.get(name, True)
    ]
    release_results = [
        item["result"] for item in event.get("release_checks", {}).values()
    ]
    presentation_results = [
        item["result"] for item in event.get("presentation_checks", {}).values()
    ]
    contract_results = [
        item["result"]
        for field in (
            "semantic_checks",
            "acceptance_checks",
            "critique_checks",
        )
        for item in (
            event.get(field, {}).values()
            if isinstance(event.get(field), dict)
            else event.get(field, [])
        )
    ]
    return gate_results + release_results + presentation_results + contract_results


def candidate_rank(event: dict) -> list[int]:
    results = required_results(event)
    hard = sum(result in ("Fail", "Unknown") for result in results)
    non_pass = sum(result != "Pass" for result in results)
    passes = sum(result == "Pass" for result in results)
    return [-hard, -non_pass, passes, -len(event.get("codes", []))]


def update_best_candidate(data: dict, event: dict, iteration: dict) -> None:
    rank = candidate_rank(event)
    current = data.get("best_candidate")
    if current is not None and rank <= current.get("rank", []):
        return
    data["best_candidate"] = {
        "selected_at": now_iso(),
        "iteration": iteration["number"],
        "evaluation": event["number"],
        "verdict": event["verdict"],
        "artifact": iteration["artifact"],
        "rank": rank,
        "selection": "fewest unresolved required gates; hard failures cannot be averaged away",
    }


def evaluation_failure_keys(event: dict) -> set[str]:
    """Return stable keys for recurring failures, independent of wording and ids."""
    codes = tuple(sorted(str(code).strip().lower() for code in event.get("codes", [])))
    keys = {"action:" + action_fingerprint(action) for action in event.get("required_actions", [])}

    nonpass: list[str] = []
    for name, result in event.get("gates", {}).items():
        if event.get("gate_required", {}).get(name, True) and result != "Pass":
            nonpass.append(f"gate:{name.lower()}={str(result).lower()}")
    for field in ("release_checks", "presentation_checks", "semantic_checks"):
        for name, item in event.get(field, {}).items():
            result = item.get("result") if isinstance(item, dict) else item
            if result != "Pass":
                nonpass.append(f"{field}:{name.lower()}={str(result).lower()}")
    for field in ("acceptance_checks", "critique_checks"):
        for item in event.get(field, []):
            if item.get("result") != "Pass":
                nonpass.append(f"{field}:{item.get('id')}={str(item.get('result')).lower()}")
    if codes and nonpass:
        keys.add(
            "outcome:"
            + ",".join(codes)
            + "|"
            + ",".join(sorted(nonpass))
        )
    return keys


def update_stall_count(data: dict, event: dict) -> bool:
    previous = data.get("evaluations", [])[-1] if data.get("evaluations") else None
    if previous is None:
        data["stalled_evaluations"] = 0
        event["stall_keys"] = sorted(evaluation_failure_keys(event))
        data["stall_keys"] = event["stall_keys"]
        return False
    current_keys = evaluation_failure_keys(event)
    previous_keys = set(previous.get("stall_keys") or evaluation_failure_keys(previous))
    recurring = current_keys & previous_keys
    stalled = bool(
        event["verdict"] in ("Revise", "Redesign")
        and previous.get("verdict") in ("Revise", "Redesign")
        and recurring
    )
    data["stalled_evaluations"] = data.get("stalled_evaluations", 0) + 1 if stalled else 0
    event["stall_keys"] = sorted(current_keys)
    event["recurring_stall_keys"] = sorted(recurring)
    data["stall_keys"] = event["stall_keys"]
    limit = data["limits"].get("max_stalled_evaluations")
    return limit is not None and data["stalled_evaluations"] >= limit


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def copy_artifact(source: Path, target: Path) -> dict:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Artifact not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {
        "path": str(target),
        "original_path": str(source),
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
    }


def validate_deliverable(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix not in DELIVERABLE_SUFFIXES:
        raise SystemExit(
            f"Iteration must be delivered media ({', '.join(DELIVERABLE_SUFFIXES)}), not {suffix or 'an extensionless file'}"
        )
    head = path.read_bytes()[:512]
    valid = False
    if suffix == ".png":
        valid = head.startswith(b"\x89PNG\r\n\x1a\n")
    elif suffix in (".jpg", ".jpeg"):
        valid = head.startswith(b"\xff\xd8\xff")
    elif suffix == ".pdf":
        valid = head.startswith(b"%PDF-")
    elif suffix == ".svg":
        valid = b"<svg" in head.lower()
    if not valid:
        raise SystemExit(f"Iteration extension and file content do not match: {path}")


def active_pointer(session: str) -> Path:
    return root_dir() / "active" / f"{safe_id(session)}.txt"


def resolve_case(args: argparse.Namespace) -> Path:
    if getattr(args, "case", None):
        case_dir = root_dir() / "cases" / safe_id(args.case)
    else:
        pointer = active_pointer(args.session)
        if not pointer.is_file():
            raise SystemExit(f"No active case for session {args.session!r}")
        case_dir = Path(pointer.read_text(encoding="utf-8").strip())
    if not (case_dir / "case.json").is_file():
        raise SystemExit(f"Invalid case directory: {case_dir}")
    return case_dir


def snapshot_skills(skills_root: Path | None, case_dir: Path) -> str | None:
    if skills_root is None:
        return None
    skills_root = skills_root.expanduser().resolve()
    if not skills_root.is_dir():
        raise SystemExit(f"Skills root not found: {skills_root}")
    rows = []
    for path in sorted(skills_root.rglob("SKILL.md")):
        if ".git" in path.parts:
            continue
        rows.append({"path": str(path.relative_to(skills_root)), "sha256": sha256(path)})
    target = case_dir / "skill-snapshot.json"
    write_json(target, {"root": str(skills_root), "captured_at": now_iso(), "skills": rows})
    return str(target)


def cmd_start(args: argparse.Namespace) -> None:
    root = root_dir()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_id = f"{stamp}-{token_hex(2)}"
    case_dir = root / "cases" / case_id
    case_dir.mkdir(parents=True)

    image = Path(args.image).expanduser().resolve()
    ext = image.suffix.lower() or ".bin"
    original = copy_artifact(image, case_dir / f"original{ext}")
    snapshot = snapshot_skills(Path(args.skills_root) if args.skills_root else None, case_dir)
    data = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "session_id": args.session,
        "creator": args.creator or f"session:{args.session}",
        "state": "intake",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "request": args.request or "",
        "audience": args.audience or "",
        "medium": args.medium or "",
        "intake_context_source": args.context_source,
        "context_version": 1,
        "original": original,
        "skill_snapshot": snapshot,
        "limits": {
            "max_iterations": args.max_iterations,
            "max_stalled_evaluations": args.max_stalled_evaluations,
            "max_elapsed_seconds": args.max_elapsed_minutes * 60
            if args.max_elapsed_minutes
            else None,
            "max_tokens": args.max_tokens,
            "max_cost_usd": args.max_cost_usd,
        },
        "telemetry": {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "latency_seconds": 0.0,
            "events": [],
        },
        "stalled_evaluations": 0,
        "stall_keys": [],
        "best_candidate": None,
        "stop": None,
        "limit_authorizations": [],
        "limit_changes": [],
        "request_checks": [],
        "semantic_preflights": [],
        "critiques": [],
        "design_contracts": [],
        "revision_contracts": [],
        "renderer_selections": [],
        "feedback": [],
        "iterations": [],
        "evaluations": [],
        "acceptance": None,
        "diagnosis": None,
        "diagnoses": [],
        "transitions": [],
    }
    data["context"] = initial_context(data)
    for name in CONTEXT_FIELDS:
        value = getattr(args, name, None)
        if value:
            data["context"]["fields"][name] = context_field(value, args.context_source)
    if args.preserve:
        data["request_checks"].append(
            {
                "number": 1,
                "at": now_iso(),
                "kind": "preserve",
                "text": f"Preserve: {args.preserve}",
                "acceptance_check": {
                    "target": "all elements named in the preservation contract",
                    "current": f"The source or latest accepted candidate contains: {args.preserve}",
                    "required": f"The delivered candidate still preserves: {args.preserve}",
                    "why": "Prevent scope drift and regressions outside the requested repair.",
                },
            }
        )
    data["context_history"] = [context_snapshot(data["context"], "Case intake")]
    transition(
        data,
        "critique",
        "start",
        "Case created; dataviz-critique of the original artifact is required",
    )
    write_json(case_dir / "case.json", data)
    pointer = active_pointer(args.session)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(case_dir) + "\n", encoding="utf-8")
    print(json.dumps({"case_id": case_id, "case_dir": str(case_dir), "original": original["path"]}))


def cmd_check(args: argparse.Namespace) -> None:
    """Record a concrete intake change or preservation check before the first build."""
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("critique", "design", "build"), "record an intake acceptance check")
    if data["iterations"]:
        raise SystemExit("Use feedback after the first candidate; intake checks must precede iteration 1")
    number = len(data["request_checks"]) + 1
    event = {
        "number": number,
        "at": now_iso(),
        "kind": args.kind,
        "text": args.text,
        "acceptance_check": {
            "target": args.target,
            "current": args.current,
            "required": args.required,
            "why": args.why or "",
        },
    }
    data["request_checks"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "request_check": number, "kind": args.kind}))


def cmd_critique(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("critique", "redesign"), "attach a critique repair brief")
    report_path = Path(args.report).expanduser().resolve()
    validated = validate_critique_report(read_json(report_path), data["context_version"])
    event = {
        "number": len(data["critiques"]) + 1,
        "at": now_iso(),
        **validated,
        "report": {"path": str(report_path), "sha256": sha256(report_path)},
        "source_artifact_sha256": data["original"]["sha256"],
    }
    data["critiques"].append(event)
    transition(
        data,
        "design",
        "critique",
        "Structured critique attached; map every fatal and major finding into the design",
    )
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "critique": event["number"], "state": data["state"]}))


def cmd_design_contract(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("design",), "attach a design contract")
    critique = current_critique(data)
    report_path = Path(args.report).expanduser().resolve()
    validated = validate_design_contract(read_json(report_path), critique)
    event = {
        "number": len(data["design_contracts"]) + 1,
        "at": now_iso(),
        **validated,
        "report": {"path": str(report_path), "sha256": sha256(report_path)},
    }
    data["design_contracts"].append(event)
    transition(data, "build", "design-contract", "Complete implementation contract attached")
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "design_contract": event["number"], "state": data["state"]}))


def cmd_revision_contract(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("revise",), "attach a revision contract")
    report_path = Path(args.report).expanduser().resolve()
    validated = validate_revision_contract(read_json(report_path), data)
    event = {
        "number": len(data["revision_contracts"]) + 1,
        "at": now_iso(),
        "context_version": data["context_version"],
        **validated,
        "report": {"path": str(report_path), "sha256": sha256(report_path)},
    }
    data["revision_contracts"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "revision_contract": event["number"], "state": data["state"]}))


def cmd_renderer_selection(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("build", "revise"), "record renderer selection")
    report_path = Path(args.report).expanduser().resolve()
    validated = validate_renderer_selection(read_json(report_path))
    event = {
        "number": len(data["renderer_selections"]) + 1,
        "at": now_iso(),
        "context_version": data["context_version"],
        **validated,
        "report": {"path": str(report_path), "sha256": sha256(report_path)},
    }
    data["renderer_selections"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "renderer_selection": event["number"], "selected": event["selected"]}))


def cmd_semantic_preflight(args: argparse.Namespace) -> None:
    """Record the creator's semantic audit before rendering under this context."""
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("build", "revise", "redesign"), "record a semantic preflight")
    if data["iterations"] and data["iterations"][-1].get("context_version") == data["context_version"]:
        latest_iteration = data["iterations"][-1]["number"]
        evaluated = any(
            item["iteration"] == latest_iteration for item in data.get("evaluations", [])
        )
        if not evaluated:
            raise SystemExit(
                f"Evaluate iteration {latest_iteration} before replacing its semantic preflight"
            )
    report_path = Path(args.report).expanduser().resolve()
    validated = validate_semantic_preflight(read_json(report_path), data["context_version"])
    event = {
        "number": len(data["semantic_preflights"]) + 1,
        "at": now_iso(),
        **validated,
        "report_sha256": sha256(report_path),
    }
    data["semantic_preflights"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "semantic_preflight": event["number"],
                "context_version": event["context_version"],
            }
        )
    )


def cmd_feedback(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ACTIVE_STATES + PAUSED_STATES, "record feedback")
    number = len(data["feedback"]) + 1
    supersedes: list[int] = []
    if args.supersedes:
        try:
            supersedes = [int(value.strip()) for value in args.supersedes.split(",") if value.strip()]
        except ValueError as exc:
            raise SystemExit("--supersedes must be a comma-separated list of feedback numbers") from exc
        if len(supersedes) != len(set(supersedes)):
            raise SystemExit("--supersedes cannot repeat a feedback number")
        invalid = [value for value in supersedes if value < 1 or value >= number]
        if invalid:
            raise SystemExit(
                "--supersedes must reference earlier feedback numbers: "
                + ", ".join(str(value) for value in invalid)
            )
        for value in supersedes:
            prior = data["feedback"][value - 1]
            if prior.get("superseded_by_feedback"):
                raise SystemExit(
                    f"Feedback {value} was already superseded by feedback "
                    f"{prior['superseded_by_feedback']}"
                )
            prior["superseded_by_feedback"] = number
    supersedes_actions: list[str] = []
    if args.supersedes_actions:
        supersedes_actions = [
            value.strip() for value in args.supersedes_actions.split(",") if value.strip()
        ]
        if len(supersedes_actions) != len(set(supersedes_actions)):
            raise SystemExit("--supersedes-actions cannot repeat an action id")
        latest_evaluation = data.get("evaluations", [])[-1] if data.get("evaluations") else {}
        known_actions = {
            item["id"] for item in latest_evaluation.get("open_required_actions", [])
        }
        invalid_actions = [value for value in supersedes_actions if value not in known_actions]
        if invalid_actions:
            raise SystemExit(
                "--supersedes-actions must reference open evaluator action ids: "
                + ", ".join(invalid_actions)
            )
    event = {
        "number": number,
        "at": now_iso(),
        "text": args.text,
        "supersedes": supersedes,
        "supersedes_actions": supersedes_actions,
        "acceptance_check": {
            "target": args.target,
            "current": args.current,
            "required": args.required,
            "why": args.why or "",
        },
    }
    data["feedback"].append(event)
    if data["state"] == "user_review":
        transition(data, "revise", "feedback", "User correction requires another candidate")
    else:
        data["updated_at"] = now_iso()
    write_json(path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "feedback": event["number"],
                "state": data["state"],
                "resume_required": data["state"] in PAUSED_STATES,
            }
        )
    )


def cmd_iterate(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("build", "revise"), "record an iteration")
    build_state = data["state"]
    critique = current_critique(data)
    design_contract = current_design_contract(data, critique)
    renderer_selection = current_renderer_selection(data)
    revision_contract = None
    if build_state == "revise":
        revision_contract = next(
            (
                item
                for item in reversed(data.get("revision_contracts", []))
                if item.get("source_iteration") == data["iterations"][-1]["number"]
                and item.get("context_version") == data["context_version"]
            ),
            None,
        )
        if revision_contract is None:
            raise SystemExit(
                "Revise requires a complete revision contract covering every open action and user correction"
            )
    semantic_preflight = require_current_semantic_preflight(data)
    if data["iterations"]:
        latest = data["iterations"][-1]["number"]
        evaluated = any(item["iteration"] == latest for item in data.get("evaluations", []))
        cancelled = bool(data["iterations"][-1].get("cancelled_at"))
        if not evaluated and not cancelled:
            raise SystemExit(f"Evaluate iteration {latest} before recording another iteration")
    number = len(data["iterations"]) + 1
    source = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Artifact not found: {source}")
    validate_deliverable(source)
    source_sha = sha256(source)
    duplicate = next(
        (
            item
            for item in data["iterations"]
            if item["artifact"]["sha256"] == source_sha
            and item.get("context_version", 1) == data.get("context_version", 1)
        ),
        None,
    )
    if duplicate:
        raise SystemExit(
            f"Artifact is unchanged from iteration {duplicate['number']} under context version "
            f"{data.get('context_version', 1)}; change the artifact or context before reviewing again"
        )
    ext = source.suffix.lower() or ".bin"
    manifest_source = None
    validated_manifest = None
    validated_sidecars: dict[str, tuple[Path, str]] = {}
    if args.bundle_manifest:
        manifest_source = Path(args.bundle_manifest).expanduser().resolve()
        validated_manifest = read_json(manifest_source)
        if validated_manifest.get("artifact", {}).get("sha256") != source_sha:
            raise SystemExit("Render bundle manifest does not match the iteration artifact hash")
        manifest_selection = validated_manifest.get("renderer_selection", {})
        manifest_renderer = (
            manifest_selection.get("selected") or validated_manifest.get("renderer")
        )
        if manifest_renderer != renderer_selection["selected"]:
            raise SystemExit(
                "Render bundle renderer does not match the recorded renderer selection"
            )
        if (
            manifest_renderer == "matplotlib"
            and renderer_selection["probe"]["renderers"]["ggplot2"]["available"]
            and renderer_selection["requested"] != "matplotlib"
            and not renderer_selection.get("reason")
        ):
            raise SystemExit(
                "Matplotlib render is unexplained even though ggplot2 was available"
            )
        for key, suffix in (
            ("chart_spec", "chart-spec.json"),
            ("layout_metadata", "layout-metadata.json"),
        ):
            item = validated_manifest.get(key)
            if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
                raise SystemExit(f"Render bundle manifest is missing {key}")
            sidecar_source = Path(item["path"]).expanduser().resolve()
            if not sidecar_source.is_file() or sha256(sidecar_source) != item["sha256"]:
                raise SystemExit(f"Render bundle {key} hash does not match its file")
            if key == "layout_metadata":
                layout_document = read_json(sidecar_source)
                if layout_document.get("artifact", {}).get("sha256") != source_sha:
                    raise SystemExit(
                        "Render bundle layout metadata does not match the iteration artifact hash"
                    )
            validated_sidecars[key] = (sidecar_source, suffix)

    artifact = copy_artifact(source, case_dir / f"iteration-{number:02d}{ext}")
    render_bundle = None
    if validated_manifest is not None and manifest_source is not None:
        sidecars: dict[str, dict] = {}
        for key, (sidecar_source, suffix) in validated_sidecars.items():
            sidecars[key] = copy_artifact(
                sidecar_source,
                case_dir / f"iteration-{number:02d}-{suffix}",
            )
        manifest_copy = copy_artifact(
            manifest_source,
            case_dir / f"iteration-{number:02d}-manifest.json",
        )
        render_bundle = {"manifest": manifest_copy, **sidecars}
    event = {
        "number": number,
        "at": now_iso(),
        "summary": args.summary or "",
        "artifact": artifact,
        "feedback_count": len(data["feedback"]),
        "request_check_count": len(data.get("request_checks", [])),
        "context_version": data.get("context_version", 1),
        "semantic_preflight": semantic_preflight["number"],
        "critique": critique["number"],
        "design_contract": design_contract["number"],
        "revision_contract": revision_contract["number"] if revision_contract else None,
        "renderer_selection": renderer_selection["number"],
        "renderer": renderer_selection["selected"],
        "presentation_checks_required": True,
    }
    if render_bundle:
        event["render_bundle"] = render_bundle
    data["iterations"].append(event)
    transition(data, "blind_review", "iterate", "Candidate recorded; independent blind review required", event)
    write_json(path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "iteration": number,
                "path": artifact["path"],
                "state": data["state"],
                "budget": budget_status(data),
            }
        )
    )


def cmd_inspect(args: argparse.Namespace) -> None:
    """Attach deterministic inspection evidence to the latest exact iteration."""
    case_dir = resolve_case(args)
    case_path = case_dir / "case.json"
    data = load_case(case_path)
    require_state(data, ("blind_review",), "record deterministic inspection")
    if not data["iterations"]:
        raise SystemExit("Cannot inspect a case with no recorded iteration")
    iteration = data["iterations"][-1]
    if iteration.get("inspection"):
        raise SystemExit(f"Iteration {iteration['number']} already has deterministic inspection")
    request_path = case_dir / f"review-blind-request-{iteration['number']:02d}.json"
    if request_path.exists():
        raise SystemExit("Record deterministic inspection before creating the blind review request")
    report_path = Path(args.report).expanduser().resolve()
    report = read_json(report_path)
    if report.get("artifact", {}).get("sha256") != iteration["artifact"]["sha256"]:
        raise SystemExit("Inspection report artifact hash does not match the recorded iteration")
    if not isinstance(report.get("checks_complete"), bool):
        raise SystemExit("Inspection report checks_complete must be true or false")
    if not isinstance(report.get("passes_geometry_checks"), bool):
        raise SystemExit("Inspection report passes_geometry_checks must be true or false")
    defects = report.get("defects")
    if not isinstance(defects, list):
        raise SystemExit("Inspection report defects must be a list")
    for defect in defects:
        if not isinstance(defect, dict) or not isinstance(defect.get("code"), str) or not defect[
            "code"
        ].strip():
            raise SystemExit("Each inspection defect requires a non-empty code")
        if defect.get("severity") not in ("high", "medium", "low"):
            raise SystemExit("Each inspection defect requires high, medium, or low severity")
    blocking_defects = [
        defect for defect in defects if defect["severity"] in ("high", "medium")
    ]
    expected_pass = report["checks_complete"] and not blocking_defects
    if report["passes_geometry_checks"] != expected_pass:
        raise SystemExit(
            "Inspection passes_geometry_checks is inconsistent with completeness and defects"
        )

    metadata = report.get("layout_metadata")
    stored_metadata = None
    if metadata is not None:
        if not isinstance(metadata, dict) or not metadata.get("path") or not metadata.get("sha256"):
            raise SystemExit("Inspection report layout_metadata is invalid")
        source_metadata = Path(metadata["path"]).expanduser().resolve()
        if not source_metadata.is_file() or sha256(source_metadata) != metadata["sha256"]:
            raise SystemExit("Inspection layout metadata hash does not match its file")
        metadata_document = read_json(source_metadata)
        if metadata_document.get("artifact", {}).get("sha256") != iteration["artifact"][
            "sha256"
        ]:
            raise SystemExit(
                "Inspection layout metadata does not match the recorded iteration artifact"
            )
        bundled = iteration.get("render_bundle", {}).get("layout_metadata")
        if bundled and bundled.get("sha256") == metadata["sha256"]:
            stored_metadata = bundled
        else:
            stored_metadata = copy_artifact(
                source_metadata,
                case_dir / f"iteration-{iteration['number']:02d}-inspection-layout.json",
            )
        report["layout_metadata"] = {
            "path": stored_metadata["path"],
            "sha256": stored_metadata["sha256"],
        }

    report["artifact"]["path"] = iteration["artifact"]["path"]
    stored_views: list[dict] = []
    raw_views = report.get("review_views", [])
    if not isinstance(raw_views, list):
        raise SystemExit("Inspection review_views must be a list")
    for index, view in enumerate(raw_views, start=1):
        if not isinstance(view, dict) or not view.get("path") or not view.get("sha256"):
            raise SystemExit("Each inspection review view requires path and sha256")
        view_source = Path(view["path"]).expanduser().resolve()
        if not view_source.is_file() or sha256(view_source) != view["sha256"]:
            raise SystemExit("Inspection review view hash does not match its file")
        stored_views.append(
            copy_artifact(
                view_source,
                case_dir / f"iteration-{iteration['number']:02d}-review-view-{index:02d}{view_source.suffix}",
            )
        )
    report["review_views"] = stored_views
    stored_report = case_dir / f"inspection-{iteration['number']:02d}.json"
    write_json(stored_report, report)
    inspection = {
        "path": str(stored_report),
        "sha256": sha256(stored_report),
        "checks_complete": report["checks_complete"],
        "passes_geometry_checks": report["passes_geometry_checks"],
        "defect_codes": [
            item.get("code")
            for item in defects
            if isinstance(item, dict) and item.get("code")
        ],
        "blocking_defect_codes": [item["code"] for item in blocking_defects],
        "layout_metadata": stored_metadata,
        "review_views": stored_views,
    }
    previous_inspection = next(
        (
            item.get("inspection")
            for item in reversed(data["iterations"][:-1])
            if item.get("inspection")
        ),
        None,
    )
    if previous_inspection:
        previous_report = read_json(Path(previous_inspection["path"]))
        signature = lambda item: (
            item.get("code"),
            tuple(sorted(str(value) for value in item.get("element_ids", []))),
        )
        before = {signature(item): item for item in previous_report.get("defects", [])}
        after = {signature(item): item for item in report.get("defects", [])}
        comparison_report = {
            "schema_version": SCHEMA_VERSION,
            "before_iteration": iteration["number"] - 1,
            "after_iteration": iteration["number"],
            "before_artifact_sha256": previous_report["artifact"]["sha256"],
            "after_artifact_sha256": report["artifact"]["sha256"],
            "resolved_defects": [before[key] for key in sorted(set(before) - set(after))],
            "introduced_defects": [after[key] for key in sorted(set(after) - set(before))],
            "persistent_defects": [after[key] for key in sorted(set(after) & set(before))],
        }
        comparison_path = case_dir / f"comparison-{iteration['number'] - 1:02d}-{iteration['number']:02d}.json"
        write_json(comparison_path, comparison_report)
        inspection["comparison"] = {
            "path": str(comparison_path),
            "sha256": sha256(comparison_path),
            "introduced_defect_codes": [
                item["code"] for item in comparison_report["introduced_defects"]
            ],
            "persistent_defect_codes": [
                item["code"] for item in comparison_report["persistent_defects"]
            ],
            "resolved_defect_codes": [
                item["code"] for item in comparison_report["resolved_defects"]
            ],
        }
    iteration["inspection"] = inspection
    transition(
        data,
        "blind_review",
        "inspect",
        "Exact artifact inspected; independent blind evaluation may begin",
        iteration,
    )
    write_json(case_path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "iteration": iteration["number"],
                "inspection": inspection,
            }
        )
    )


def cmd_evaluate(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("context_reveal",), "record an evaluation")
    if not data["iterations"]:
        raise SystemExit("Cannot evaluate a case with no recorded iteration")
    iteration_number = args.iteration or data["iterations"][-1]["number"]
    iterations = {item["number"]: item for item in data["iterations"]}
    if iteration_number not in iterations:
        raise SystemExit(f"Iteration {iteration_number} does not exist")
    if any(item["iteration"] == iteration_number for item in data.get("evaluations", [])):
        raise SystemExit(f"Iteration {iteration_number} already has an evaluation")
    report_path = Path(args.report).expanduser().resolve()
    if not report_path.is_file():
        raise SystemExit(f"Review report not found: {report_path}")
    try:
        raw_report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read review report {report_path}: {exc}") from exc
    reveal_path = case_dir / f"review-reveal-{iteration_number:02d}.json"
    if not reveal_path.is_file():
        raise SystemExit(f"Review request not found for iteration {iteration_number}; run review-request first")
    reveal = read_json(reveal_path)
    blind_response_path = Path(reveal["blind_response_path"])
    if not blind_response_path.is_file():
        raise SystemExit(f"Blind response not found: {blind_response_path}")
    blind_response_sha = sha256(blind_response_path)
    if blind_response_sha != reveal.get("blind_response_sha256"):
        raise SystemExit("Blind response changed after intent was revealed")
    blind_response = validate_blind_response(read_json(blind_response_path), iterations[iteration_number])
    creator = data.get("creator") or f"session:{data['session_id']}"
    carry_actions = open_required_actions(data, iterations[iteration_number])
    acceptance_checks = active_acceptance_checks(data, iterations[iteration_number])
    critique_contract = critique_for_iteration(data, iterations[iteration_number])
    report = validate_review_report(
        raw_report,
        iterations[iteration_number],
        creator,
        reveal["review_token"],
        blind_response,
        blind_response_sha,
        carry_actions,
        acceptance_checks,
        critique_contract,
    )
    number = len(data.setdefault("evaluations", [])) + 1
    stored_report = case_dir / f"evaluation-{number:02d}.json"
    if report_path != stored_report.resolve():
        shutil.copy2(report_path, stored_report)
    event = {
        "number": number,
        "at": now_iso(),
        "iteration": iteration_number,
        "verdict": report["verdict"],
        "scope": report["scope"],
        "tested_size": report["tested_size"],
        "reviewer": report["reviewer"],
        "reviewer_role": report["reviewer_role"],
        "creator": creator,
        "blind_response": {"path": str(blind_response_path), "sha256": blind_response_sha},
        "blind_reads": report["blind_reads"],
        "gates": {name: item["result"] for name, item in report["gates"].items()},
        "gate_required": {name: item["required"] for name, item in report["gates"].items()},
        "gate_evidence": {name: item["evidence"] for name, item in report["gates"].items()},
        "release_checks": report["release_checks"],
        "presentation_checks": report["presentation_checks"],
        "semantic_checks": report["semantic_checks"],
        "carry_forward_checks": report["carry_forward_checks"],
        "acceptance_checks": report["acceptance_checks"],
        "critique_checks": report["critique_checks"],
        "codes": report["codes"],
        "required_actions": report["required_actions"],
        "baseline_concerns": report["baseline_concerns"],
        "report": {"path": str(stored_report), "sha256": sha256(stored_report)},
        "context_version": report["context_version"],
    }
    if iterations[iteration_number].get("inspection"):
        event["deterministic_inspection"] = iterations[iteration_number]["inspection"]
    event["open_required_actions"] = update_open_required_actions(
        carry_actions,
        report["carry_forward_checks"],
        report["required_actions"],
        number,
    )
    stalled = update_stall_count(data, event)
    data["evaluations"].append(event)
    update_best_candidate(data, event, iterations[iteration_number])
    if report["verdict"] == "Send":
        transition(data, "user_review", "evaluate", "All required release gates passed", iterations[iteration_number])
    elif report["verdict"] == "Not evaluable":
        missing_kind = (
            "missing_evidence"
            if report["gates"]["Evidence"]["result"] == "Unknown"
            else "missing_context"
        )
        stop_case(
            data,
            missing_kind,
            "Required evidence or context is unavailable; human input is needed",
            "evaluate",
        )
    elif stalled:
        stop_case(
            data,
            "no_progress",
            "Failure codes and gate results repeated without movement",
            "evaluate",
        )
    else:
        exhausted = budget_status(data)["exhausted"]
        if exhausted:
            stop_case(
                data,
                exhausted[0],
                f"Evaluator requested {report['verdict']}, but {exhausted[0].replace('_', ' ')} is exhausted",
                "evaluate",
            )
        else:
            target = "revise" if report["verdict"] == "Revise" else "redesign"
            transition(
                data,
                target,
                "evaluate",
                f"Independent reviewer verdict: {report['verdict']}",
                iterations[iteration_number],
            )
    write_json(path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "evaluation": event["number"],
                "iteration": iteration_number,
                "verdict": report["verdict"],
                "state": data["state"],
                "stalled_evaluations": data["stalled_evaluations"],
                "best_candidate": data["best_candidate"],
            }
        )
    )


def cmd_review_request(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    data = load_case(case_dir / "case.json")
    require_state(data, ("blind_review",), "request a blind review")
    if not data["iterations"]:
        raise SystemExit("Cannot request a review with no recorded iteration")
    iteration = data["iterations"][-1]
    if any(item["iteration"] == iteration["number"] for item in data.get("evaluations", [])):
        raise SystemExit(f"Iteration {iteration['number']} already has an evaluation")
    if not iteration.get("inspection"):
        raise SystemExit("Inspect the exact recorded artifact before requesting independent evaluation")

    skill_root = Path(__file__).resolve().parent.parent
    if skill_root.name in ("claude", "codex"):
        skill_path = skill_root.parents[1] / "dataviz-eval" / skill_root.name / "SKILL.md"
    else:
        skill_path = skill_root.parent / "dataviz-eval" / "SKILL.md"
    blind_response_path = case_dir / f"review-blind-response-{iteration['number']:02d}.json"
    reveal_path = case_dir / f"review-reveal-{iteration['number']:02d}.json"
    blind_request = {
        "case_id": data["case_id"],
        "iteration": iteration["number"],
        "original": data["original"]["path"],
        "artifact": iteration["artifact"]["path"],
        "artifact_sha256": iteration["artifact"]["sha256"],
        "context_version": iteration.get("context_version", 1),
        "deterministic_inspection": iteration.get("inspection"),
        "required_review_views": iteration.get("inspection", {}).get("review_views", []),
        "revision_comparison": iteration.get("inspection", {}).get("comparison"),
        "dataviz_eval_skill": str(skill_path),
        "blind_response_path": str(blind_response_path),
        "reveal_path": str(reveal_path),
        "blind_submit_command": (
            f'python3 "{Path(__file__).resolve()}" blind-submit --case "{data["case_id"]}"'
        ),
        "review_instructions": [
            "You are a fresh independent release reviewer, not the chart creator.",
            "Inspect the original and exact delivered artifact; the intent reveal does not exist yet.",
            "Inspect the artifact visually first, then incorporate deterministic_inspection when present; it is bound to the same artifact hash.",
            "Write reviewer, iteration, artifact_sha256, expert, audience, and the five-part semantics object to blind_response_path.",
            "Before reveal, state the visible reading and uncertainty for measure, time_context, universe_denominator, claim_strength, and audience_units. Use Unknown when the artifact does not establish an answer.",
            "After saving the blind response, run blind_submit_command to freeze it and create reveal_path.",
            "Then open reveal_path and finish the gate review in this same reviewer context.",
            "Do not inspect creator reasoning, claimed fixes, intended verdict, or rendering code.",
        ],
    }
    target = case_dir / f"review-blind-request-{iteration['number']:02d}.json"
    if target.exists():
        raise SystemExit(f"Blind review request already exists for iteration {iteration['number']}")
    if reveal_path.exists():
        raise SystemExit(f"Review reveal already exists for iteration {iteration['number']}")
    write_json(target, blind_request)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "iteration": iteration["number"],
                "request": str(target),
                "blind_response": str(blind_response_path),
            }
        )
    )


def cmd_blind_submit(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    case_path = case_dir / "case.json"
    data = load_case(case_path)
    require_state(data, ("blind_review",), "submit a blind review")
    if not data["iterations"]:
        raise SystemExit("Cannot submit a blind review with no recorded iteration")
    iteration = data["iterations"][-1]
    if any(item["iteration"] == iteration["number"] for item in data.get("evaluations", [])):
        raise SystemExit(f"Iteration {iteration['number']} already has an evaluation")
    reveal_path = case_dir / f"review-reveal-{iteration['number']:02d}.json"
    if reveal_path.exists():
        raise SystemExit(f"Blind response for iteration {iteration['number']} was already submitted")
    blind_response_path = case_dir / f"review-blind-response-{iteration['number']:02d}.json"
    if not blind_response_path.is_file():
        raise SystemExit(f"Blind response not found: {blind_response_path}")
    blind_response = validate_blind_response(read_json(blind_response_path), iteration)
    creator = data.get("creator") or f"session:{data['session_id']}"
    if blind_response["reviewer"] == creator:
        raise SystemExit("Chart creator and blind reviewer must be different identities")

    response_path = case_dir / f"review-response-{iteration['number']:02d}.json"
    review_token = token_hex(16)
    review_context = context_at_version(data, iteration.get("context_version", 1))
    context_values = {
        name: detail["value"] for name, detail in review_context["fields"].items()
    }
    rating_template = {
        name: {
            "required": True if name in CORE_GATE_NAMES else "<true if scope requires this gate; otherwise false>",
            "result": "<Pass|Concern|Fail|Unknown>",
            "evidence": "<specific observed evidence>",
        }
        for name in GATE_NAMES
    }
    release_template = {
        name: {
            "result": "<Pass|Concern|Fail|Unknown>",
            "evidence": "<specific observed evidence>",
            "stress_test": "<most failure-prone element, pair, or region inspected and why it survives or fails>",
        }
        for name in RELEASE_CHECK_NAMES
    }
    presentation_template = {
        name: {
            "result": "<Pass|Concern|Fail|Unknown>",
            "evidence": "<specific observed evidence>",
            "stress_test": "<most failure-prone copy or colour relationship inspected>",
        }
        for name in PRESENTATION_CHECK_NAMES
    }
    semantic_template = {
        name: {
            "result": "<Pass|Concern|Fail|Unknown>",
            "misleading_interpretation": "<materially wrong reading a viewer could take, or 'No material competing reading observed'>",
            "defensible_interpretation": "<reading supported by the artifact and evidence>",
            "evidence": "<specific title, mark, scale, unit, boundary, universe, or comparator inspected>",
        }
        for name in SEMANTIC_DIMENSIONS
    }
    carry_actions = open_required_actions(data, iteration)
    acceptance_checks = active_acceptance_checks(data, iteration)
    semantic_preflight = semantic_preflight_for_iteration(data, iteration)
    critique_contract = critique_for_iteration(data, iteration)
    design_contract = next(
        (
            item
            for item in data.get("design_contracts", [])
            if item.get("number") == iteration.get("design_contract")
        ),
        None,
    )
    if semantic_preflight is None:
        raise SystemExit("Iteration is missing its context-matched semantic preflight")
    reveal = {
        "case_id": data["case_id"],
        "iteration": iteration["number"],
        "context_version": iteration.get("context_version", 1),
        "review_token": review_token,
        "context": review_context,
        "user_request": "\n\n".join(item["text"] for item in review_context.get("prompts", [])),
        "audience": context_values.get("audience", ""),
        "medium": context_values.get("medium", ""),
        "active_user_corrections": [item["text"] for item in acceptance_checks],
        "active_acceptance_checks": acceptance_checks,
        "semantic_preflight": semantic_preflight,
        "critique_contract": critique_contract,
        "design_contract": design_contract,
        "blind_semantics": blind_response["semantics"],
        "carry_forward_required_actions": carry_actions,
        "required_review_views": iteration.get("inspection", {}).get("review_views", []),
        "revision_comparison": iteration.get("inspection", {}).get("comparison"),
        "release_instructions": [
            "Re-run all five semantic dimensions against the artifact and source; the creator preflight is a hypothesis, not evidence.",
            "Challenge inferred context against the verbatim user_request and source. Do not grade an unsupported inferred question or message as user intent.",
            "For each semantic check, state the misleading interpretation, the defensible interpretation, and direct observed evidence.",
            "Inspect every carry_forward_required_action directly in the current artifact.",
            "Record one carry_forward_check per id; do not infer resolution from an overall gate.",
            "An unresolved prior action prevents Send and remains active for the next iteration.",
            "Inspect every active_acceptance_check directly in the current artifact.",
            "Inspect every fatal and major critique finding against its observable condition; none can be silently dropped.",
            "Inspect all panels, every repeated structure, every required_review_view, and the neighbouring layout zones around each proposed pass.",
            "Use revision_comparison to identify introduced, persistent, and resolved defects; an introduced blocking defect prevents Send.",
            "Record one acceptance_check result per id; user checks are release gates, not prose context.",
            "Send is invalid unless every active, non-superseded user acceptance check passes.",
            "Treat active user checks as the change contract. A required action must not conflict with a change or preservation check.",
            "For a narrow repair, test changed regions absolutely and untouched regions for preservation and regression. Put unchanged pre-existing defects outside the authorised scope in baseline_concerns; do not turn them into required actions unless they block the requested correction or materially mislead.",
            "A later user correction outranks an older evaluator preference. Do not preserve or restore an element the user explicitly asked to remove.",
            "After the blind read is frozen, open and apply any installed writing, brand, and visual-style skills relevant to this user or project.",
            "Colour distinction is a separate release gate: inspect the closest competing encoded colours at delivery size and under grayscale or a common colour-vision deficiency; prose saying the palette is consistent is not evidence.",
            "Copy style is a separate release gate: inspect titles, subtitles, annotations, and notes against the applicable writing/style skill; generic AI phrasing cannot pass merely because the claim is accurate.",
        ],
        "blind_response_path": str(blind_response_path),
        "blind_response_sha256": sha256(blind_response_path),
        "response_path": str(response_path),
        "response_template": {
            "reviewer": blind_response["reviewer"],
            "reviewer_role": "independent",
            "review_token": review_token,
            "blind_response_sha256": sha256(blind_response_path),
            "iteration": iteration["number"],
            "artifact_sha256": iteration["artifact"]["sha256"],
            "deterministic_inspection_sha256": iteration.get("inspection", {}).get("sha256"),
            "context_version": iteration.get("context_version", 1),
            "scope": "<evidence scope, audience, and medium>",
            "tested_size": "<actual or representative viewing condition>",
            "blind_reads": {
                "expert": blind_response["expert"],
                "audience": blind_response["audience"],
            },
            "blind_semantics": blind_response["semantics"],
            "gates": rating_template,
            "semantic_checks": semantic_template,
            "release_checks": release_template,
            "presentation_checks": presentation_template,
            "carry_forward_checks": [
                {
                    "id": item["id"],
                    "result": "<Pass|Concern|Fail|Unknown>",
                    "evidence": "<direct observation of the named target in this artifact>",
                }
                for item in carry_actions
            ],
            "acceptance_checks": [
                {
                    "id": item["id"],
                    "result": "<Pass|Concern|Fail|Unknown>",
                    "evidence": "<direct observation of the named user check in this artifact>",
                }
                for item in acceptance_checks
            ],
            "critique_checks": [
                {
                    "id": item["id"],
                    "result": "<Pass|Concern|Fail|Unknown>",
                    "evidence": "<direct evidence that the original critique condition is closed or remains open>",
                }
                for item in critique_findings(critique_contract)
            ] if critique_contract else [],
            "verdict": "<Send|Revise|Redesign|Not evaluable>",
            "codes": ["<failure code; empty list only for Send>"],
            "required_actions": [
                {
                    "target": "<element or relationship>",
                    "from": "<current observed state>",
                    "to": "<minimum passing state>",
                    "why": "<reader consequence>",
                    "codes": ["<failure code>"],
                    "affected_zones": ["<title|subtitle|legend|plot|annotation|footer|panel>"]
                }
            ],
            "baseline_concerns": ["<unchanged pre-existing issue outside authorised scope; empty when none>"],
        },
    }
    write_json(reveal_path, reveal)
    transition(
        data,
        "context_reveal",
        "blind-submit",
        "Blind read frozen; context revealed to the same independent reviewer",
        iteration,
    )
    write_json(case_path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "iteration": iteration["number"],
                "reveal": str(reveal_path),
                "response": str(response_path),
            }
        )
    )


def write_review_packet(case_dir: Path, data: dict) -> Path:
    context_values = {
        name: detail["value"] or "(unknown)"
        for name, detail in data["context"]["fields"].items()
    }
    acceptance = data.get("acceptance") or {}
    lines = [
        f"# Dataviz repair case {data['case_id']}",
        "",
        f"- State: {data['state']}",
        f"- Context version: {data['context_version']}",
        f"- Request: {data['request'] or '(none)'}",
        f"- Audience: {context_values['audience']}",
        f"- Purpose: {context_values['purpose']}",
        f"- Question: {context_values['question']}",
        f"- Hypothesis: {context_values['hypothesis']}",
        f"- Message: {context_values['message']}",
        f"- Medium: {context_values['medium']}",
        f"- Original: `{data['original']['path']}`",
        f"- Accepted iteration: {acceptance.get('iteration', '(none)')}",
        f"- Accepted artifact: `{acceptance.get('path', '(none)')}`",
        f"- Best candidate before acceptance: iteration {data['best_candidate']['iteration'] if data.get('best_candidate') else '(none)'}",
        f"- Limits: `{json.dumps(data['limits'], sort_keys=True)}`",
        f"- Usage: `{json.dumps({name: value for name, value in data['telemetry'].items() if name != 'events'}, sort_keys=True)}`",
        f"- Skill snapshot: `{data['skill_snapshot'] or '(not captured)'}`",
        "",
    ]
    if data.get("request_checks"):
        lines.extend(["## Intake acceptance checks", ""])
        for item in data["request_checks"]:
            check = item["acceptance_check"]
            lines.append(
                f"{item['number']}. [{item.get('kind', 'change')}] {check['target']} - "
                f"{check['current']} -> {check['required']}"
            )
        lines.append("")
    lines.extend(["## User feedback", ""])
    if data["feedback"]:
        for item in data["feedback"]:
            check = item.get("acceptance_check")
            lines.append(f"{item['number']}. {item['text']}")
            if check:
                lines.append(
                    f"   - Check: {check['target']} - {check['current']} -> {check['required']}"
                )
    else:
        lines.append("No user correction was recorded.")
    lines.extend(["", "## Iterations", ""])
    for item in data["iterations"]:
        cancellation = f"; cancelled: {item['cancel_reason']}" if item.get("cancelled_at") else ""
        lines.append(
            f"{item['number']}. `{item['artifact']['path']}` - context v{item.get('context_version', 1)}; "
            f"{item['summary'] or '(no summary)'}{cancellation}"
        )
    lines.extend(["", "## Evaluations", ""])
    evaluations = data.get("evaluations", [])
    if evaluations:
        for item in evaluations:
            gates = ", ".join(
                f"{name}={result} ({'required' if item.get('gate_required', {}).get(name, True) else 'not required'})"
                for name, result in item["gates"].items()
            )
            codes = ", ".join(item["codes"]) or "none"
            release_checks = ", ".join(
                f"{name}={detail['result']}"
                for name, detail in item.get("release_checks", {}).items()
            ) or "(not recorded)"
            presentation_checks = ", ".join(
                f"{name}={detail['result']}"
                for name, detail in item.get("presentation_checks", {}).items()
            ) or "(not recorded)"
            lines.extend(
                [
                    f"{item['number']}. Iteration {item['iteration']}: **{item['verdict']}**",
                    f"   - Scope: {item['scope'] or '(not recorded)'}",
                    f"   - Gates: {gates}",
                    f"   - Codes: {codes}",
                    f"   - Reviewer: {item.get('reviewer', '(legacy self-review)')}",
                    f"   - Tested size: {item.get('tested_size', '(not recorded)')}",
                    f"   - Release checks: {release_checks}",
                    f"   - Presentation checks: {presentation_checks}",
                    f"   - Required actions: {json.dumps(item['required_actions'], ensure_ascii=False) if item.get('required_actions') else 'none'}",
                    f"   - Baseline concerns outside scope: {', '.join(item.get('baseline_concerns', [])) or 'none'}",
                    f"   - Context version: {item.get('context_version', 1)}"
                    + (
                        f"; superseded by v{item['superseded_by_context_version']}"
                        if item.get("superseded_by_context_version")
                        else ""
                    ),
                ]
            )
    else:
        lines.append("No evaluation was recorded.")
    lines.extend(["", "## Loop transitions", ""])
    for item in data.get("transitions", []):
        lines.append(
            f"{item['number']}. `{item.get('from')}` -> `{item['to']}` via `{item['action']}`: {item['reason']}"
        )
    lines.extend(
        [
            "",
            "## Skill diagnosis",
            "",
            "Compare the original, first iteration, accepted iteration, and user feedback.",
            "Classify the miss, choose one owning skill, and make only a reusable change.",
            "",
        ]
    )
    target = case_dir / "review-packet.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def cmd_accept(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ACTIVE_STATES + PAUSED_STATES, "accept a candidate")
    if not data["iterations"]:
        raise SystemExit("Cannot accept a case with no recorded iteration")
    accepted = data["iterations"][-1]
    latest_evaluations = [
        item for item in data.get("evaluations", []) if item["iteration"] == accepted["number"]
    ]
    if not latest_evaluations:
        raise SystemExit(f"Evaluate iteration {accepted['number']} before accepting it")
    evaluation = latest_evaluations[-1]
    override_reason = (args.override_reason or "").strip()
    if evaluation["verdict"] != "Send" and not override_reason:
        raise SystemExit(
            f"Latest verdict is {evaluation['verdict']}; pass --override-reason only after explicit user acceptance"
        )
    accepted_state = "accepted" if evaluation["verdict"] == "Send" else "accepted_with_override"
    data["acceptance"] = {
        "at": now_iso(),
        "iteration": accepted["number"],
        "path": accepted["artifact"]["path"],
        "evaluation": evaluation["number"],
        "evaluation_verdict": evaluation["verdict"],
        "override_reason": override_reason or None,
    }
    transition(
        data,
        accepted_state,
        "accept",
        "User accepted the latest independently evaluated candidate",
        accepted,
    )
    write_json(path, data)
    packet = write_review_packet(case_dir, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "accepted": data["acceptance"]["path"],
                "review_packet": str(packet),
            }
        )
    )


def cmd_diagnose(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, PAUSED_STATES + TERMINAL_STATES, "record a skill diagnosis")
    enforcement = (args.enforcement or "").strip()
    regression_test = (args.regression_test or "").strip()
    if args.classification == "execution-miss" and (not enforcement or not regression_test):
        raise SystemExit(
            "An execution-miss diagnosis requires --enforcement and --regression-test; "
            "another prose rule is not a control"
        )
    event = {
        "number": len(data.get("diagnoses", [])) + 1,
        "at": now_iso(),
        "case_state": data["state"],
        "classification": args.classification,
        "owner": args.owner,
        "lesson": args.lesson,
        "changed_files": [item.strip() for item in args.changed_files.split(",") if item.strip()],
        "enforcement": enforcement or None,
        "regression_test": regression_test or None,
    }
    data.setdefault("diagnoses", []).append(event)
    data["diagnosis"] = event
    data["updated_at"] = now_iso()
    write_json(path, data)
    packet = write_review_packet(case_dir, data)
    with packet.open("a", encoding="utf-8") as handle:
        diagnosis = data["diagnosis"]
        handle.write(f"- Episode: `{diagnosis['number']}` in case state `{diagnosis['case_state']}`\n")
        handle.write(f"- Classification: `{diagnosis['classification']}`\n")
        handle.write(f"- Owning skill: `{diagnosis['owner']}`\n")
        handle.write(f"- Lesson: {diagnosis['lesson']}\n")
        changed = ", ".join(f"`{item}`" for item in diagnosis["changed_files"]) or "none"
        handle.write(f"- Changed files: {changed}\n")
        handle.write(f"- Enforcement: {diagnosis['enforcement'] or 'none'}\n")
        handle.write(f"- Regression test: {diagnosis['regression_test'] or 'none'}\n")
    print(json.dumps({"case_id": data["case_id"], "diagnosis": data["diagnosis"]}))


def cmd_context(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ACTIVE_STATES + PAUSED_STATES, "update context")
    updates = {
        name: getattr(args, name)
        for name in CONTEXT_FIELDS
        if getattr(args, name) is not None
    }
    clear = csv_items(args.clear or "")
    unknown_clear = sorted(set(clear) - set(CONTEXT_FIELDS))
    if unknown_clear:
        raise SystemExit(f"Unknown context fields to clear: {', '.join(unknown_clear)}")
    prompt = (args.text or "").strip()
    if not updates and not clear and not prompt:
        raise SystemExit("Context update requires --text, a structured field, or --clear")

    updates = {
        name: value
        for name, value in updates.items()
        if data["context"]["fields"][name]["value"] != value.strip()
        or data["context"]["fields"][name]["source"] != args.source
    }
    clear = [
        name
        for name in clear
        if data["context"]["fields"][name]["value"]
        or data["context"]["fields"][name]["source"] != "unknown"
    ]
    prompt_changed = bool(prompt) and not (
        data["context"]["prompts"]
        and data["context"]["prompts"][-1]["text"] == prompt
        and data["context"]["prompts"][-1]["source"] == args.source
    )
    if not updates and not clear and not prompt_changed:
        raise SystemExit("Context update makes no material change")

    old_version = data["context"]["version"]
    data["context"]["version"] += 1
    data["context"]["updated_at"] = now_iso()
    if prompt_changed:
        data["context"]["prompts"].append(
            {
                "number": len(data["context"]["prompts"]) + 1,
                "at": now_iso(),
                "text": prompt,
                "source": args.source,
            }
        )
    for name, value in updates.items():
        data["context"]["fields"][name] = context_field(value, args.source)
    for name in clear:
        data["context"]["fields"][name] = context_field(None, "unknown")
    data["context_version"] = data["context"]["version"]
    data["context_history"].append(context_snapshot(data["context"], args.reason))
    data["audience"] = data["context"]["fields"]["audience"]["value"]
    data["medium"] = data["context"]["fields"]["medium"]["value"]

    latest_iteration = data["iterations"][-1] if data["iterations"] else None
    if latest_iteration and data["state"] in ("blind_review", "context_reveal"):
        latest_iteration["cancelled_at"] = now_iso()
        latest_iteration["cancel_reason"] = (
            f"Context changed from version {old_version} to {data['context_version']} before evaluation"
        )
    if data.get("evaluations"):
        latest_evaluation = data["evaluations"][-1]
        if latest_evaluation.get("context_version", 1) == old_version:
            latest_evaluation["superseded_at"] = now_iso()
            latest_evaluation["superseded_by_context_version"] = data["context_version"]

    exhausted = budget_status(data)["exhausted"]
    if exhausted:
        stop_case(
            data,
            exhausted[0],
            f"Context updated, but {exhausted[0].replace('_', ' ')} is exhausted",
            "context-update",
        )
    else:
        target = "critique"
        data["stop"] = None
        transition(
            data,
            target,
            "context-update",
            f"Context changed from version {old_version} to {data['context_version']}",
            latest_iteration,
        )
    write_json(path, data)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "context_version": data["context_version"],
                "state": data["state"],
                "context": data["context"],
                "budget": budget_status(data),
            }
        )
    )


def cmd_status(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    data = load_case(case_dir / "case.json")
    output = json.loads(json.dumps(data))
    output["budget_status"] = budget_status(data)
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_build_check(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ("build", "revise"), "start a build")
    critique = current_critique(data)
    design = current_design_contract(data, critique)
    renderer_selection = current_renderer_selection(data)
    revision_contract = None
    if data["state"] == "revise":
        if not data["iterations"]:
            raise SystemExit("Revise state requires an existing candidate")
        revision_contract = next(
            (
                item
                for item in reversed(data.get("revision_contracts", []))
                if item.get("source_iteration") == data["iterations"][-1]["number"]
                and item.get("context_version") == data["context_version"]
            ),
            None,
        )
        if revision_contract is None:
            raise SystemExit(
                "Attach a revision contract mapping every open evaluator action and user correction"
            )
    preflight = require_current_semantic_preflight(data)
    enforce_build_budget(data, path)
    print(
        json.dumps(
            {
                "case_id": data["case_id"],
                "state": data["state"],
                "next_iteration": len(data["iterations"]) + 1,
                "semantic_preflight": preflight["number"],
                "critique": critique["number"],
                "design_contract": design["number"],
                "revision_contract": revision_contract["number"] if revision_contract else None,
                "renderer_selection": renderer_selection["number"],
                "budget": budget_status(data),
            }
        )
    )


def cmd_limits(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ACTIVE_STATES + PAUSED_STATES, "change loop limits")
    updates = {
        "max_iterations": args.max_iterations,
        "max_stalled_evaluations": args.max_stalled_evaluations,
        "max_elapsed_seconds": args.max_elapsed_minutes * 60
        if args.max_elapsed_minutes is not None
        else None,
        "max_tokens": args.max_tokens,
        "max_cost_usd": args.max_cost_usd,
    }
    proposed = {
        name: value
        for name, value in updates.items()
        if value is not None and value != data["limits"].get(name)
    }
    if not proposed:
        print(json.dumps({"case_id": data["case_id"], "limits": data["limits"], "budget": budget_status(data)}))
        return

    increases = {
        name: value
        for name, value in proposed.items()
        if data["limits"].get(name) is not None and value > data["limits"][name]
    }
    authorization = None
    if increases:
        if not args.authorization:
            raise SystemExit(
                "Increasing an existing stopping limit requires a pre-recorded, "
                "case-bound user authorization grant; pass --authorization <grant-id>"
            )
        authorization = next(
            (
                item
                for item in data.get("limit_authorizations", [])
                if item.get("id") == args.authorization
            ),
            None,
        )
        if authorization is None:
            raise SystemExit("Unknown limit authorization grant for this case")
        if authorization.get("case_id") != data["case_id"]:
            raise SystemExit("Limit authorization is not bound to this case")
        if authorization.get("consumed_at"):
            raise SystemExit("Limit authorization has already been consumed")
        stop = data.get("stop") or {}
        if (
            data.get("state") == "stopped"
            and stop.get("kind") in BUDGET_STOP_KINDS
            and authorization.get("authorized_stop_at") != stop.get("at")
        ):
            raise SystemExit(
                "Limit authorization was not issued for the current budget stop"
            )
        approved = authorization.get("approved_limits") or {}
        if approved != increases:
            raise SystemExit(
                "Limit increase does not exactly match the values approved by the user grant"
            )

    before = dict(data["limits"])
    for name, value in proposed.items():
        data["limits"][name] = value
    change = {
        "number": len(data.setdefault("limit_changes", [])) + 1,
        "at": now_iso(),
        "before": before,
        "after": dict(data["limits"]),
        "changed": proposed,
        "increases": increases,
        "authorization_id": authorization.get("id") if authorization else None,
    }
    data["limit_changes"].append(change)
    if authorization is not None:
        authorization["consumed_at"] = change["at"]
        authorization["limit_change_number"] = change["number"]
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "limits": data["limits"], "budget": budget_status(data), "limit_change": change}))


def cmd_usage(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    existing_iterations = {item["number"] for item in data["iterations"]}
    planned_iteration = len(data["iterations"]) + 1
    planned_usage = (
        args.iteration == planned_iteration
        and data["state"] in ("build", "revise", "redesign")
    )
    if args.iteration is not None and args.iteration not in existing_iterations and not planned_usage:
        raise SystemExit(f"Iteration {args.iteration} does not exist and is not the next planned build")
    event = {
        "number": len(data["telemetry"]["events"]) + 1,
        "at": now_iso(),
        "stage": args.stage,
        "iteration": args.iteration,
        "planned_iteration": planned_usage,
        "calls": args.calls,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "cached_input_tokens": args.cached_input_tokens,
        "total_tokens": args.input_tokens + args.output_tokens,
        "cost_usd": args.cost_usd,
        "latency_seconds": args.latency_seconds,
    }
    data["telemetry"]["events"].append(event)
    for name in (
        "calls",
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "total_tokens",
        "cost_usd",
        "latency_seconds",
    ):
        data["telemetry"][name] += event[name]
    data["telemetry"]["cost_usd"] = round(data["telemetry"]["cost_usd"], 8)
    data["telemetry"]["latency_seconds"] = round(data["telemetry"]["latency_seconds"], 3)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "usage_event": event["number"], "telemetry": data["telemetry"], "budget": budget_status(data)}))


def cmd_stop(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, ACTIVE_STATES, "stop a case")
    stop_case(data, args.kind, args.reason, "stop")
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "state": data["state"], "stop": data["stop"], "best_candidate": data["best_candidate"]}))


def cmd_resume(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = load_case(path)
    require_state(data, PAUSED_STATES, "resume a case")
    stop = data.get("stop") or {}
    if stop.get("kind") in BUDGET_STOP_KINDS:
        change_count = stop.get("limit_change_count", 0)
        approved_after_stop = any(
            item.get("authorization_id") and item.get("increases")
            for item in data.get("limit_changes", [])[change_count:]
        )
        if not approved_after_stop:
            raise SystemExit(
                "A budget-stopped case requires a user-authorized limit increase "
                "recorded after this stop before it can resume"
            )
    exhausted = budget_status(data)["exhausted"]
    if exhausted:
        raise SystemExit(
            f"Cannot resume while {', '.join(item.replace('_', ' ') for item in exhausted)} is exhausted; change limits first"
        )
    target = args.to
    if target is None:
        if not data["iterations"]:
            target = "build"
        else:
            latest = data.get("evaluations", [])[-1] if data.get("evaluations") else None
            target = {
                "Send": "user_review",
                "Redesign": "redesign",
                "Revise": "revise",
                "Not evaluable": "revise",
            }.get(latest.get("verdict") if latest else None, "build")
    if target == "user_review":
        latest = data.get("evaluations", [])[-1] if data.get("evaluations") else None
        if latest is None or latest.get("verdict") != "Send":
            raise SystemExit("Only an independently recorded Send verdict can resume to user_review")
    data["stop"] = None
    transition(data, target, "resume", args.reason)
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "state": data["state"], "budget": budget_status(data)}))


def add_case_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session", default="default", help="stable conversation/session identifier")
    parser.add_argument("--case", help="explicit case id; otherwise use the session's active case")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="start a case and copy the original image")
    start.add_argument("--session", default="default")
    start.add_argument("--image", required=True)
    start.add_argument("--request", default="")
    start.add_argument(
        "--context-source",
        choices=("user", "inferred"),
        default="inferred",
        help="provenance for structured intake fields; use user only for explicitly supplied context",
    )
    start.add_argument("--audience", default="")
    start.add_argument("--purpose", default="")
    start.add_argument("--question", default="")
    start.add_argument("--hypothesis", default="")
    start.add_argument("--message", default="")
    start.add_argument("--medium", default="")
    start.add_argument("--dimensions", default="")
    start.add_argument("--expansion-available", choices=("yes", "no", "unknown"), default="")
    start.add_argument("--source-notes", default="")
    start.add_argument("--preserve", default="")
    start.add_argument("--accessibility", default="")
    start.add_argument("--brand", default="")
    start.add_argument("--tooling", default="")
    start.add_argument("--output-constraints", default="")
    start.add_argument("--skills-root")
    start.add_argument("--creator", help="stable creator identity; defaults to the session")
    start.add_argument("--max-iterations", type=positive_int, default=DEFAULT_MAX_ITERATIONS)
    start.add_argument(
        "--max-stalled-evaluations",
        type=positive_int,
        default=DEFAULT_MAX_STALLED_EVALUATIONS,
    )
    start.add_argument("--max-elapsed-minutes", type=positive_float)
    start.add_argument("--max-tokens", type=positive_int)
    start.add_argument("--max-cost-usd", type=positive_float)
    start.set_defaults(func=cmd_start)

    check = sub.add_parser(
        "check", help="record a concrete intake change or preservation acceptance check"
    )
    add_case_args(check)
    check.add_argument("--kind", choices=("change", "preserve"), default="change")
    check.add_argument("--text", required=True)
    check.add_argument("--target", required=True)
    check.add_argument("--current", required=True)
    check.add_argument("--required", required=True)
    check.add_argument("--why")
    check.set_defaults(func=cmd_check)

    critique = sub.add_parser(
        "critique", help="attach the mandatory structured dataviz-critique repair brief"
    )
    add_case_args(critique)
    critique.add_argument("--report", required=True)
    critique.set_defaults(func=cmd_critique)

    design_contract = sub.add_parser(
        "design-contract", help="map every fatal and major critique finding into implementation"
    )
    add_case_args(design_contract)
    design_contract.add_argument("--report", required=True)
    design_contract.set_defaults(func=cmd_design_contract)

    revision_contract = sub.add_parser(
        "revision-contract", help="map every open evaluator action and user correction into changes"
    )
    add_case_args(revision_contract)
    revision_contract.add_argument("--report", required=True)
    revision_contract.set_defaults(func=cmd_revision_contract)

    renderer_selection = sub.add_parser(
        "renderer-selection", help="record renderer probe and selection evidence"
    )
    add_case_args(renderer_selection)
    renderer_selection.add_argument("--report", required=True)
    renderer_selection.set_defaults(func=cmd_renderer_selection)

    semantic_preflight = sub.add_parser(
        "semantic-preflight",
        help="record the five-part semantic audit required before rendering",
    )
    add_case_args(semantic_preflight)
    semantic_preflight.add_argument(
        "--report",
        required=True,
        help="JSON containing context_version and all required semantic dimensions",
    )
    semantic_preflight.set_defaults(func=cmd_semantic_preflight)

    feedback = sub.add_parser("feedback", help="record user feedback verbatim")
    add_case_args(feedback)
    feedback.add_argument("--text", required=True)
    feedback.add_argument("--target", required=True, help="element or relationship to inspect")
    feedback.add_argument("--current", required=True, help="observable current state")
    feedback.add_argument("--required", required=True, help="observable required state")
    feedback.add_argument("--why", help="reader consequence")
    feedback.add_argument(
        "--supersedes",
        help="comma-separated earlier feedback numbers replaced by this clarification",
    )
    feedback.add_argument(
        "--supersedes-actions",
        help="comma-separated open evaluator action ids replaced by this user correction",
    )
    feedback.set_defaults(func=cmd_feedback)

    iterate = sub.add_parser("iterate", help="copy and record a rendered revision")
    add_case_args(iterate)
    iterate.add_argument("--output", required=True)
    iterate.add_argument("--summary", default="")
    iterate.add_argument(
        "--bundle-manifest",
        help="optional render bundle manifest whose spec and layout sidecars match the output hash",
    )
    iterate.set_defaults(func=cmd_iterate)

    inspect = sub.add_parser(
        "inspect", help="attach deterministic inspection evidence to the latest iteration"
    )
    add_case_args(inspect)
    inspect.add_argument("--report", required=True)
    inspect.set_defaults(func=cmd_inspect)

    evaluate = sub.add_parser("evaluate", help="record a dataviz-eval verdict for an iteration")
    add_case_args(evaluate)
    evaluate.add_argument("--iteration", type=int, help="iteration number; defaults to the latest")
    evaluate.add_argument(
        "--report",
        required=True,
        help="independent review JSON for the exact recorded artifact",
    )
    evaluate.set_defaults(func=cmd_evaluate)

    review_request = sub.add_parser(
        "review-request", help="write a blind independent-review packet for the latest iteration"
    )
    add_case_args(review_request)
    review_request.set_defaults(func=cmd_review_request)

    blind_submit = sub.add_parser(
        "blind-submit", help="freeze the blind response and reveal intent for the same reviewer"
    )
    add_case_args(blind_submit)
    blind_submit.set_defaults(func=cmd_blind_submit)

    accept = sub.add_parser("accept", help="accept the latest recorded revision")
    add_case_args(accept)
    accept.add_argument(
        "--override-reason",
        help="record explicit user acceptance when the latest independent verdict is not Send",
    )
    accept.set_defaults(func=cmd_accept)

    diagnose = sub.add_parser("diagnose", help="record the skill-level diagnosis")
    add_case_args(diagnose)
    diagnose.add_argument("--classification", choices=CLASSIFICATIONS, required=True)
    diagnose.add_argument("--owner", required=True)
    diagnose.add_argument("--lesson", required=True)
    diagnose.add_argument("--changed-files", default="")
    diagnose.add_argument("--enforcement")
    diagnose.add_argument("--regression-test")
    diagnose.set_defaults(func=cmd_diagnose)

    context = sub.add_parser("context", help="append prompt context or update structured context")
    add_case_args(context)
    context.add_argument("--text", help="ordinary free-text context or correction")
    context.add_argument("--source", choices=CONTEXT_SOURCES, default="user")
    context.add_argument("--reason", default="Context updated")
    context.add_argument("--clear", help="comma-separated context fields to mark unknown")
    for field in CONTEXT_FIELDS:
        option = "--" + field.replace("_", "-")
        if field == "expansion_available":
            context.add_argument(option, choices=("yes", "no", "unknown"))
        else:
            context.add_argument(option)
    context.set_defaults(func=cmd_context)

    status = sub.add_parser("status", help="print the active case JSON")
    add_case_args(status)
    status.set_defaults(func=cmd_status)

    build_check = sub.add_parser("build-check", help="verify state and budgets before model work")
    add_case_args(build_check)
    build_check.set_defaults(func=cmd_build_check)

    limits = sub.add_parser("limits", help="show or update loop stopping limits")
    add_case_args(limits)
    limits.add_argument("--max-iterations", type=positive_int)
    limits.add_argument("--max-stalled-evaluations", type=positive_int)
    limits.add_argument("--max-elapsed-minutes", type=positive_float)
    limits.add_argument("--max-tokens", type=positive_int)
    limits.add_argument("--max-cost-usd", type=positive_float)
    limits.add_argument(
        "--authorization",
        help="single-use case-bound grant id recorded from an explicit user turn",
    )
    limits.set_defaults(func=cmd_limits)

    usage = sub.add_parser("usage", help="record token, cost, call, and latency telemetry")
    add_case_args(usage)
    usage.add_argument("--stage", choices=("creator", "reviewer", "renderer", "other"), required=True)
    usage.add_argument("--iteration", type=positive_int)
    usage.add_argument("--calls", type=positive_int, default=1)
    usage.add_argument("--input-tokens", type=nonnegative_int, default=0)
    usage.add_argument("--output-tokens", type=nonnegative_int, default=0)
    usage.add_argument("--cached-input-tokens", type=nonnegative_int, default=0)
    usage.add_argument("--cost-usd", type=nonnegative_float, default=0.0)
    usage.add_argument("--latency-seconds", type=nonnegative_float, default=0.0)
    usage.set_defaults(func=cmd_usage)

    stop = sub.add_parser("stop", help="stop or block a case with a recorded reason")
    add_case_args(stop)
    stop.add_argument("--kind", choices=STOP_KINDS, required=True)
    stop.add_argument("--reason", required=True)
    stop.set_defaults(func=cmd_stop)

    resume = sub.add_parser("resume", help="resume a blocked or stopped case")
    add_case_args(resume)
    resume.add_argument("--reason", required=True)
    resume.add_argument("--to", choices=("build", "revise", "redesign", "user_review"))
    resume.set_defaults(func=cmd_resume)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

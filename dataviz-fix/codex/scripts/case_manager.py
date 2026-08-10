#!/usr/bin/env python3
"""Persist dataviz repair cases without deleting or overwriting artifacts."""

from __future__ import annotations

import argparse
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
CORE_GATE_NAMES = ("Evidence", "Visual reasoning", "Information fit", "Delivery")
RELEASE_CHECK_NAMES = (
    "Visual integrity",
    "Relationship traceability",
    "Spatial economy",
    "Encoding semantics",
    "Delivery robustness",
)
DELIVERABLE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".pdf")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def root_dir() -> Path:
    override = os.getenv("DATAVIZ_FIX_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    hermes_home = os.getenv("HERMES_HOME")
    if hermes_home:
        return Path(hermes_home).expanduser().resolve() / "dataviz-fix"
    if (Path.home() / ".hermes").is_dir():
        return Path.home() / ".hermes" / "dataviz-fix"
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
) -> dict[str, dict[str, object]]:
    if not isinstance(raw, dict):
        raise SystemExit(f"Review report {field!r} must be an object")
    ratings: dict[str, dict[str, object]] = {}
    for name in names:
        item = raw.get(name)
        if not isinstance(item, dict):
            raise SystemExit(f"Review report missing {field}.{name}")
        result = item.get("result")
        evidence = item.get("evidence")
        if result not in GATE_RESULTS:
            raise SystemExit(
                f"Invalid {field}.{name}.result {result!r}; choose from {', '.join(GATE_RESULTS)}"
            )
        if not isinstance(evidence, str) or not evidence.strip():
            raise SystemExit(f"Review report {field}.{name}.evidence must be non-empty")
        rating: dict[str, object] = {"result": result, "evidence": evidence.strip()}
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


def validate_blind_response(raw: object, iteration: dict) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise SystemExit("Blind response must be a JSON object")
    reviewer = nonempty_text(raw.get("reviewer"), "blind_response.reviewer")
    if raw.get("iteration") != iteration["number"]:
        raise SystemExit("Blind response iteration does not match the recorded iteration")
    if raw.get("artifact_sha256") != iteration["artifact"]["sha256"]:
        raise SystemExit("Blind response artifact_sha256 does not match the recorded iteration")
    return {
        "reviewer": reviewer,
        "expert": nonempty_text(raw.get("expert"), "blind_response.expert"),
        "audience": nonempty_text(raw.get("audience"), "blind_response.audience"),
    }


def validate_review_report(
    report: dict,
    iteration: dict,
    creator: str,
    review_token: str,
    blind_response: dict[str, str],
    blind_response_sha: str,
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
    gates = validate_ratings(report.get("gates"), GATE_NAMES, "gates", include_required=True)
    release_checks = validate_ratings(
        report.get("release_checks"), RELEASE_CHECK_NAMES, "release_checks"
    )

    raw_codes = report.get("codes", [])
    if not isinstance(raw_codes, list) or any(not isinstance(code, str) or not code.strip() for code in raw_codes):
        raise SystemExit("Review report codes must be a list of non-empty strings")
    codes = list(dict.fromkeys(code.strip() for code in raw_codes))
    raw_actions = report.get("required_actions", [])
    if not isinstance(raw_actions, list) or any(
        not isinstance(action, str) or not action.strip() for action in raw_actions
    ):
        raise SystemExit("Review report required_actions must be a list of non-empty strings")
    required_actions = [action.strip() for action in raw_actions]

    required_results = [item["result"] for item in gates.values() if item["required"]] + [
        item["result"] for item in release_checks.values()
    ]
    if verdict == "Send":
        if any(result != "Pass" for result in required_results):
            raise SystemExit("Send requires every required gate and release check to Pass")
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
        "scope": scope,
        "tested_size": tested_size,
        "blind_reads": {"expert": expert, "audience": audience},
        "gates": gates,
        "release_checks": release_checks,
        "verdict": verdict,
        "codes": codes,
        "required_actions": required_actions,
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
        "schema_version": 4,
        "case_id": case_id,
        "session_id": args.session,
        "creator": args.creator or os.getenv("HERMES_AGENT_ID") or f"session:{args.session}",
        "state": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "request": args.request or "",
        "audience": args.audience or "",
        "medium": args.medium or "",
        "original": original,
        "skill_snapshot": snapshot,
        "feedback": [],
        "iterations": [],
        "evaluations": [],
        "acceptance": None,
        "diagnosis": None,
    }
    write_json(case_dir / "case.json", data)
    pointer = active_pointer(args.session)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(case_dir) + "\n", encoding="utf-8")
    print(json.dumps({"case_id": case_id, "case_dir": str(case_dir), "original": original["path"]}))


def cmd_feedback(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = read_json(path)
    event = {"number": len(data["feedback"]) + 1, "at": now_iso(), "text": args.text}
    data["feedback"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "feedback": event["number"]}))


def cmd_iterate(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = read_json(path)
    if data["iterations"]:
        latest = data["iterations"][-1]["number"]
        evaluated = any(item["iteration"] == latest for item in data.get("evaluations", []))
        if not evaluated:
            raise SystemExit(f"Evaluate iteration {latest} before recording another iteration")
    number = len(data["iterations"]) + 1
    source = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Artifact not found: {source}")
    validate_deliverable(source)
    ext = source.suffix.lower() or ".bin"
    artifact = copy_artifact(source, case_dir / f"iteration-{number:02d}{ext}")
    event = {
        "number": number,
        "at": now_iso(),
        "summary": args.summary or "",
        "artifact": artifact,
        "feedback_count": len(data["feedback"]),
    }
    data["iterations"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "iteration": number, "path": artifact["path"]}))


def cmd_evaluate(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    path = case_dir / "case.json"
    data = read_json(path)
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
    report = validate_review_report(
        raw_report,
        iterations[iteration_number],
        creator,
        reveal["review_token"],
        blind_response,
        blind_response_sha,
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
        "codes": report["codes"],
        "required_actions": report["required_actions"],
        "report": {"path": str(stored_report), "sha256": sha256(stored_report)},
    }
    data["evaluations"].append(event)
    data["updated_at"] = now_iso()
    write_json(path, data)
    print(json.dumps({"case_id": data["case_id"], "evaluation": event["number"], "iteration": iteration_number, "verdict": report["verdict"]}))


def cmd_review_request(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    data = read_json(case_dir / "case.json")
    if not data["iterations"]:
        raise SystemExit("Cannot request a review with no recorded iteration")
    iteration = data["iterations"][-1]
    if any(item["iteration"] == iteration["number"] for item in data.get("evaluations", [])):
        raise SystemExit(f"Iteration {iteration['number']} already has an evaluation")

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
        "dataviz_eval_skill": str(skill_path),
        "blind_response_path": str(blind_response_path),
        "reveal_path": str(reveal_path),
        "blind_submit_command": (
            f'python3 "{Path(__file__).resolve()}" blind-submit --case "{data["case_id"]}"'
        ),
        "review_instructions": [
            "You are a fresh independent release reviewer, not the chart creator.",
            "Inspect the original and exact delivered artifact; the intent reveal does not exist yet.",
            "Write reviewer, iteration, artifact_sha256, expert, and audience to blind_response_path.",
            "After saving the blind response, run blind_submit_command to freeze it and create reveal_path.",
            "Then open reveal_path and finish the gate review in this same reviewer context.",
            "Do not inspect creator reasoning, claimed fixes, intended verdict, or rendering code.",
        ],
    }
    target = case_dir / f"review-blind-request-{iteration['number']:02d}.json"
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
    data = read_json(case_dir / "case.json")
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
    rating_template = {
        name: {
            "required": True if name in CORE_GATE_NAMES else "<true if scope requires this gate; otherwise false>",
            "result": "<Pass|Concern|Fail|Unknown>",
            "evidence": "<specific observed evidence>",
        }
        for name in GATE_NAMES
    }
    release_template = {
        name: {"result": "<Pass|Concern|Fail|Unknown>", "evidence": "<specific observed evidence>"}
        for name in RELEASE_CHECK_NAMES
    }
    reveal = {
        "case_id": data["case_id"],
        "iteration": iteration["number"],
        "review_token": review_token,
        "user_request": data["request"],
        "audience": data.get("audience", ""),
        "medium": data.get("medium", ""),
        "active_user_corrections": [item["text"] for item in data["feedback"]],
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
            "scope": "<evidence scope, audience, and medium>",
            "tested_size": "<actual or representative viewing condition>",
            "blind_reads": {
                "expert": blind_response["expert"],
                "audience": blind_response["audience"],
            },
            "gates": rating_template,
            "release_checks": release_template,
            "verdict": "<Send|Revise|Redesign|Not evaluable>",
            "codes": ["<failure code; empty list only for Send>"],
            "required_actions": ["<minimum concrete change; empty list only for Send>"],
        },
    }
    write_json(reveal_path, reveal)
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
    lines = [
        f"# Dataviz repair case {data['case_id']}",
        "",
        f"- State: {data['state']}",
        f"- Request: {data['request'] or '(none)'}",
        f"- Audience: {data.get('audience') or '(not recorded)'}",
        f"- Medium: {data.get('medium') or '(not recorded)'}",
        f"- Original: `{data['original']['path']}`",
        f"- Accepted iteration: {data['acceptance']['iteration']}",
        f"- Accepted artifact: `{data['acceptance']['path']}`",
        f"- Skill snapshot: `{data['skill_snapshot'] or '(not captured)'}`",
        "",
        "## User feedback",
        "",
    ]
    if data["feedback"]:
        for item in data["feedback"]:
            lines.append(f"{item['number']}. {item['text']}")
    else:
        lines.append("No correction was needed before acceptance.")
    lines.extend(["", "## Iterations", ""])
    for item in data["iterations"]:
        lines.append(f"{item['number']}. `{item['artifact']['path']}` - {item['summary'] or '(no summary)'}")
    lines.extend(["", "## Evaluations", ""])
    evaluations = data.get("evaluations", [])
    if evaluations:
        for item in evaluations:
            gates = ", ".join(
                f"{name}={result} ({'required' if item.get('gate_required', {}).get(name, True) else 'not required'})"
                for name, result in item["gates"].items()
            )
            codes = ", ".join(item["codes"]) or "none"
            lines.extend(
                [
                    f"{item['number']}. Iteration {item['iteration']}: **{item['verdict']}**",
                    f"   - Scope: {item['scope'] or '(not recorded)'}",
                    f"   - Gates: {gates}",
                    f"   - Codes: {codes}",
                    f"   - Reviewer: {item.get('reviewer', '(legacy self-review)')}",
                    f"   - Tested size: {item.get('tested_size', '(not recorded)')}",
                    f"   - Release checks: {', '.join(f'{name}={detail['result']}' for name, detail in item.get('release_checks', {}).items()) or '(not recorded)'}",
                    f"   - Required actions: {', '.join(item['required_actions']) if isinstance(item['required_actions'], list) else item['required_actions'] or 'none'}",
                ]
            )
    else:
        lines.append("No evaluation was recorded.")
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
    data = read_json(path)
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
    data["state"] = "accepted" if evaluation["verdict"] == "Send" else "accepted_with_override"
    data["acceptance"] = {
        "at": now_iso(),
        "iteration": accepted["number"],
        "path": accepted["artifact"]["path"],
        "evaluation": evaluation["number"],
        "evaluation_verdict": evaluation["verdict"],
        "override_reason": override_reason or None,
    }
    data["updated_at"] = now_iso()
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
    data = read_json(path)
    data["diagnosis"] = {
        "at": now_iso(),
        "classification": args.classification,
        "owner": args.owner,
        "lesson": args.lesson,
        "changed_files": [item.strip() for item in args.changed_files.split(",") if item.strip()],
    }
    data["updated_at"] = now_iso()
    write_json(path, data)
    packet = write_review_packet(case_dir, data)
    with packet.open("a", encoding="utf-8") as handle:
        diagnosis = data["diagnosis"]
        handle.write(f"- Classification: `{diagnosis['classification']}`\n")
        handle.write(f"- Owning skill: `{diagnosis['owner']}`\n")
        handle.write(f"- Lesson: {diagnosis['lesson']}\n")
        changed = ", ".join(f"`{item}`" for item in diagnosis["changed_files"]) or "none"
        handle.write(f"- Changed files: {changed}\n")
    print(json.dumps({"case_id": data["case_id"], "diagnosis": data["diagnosis"]}))


def cmd_status(args: argparse.Namespace) -> None:
    case_dir = resolve_case(args)
    data = read_json(case_dir / "case.json")
    print(json.dumps(data, indent=2, ensure_ascii=False))


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
    start.add_argument("--audience", default="")
    start.add_argument("--medium", default="")
    start.add_argument("--skills-root")
    start.add_argument("--creator", help="stable creator identity; defaults to the Hermes agent or session")
    start.set_defaults(func=cmd_start)

    feedback = sub.add_parser("feedback", help="record user feedback verbatim")
    add_case_args(feedback)
    feedback.add_argument("--text", required=True)
    feedback.set_defaults(func=cmd_feedback)

    iterate = sub.add_parser("iterate", help="copy and record a rendered revision")
    add_case_args(iterate)
    iterate.add_argument("--output", required=True)
    iterate.add_argument("--summary", default="")
    iterate.set_defaults(func=cmd_iterate)

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
    diagnose.set_defaults(func=cmd_diagnose)

    status = sub.add_parser("status", help="print the active case JSON")
    add_case_args(status)
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

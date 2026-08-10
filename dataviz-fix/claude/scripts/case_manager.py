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
        "schema_version": 1,
        "case_id": case_id,
        "session_id": args.session,
        "state": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "request": args.request or "",
        "original": original,
        "skill_snapshot": snapshot,
        "feedback": [],
        "iterations": [],
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
    number = len(data["iterations"]) + 1
    source = Path(args.output).expanduser().resolve()
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


def write_review_packet(case_dir: Path, data: dict) -> Path:
    lines = [
        f"# Dataviz repair case {data['case_id']}",
        "",
        f"- State: {data['state']}",
        f"- Request: {data['request'] or '(none)'}",
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
        lines.append(f"{item['number']}. `{item['artifact']['path']}` — {item['summary'] or '(no summary)'}")
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
    data["state"] = "accepted"
    data["acceptance"] = {
        "at": now_iso(),
        "iteration": accepted["number"],
        "path": accepted["artifact"]["path"],
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
    start.add_argument("--skills-root")
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

    accept = sub.add_parser("accept", help="accept the latest recorded revision")
    add_case_args(accept)
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

"""Fail-closed Hermes release guard for chart-repair turns.

The dataviz-fix case manager can validate a repair only after the agent uses
it.  This plugin closes the remaining bypass: a Hermes turn identified as a
chart repair may not return an image unless a new, turn-bound case reached
``user_review`` with an independent ``Send`` verdict and the returned image
hash matches that reviewed artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


_CHART_TERM = re.compile(
    r"\b(chart|graph|plot|figure|data[ -]?visuali[sz]ation|visuali[sz]ation|dashboard)\b",
    re.IGNORECASE,
)
_REPAIR_TERM = re.compile(
    r"\b(fix|repair|improve|redesign|revise|rework|redo|change|update|wrong|poor)\b"
    r"|\bclean\s+up\b|\bmake\b.{0,24}\bbetter\b|\bnot\s+happy\b|\bdid\s+nothing\b",
    re.IGNORECASE,
)
_CHART_ELEMENT = re.compile(
    r"\b(title|subtitle|axis|axes|label|legend|annotation|panel|bar|line|point|"
    r"colour|color|scale|unit|series|facet)\b",
    re.IGNORECASE,
)
_ACCEPTANCE_TERM = re.compile(
    r"^\s*(this\s+is\s+)?(right|good|fine|done|final|accepted?|looks\s+good)\b",
    re.IGNORECASE,
)
_MEDIA_PATH = re.compile(
    r"(?:MEDIA:\s*)?(/[^\s\"'<>|]+?\.(?:png|jpe?g|svg|pdf))(?=$|[\s\]),.;])",
    re.IGNORECASE,
)
_SKILL_INVOCATION = re.compile(
    r"\[IMPORTANT:\s*The user has invoked the [\"']([^\"']+)[\"'] skill",
    re.IGNORECASE,
)
_INSTRUCTION_MARKER = (
    "The user has provided the following instruction alongside the skill invocation:"
)
_ABSOLUTE_PATH = re.compile(r"(?<!\w)/(?:[^\s\"'<>|]+/)*[^\s\"'<>|]+")


@dataclass(frozen=True)
class GuardedTurn:
    case_session: str
    request: str
    started_at: float
    source_hashes: tuple[str, ...]


_turns: dict[str, GuardedTurn] = {}
_repair_sessions: set[str] = set()
_lock = threading.Lock()


def _intent_text(text: str) -> str:
    """Discard injected skill manuals and path tokens before intent matching."""

    if _INSTRUCTION_MARKER in text:
        text = text.rsplit(_INSTRUCTION_MARKER, 1)[1]
    else:
        invoked = {
            match.group(1).strip().lower() for match in _SKILL_INVOCATION.finditer(text)
        }
        if "dataviz-fix" in invoked or "data-science/dataviz-fix" in invoked:
            return "fix chart"

    # Internal reviewer prompts contain paths such as ``.../dataviz-fix/...``.
    # A path is evidence about an artifact, not a request to repair it.
    text = _ABSOLUTE_PATH.sub(" ", text)
    return text


def is_chart_repair_request(text: str, *, continuing: bool = False) -> bool:
    """Return whether *text* asks to change a chart rather than discuss one."""

    if not isinstance(text, str) or not text.strip():
        return False
    intent = _intent_text(text).strip()
    if not intent or _ACCEPTANCE_TERM.search(intent):
        return False
    if _CHART_TERM.search(intent) and _REPAIR_TERM.search(intent):
        return True
    return continuing and bool(_REPAIR_TERM.search(intent)) and bool(
        _CHART_ELEMENT.search(intent)
        or re.search(r"\b(still|again|same)\b", intent, re.I)
    )


def case_root() -> Path:
    override = os.getenv("DATAVIZ_FIX_ROOT")
    if override:
        return Path(override).expanduser().resolve() / "cases"
    hermes_home = Path(os.getenv("HERMES_HOME", "~/.hermes")).expanduser().resolve()
    return hermes_home / "dataviz-fix" / "cases"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _response_paths(response_text: str) -> list[Path]:
    paths: list[Path] = []
    for match in _MEDIA_PATH.finditer(response_text or ""):
        raw = match.group(1)
        if raw not in {str(path) for path in paths}:
            paths.append(Path(raw))
    return paths


def _source_hashes(user_message: str) -> tuple[str, ...]:
    hashes: list[str] = []
    for path in _response_paths(user_message):
        try:
            if path.is_file():
                digest = _sha256(path)
                if digest not in hashes:
                    hashes.append(digest)
        except OSError:
            continue
    return tuple(hashes)


def _created_at_timestamp(data: dict[str, Any]) -> float | None:
    raw = data.get("created_at")
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _has_independent_send(data: dict[str, Any], artifact_hash: str) -> bool:
    best = data.get("best_candidate") or {}
    if data.get("state") != "user_review" or best.get("verdict") != "Send":
        return False
    if (best.get("artifact") or {}).get("sha256") != artifact_hash:
        return False

    for evaluation in data.get("evaluations") or []:
        evaluated = evaluation.get("artifact") or best.get("artifact") or {}
        if (
            evaluation.get("verdict") == "Send"
            and evaluation.get("reviewer_role") == "independent"
            and evaluation.get("reviewer") != data.get("creator")
            and evaluated.get("sha256", artifact_hash) == artifact_hash
            and not evaluation.get("required_actions")
            and not evaluation.get("codes")
        ):
            return True
    return False


def find_released_artifact(
    expected_case_session: str,
    response_text: str,
    *,
    root: Path | None = None,
    not_before: float | None = None,
    source_hashes: tuple[str, ...] = (),
) -> Path | None:
    """Return the exact reviewed image referenced by the response, if any.

    The exact guard-generated case session is authoritative.  ``not_before``
    enables a narrow recovery for agents that created a fresh case under a
    different session id: the case must be new for this turn, owned by a main
    creator, independently approved, source-bound when a source was attached,
    and match the delivered artifact hash.  Ambiguous recovery fails closed.
    """

    delivered_paths = _response_paths(response_text)
    if not delivered_paths:
        return None

    delivered_hashes: dict[str, Path] = {}
    for path in delivered_paths:
        try:
            if path.is_file():
                delivered_hashes[_sha256(path)] = path
        except OSError:
            continue
    if not delivered_hashes:
        return None

    cases = root or case_root()
    try:
        case_files = list(cases.glob("*/case.json"))
    except OSError:
        return None

    loaded_cases: list[dict[str, Any]] = []
    for case_file in case_files:
        try:
            data = json.loads(case_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        loaded_cases.append(data)

    def released_path(data: dict[str, Any]) -> Path | None:
        artifact_hash = ((data.get("best_candidate") or {}).get("artifact") or {}).get(
            "sha256"
        )
        if (
            isinstance(artifact_hash, str)
            and artifact_hash in delivered_hashes
            and _has_independent_send(data, artifact_hash)
        ):
            return delivered_hashes[artifact_hash]
        return None

    for data in loaded_cases:
        if data.get("session_id") != expected_case_session:
            continue
        released = released_path(data)
        if released is not None:
            return released

    if not_before is None:
        return None

    recovery_matches: list[Path] = []
    expected_sources = set(source_hashes)
    for data in loaded_cases:
        if data.get("session_id") == expected_case_session:
            continue
        creator = data.get("creator")
        if not isinstance(creator, str) or not creator.startswith("main:"):
            continue
        created_at = _created_at_timestamp(data)
        if created_at is None or created_at < not_before - 1.0:
            continue
        if expected_sources:
            original_hash = (data.get("original") or {}).get("sha256")
            if original_hash not in expected_sources:
                continue
        released = released_path(data)
        if released is not None and released not in recovery_matches:
            recovery_matches.append(released)
    if len(recovery_matches) == 1:
        return recovery_matches[0]
    return None


def _case_session_id(session_id: str) -> str:
    seed = f"{session_id}:{secrets.token_hex(12)}".encode("utf-8")
    return "hermes-guard-" + hashlib.sha256(seed).hexdigest()[:20]


def on_pre_llm_call(**kwargs: Any) -> dict[str, str] | None:
    session_id = str(kwargs.get("session_id") or "")
    user_message = str(kwargs.get("user_message") or "")
    if not session_id:
        return None

    with _lock:
        continuing = session_id in _repair_sessions
    if not is_chart_repair_request(user_message, continuing=continuing):
        with _lock:
            _turns.pop(session_id, None)
        return None

    case_session = _case_session_id(session_id)
    started_at = time.time()
    source_hashes = _source_hashes(user_message)
    with _lock:
        _turns[session_id] = GuardedTurn(
            case_session, user_message, started_at, source_hashes
        )
        _repair_sessions.add(session_id)

    return {
        "context": (
            "Hermes dataviz release guard is active for this chart-repair turn. "
            "Run the installed dataviz-fix workflow and pass exactly "
            f"--session {case_session!r} to case_manager.py start. "
            "The final response must reference the exact reviewed image. "
            "Hermes will withhold it unless this turn-bound case reaches "
            "user_review with an independent Send verdict and the delivered "
            "file hash matches the reviewed artifact."
        )
    }


def on_transform_llm_output(**kwargs: Any) -> str | None:
    session_id = str(kwargs.get("session_id") or "")
    response_text = str(kwargs.get("response_text") or "")
    with _lock:
        turn = _turns.pop(session_id, None)
    if turn is None:
        return None

    try:
        released = find_released_artifact(
            turn.case_session,
            response_text,
            not_before=turn.started_at,
            source_hashes=turn.source_hashes,
        )
    except Exception:
        released = None
    if released is not None:
        return None

    return (
        "Chart withheld by the Hermes dataviz release guard: this repair turn "
        "did not produce a new turn-bound dataviz-fix case in user_review "
        "with an independent Send verdict and a matching delivered-artifact "
        "hash. No chart was released. Re-run the repair through dataviz-fix."
    )


def register(ctx: Any) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("transform_llm_output", on_transform_llm_output)

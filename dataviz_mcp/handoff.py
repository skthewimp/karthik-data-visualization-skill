"""Tolerant structured-text handoffs for the staged dataviz pipelines.

The pipelines pass a compact artifact from one model call to the next. Emitting that
artifact as strict, deeply-nested JSON breaks cheaper / open-weight models, which are
unreliable at valid JSON. Almost every field in a stage artifact is reasoning content whose
only consumer is the *next LLM stage* - which reads markdown perfectly well. The only thing
code must parse reliably is a handful of routing scalars (which builder to load, which
conditional skills to open).

So a stage emits free-form markdown sections (one per content field) followed by a small
``routing`` block of ``key: value`` lines for the code. This module parses that block
leniently and, for backward compatibility with strong models, also accepts a plain JSON
object. It has no third-party dependency: the JSON tolerance is hand-rolled.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path

__all__ = [
    "strip_code_fences",
    "loose_json",
    "coerce_bool",
    "parse_routing",
    "expected_sections",
    "render_handoff_spec",
]

_FENCE_RE = re.compile(r"^\s*```[^\n]*\n(.*?)\n```\s*$", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_ROUTING_FENCE_RE = re.compile(r"```routing\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_ROUTING_MARKER_RE = re.compile(
    r"^\s*-{0,3}\s*routing\s*-{0,3}\s*$", re.IGNORECASE | re.MULTILINE
)

_TRUE_TOKENS = {"true", "yes", "y", "1", "on"}
_FALSE_TOKENS = {"false", "no", "n", "0", "off", "none", ""}


def strip_code_fences(text: str) -> str:
    """Return the inside of a single fenced block, or the text unchanged."""
    match = _FENCE_RE.match(text.strip())
    return match.group(1) if match else text.strip()


def loose_json(text: str) -> dict | None:
    """Best-effort parse of a JSON object from possibly messy text. Never raises.

    Strips a surrounding code fence, tolerates trailing commas, and falls back to the
    outermost ``{ ... }`` span. Returns the parsed dict, or ``None`` when nothing parses.
    """
    candidates = []
    stripped = strip_code_fences(text)
    candidates.append(stripped)
    candidates.append(_TRAILING_COMMA_RE.sub(r"\1", stripped))
    first, last = stripped.find("{"), stripped.rfind("}")
    if first != -1 and last > first:
        span = stripped[first : last + 1]
        candidates.append(span)
        candidates.append(_TRAILING_COMMA_RE.sub(r"\1", span))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (ValueError, TypeError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def coerce_bool(value: object) -> bool | None:
    """Coerce a routing value to a bool. Returns ``None`` when it is not a clear flag."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _TRUE_TOKENS:
            return True
        if token in _FALSE_TOKENS:
            return False
    return None


def _default_for(key: str) -> object:
    """The soft default for a routing key when it is missing or unparseable."""
    if key == "builder":
        return "chart"
    return False  # every other routing key we use is a needs_* boolean flag


def _coerce_for(key: str, value: object) -> object:
    if key == "builder":
        token = str(value).strip().lower()
        return token if token in ("chart", "table") else _default_for(key)
    coerced = coerce_bool(value)
    return _default_for(key) if coerced is None else coerced


def _routing_lines(text: str) -> dict[str, str]:
    """Extract ``key: value`` pairs from a routing block, or ``{}`` when none is present."""
    block = None
    fence = _ROUTING_FENCE_RE.search(text)
    if fence:
        block = fence.group(1)
    else:
        marker = _ROUTING_MARKER_RE.search(text)
        if marker:
            block = text[marker.end() :]
    if block is None:
        return {}
    pairs: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip().lstrip("-* \t")
        if not line or ":" not in line:
            # A fenced routing block ends at the closing fence; a bare marker block runs to
            # the next markdown heading. Stop at a heading so we never swallow later prose.
            if fence is None and line.startswith("#"):
                break
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key:
            pairs[key] = value.strip()
    return pairs


def parse_routing(source: str | Path | Mapping, keys: Iterable[str]) -> dict:
    """Read the requested routing keys from a handoff artifact, tolerantly.

    ``source`` may be a :class:`~pathlib.Path` to the artifact, its text, or an already
    parsed mapping. Looks for a ``routing`` block first; if none is present, falls back to a
    lenient JSON parse of the whole payload (the strong-model path). Every requested key is
    returned, coerced, with a soft default for anything missing or unparseable - so a garbled
    artifact degrades to defaults instead of raising.
    """
    keys = list(keys)
    if isinstance(source, Mapping):
        raw = dict(source)
    else:
        text = ""
        if isinstance(source, Path):
            try:
                text = source.read_text(encoding="utf-8")
            except OSError:
                text = ""
        else:
            text = source or ""
        raw = _routing_lines(text)
        if not raw:
            raw = loose_json(text) or {}
    result: dict[str, object] = {}
    for key in keys:
        if key in raw:
            result[key] = _coerce_for(key, raw[key])
        else:
            result[key] = _default_for(key)
    return result


def expected_sections(schema: Mapping | None) -> tuple[str, ...]:
    """Top-level content-field names of a stage schema, in declaration order.

    The prompt's section list and the required-content checklist both derive from this, so
    the schema stays the single source of truth for what a stage artifact must carry.
    """
    if not isinstance(schema, Mapping):
        return ()
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return ()
    return tuple(properties.keys())


def _section_heading(field: str) -> str:
    return field.replace("_", " ").upper()


def render_handoff_spec(
    sections: Iterable[str], routing_keys: Iterable[str] = ()
) -> str:
    """The instruction snippet telling a stage which sections and routing keys to emit."""
    section_list = ", ".join(f"`## {_section_heading(name)}`" for name in sections)
    lines = [
        "Return the artifact as the structured-text handoff, not JSON. Write one markdown "
        f"section for each required field: {section_list}. Put the content directly under "
        "each heading as prose, bullets, or a small table - whatever is clearest. Recover "
        "every required field; if a value is unknown, say so under its heading rather than "
        "omitting the heading.",
    ]
    routing_keys = list(routing_keys)
    if routing_keys:
        key_lines = "\n".join(f"{key}: <value>" for key in routing_keys)
        lines.append(
            "Then, as the LAST thing in your reply, emit a fenced routing block the driver "
            "parses - exactly these keys, one per line, `builder` as `chart` or `table` and "
            "every `needs_*` as `yes` or `no`:\n"
            f"```routing\n{key_lines}\n```"
        )
    return "\n\n".join(lines)

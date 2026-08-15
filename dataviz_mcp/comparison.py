from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .artifacts import read_json, sha256_file, write_json


SCHEMA_VERSION = 1


def _signature(defect: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return defect["code"], tuple(sorted(str(item) for item in defect.get("element_ids", [])))


def _defect_map(report: dict[str, Any]) -> dict[tuple[str, tuple[str, ...]], dict[str, Any]]:
    return {_signature(item): item for item in report.get("defects", [])}


def _pixel_difference(before_path: Path, after_path: Path) -> dict[str, Any]:
    with Image.open(before_path) as before_image, Image.open(after_path) as after_image:
        before = np.asarray(before_image.convert("RGB"), dtype=np.int16)
        after = np.asarray(after_image.convert("RGB"), dtype=np.int16)
    if before.shape != after.shape:
        return {
            "comparable": False,
            "reason": "Artifact dimensions differ",
            "before_shape": list(before.shape),
            "after_shape": list(after.shape),
        }
    delta = np.abs(before - after)
    changed = np.any(delta > 0, axis=2)
    return {
        "comparable": True,
        "changed_pixel_ratio": round(float(changed.mean()), 6),
        "mean_absolute_channel_difference": round(float(delta.mean()), 6),
        "maximum_channel_difference": int(delta.max()),
    }


def compare_chart_artifacts(
    before_inspection_path: str,
    after_inspection_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Compare two exact, hashed inspection reports without making a taste verdict."""
    before_file = Path(before_inspection_path).expanduser().resolve()
    after_file = Path(after_inspection_path).expanduser().resolve()
    before = read_json(before_file)
    after = read_json(after_file)
    before_artifact = Path(before["artifact"]["path"]).expanduser().resolve()
    after_artifact = Path(after["artifact"]["path"]).expanduser().resolve()
    if sha256_file(before_artifact) != before["artifact"]["sha256"]:
        raise ValueError("Before artifact no longer matches its inspection hash")
    if sha256_file(after_artifact) != after["artifact"]["sha256"]:
        raise ValueError("After artifact no longer matches its inspection hash")

    before_defects = _defect_map(before)
    after_defects = _defect_map(after)
    resolved_keys = sorted(set(before_defects) - set(after_defects))
    introduced_keys = sorted(set(after_defects) - set(before_defects))
    persistent_keys = sorted(set(before_defects) & set(after_defects))
    before_blocking = sum(
        item.get("severity") in ("high", "medium") for item in before_defects.values()
    )
    after_blocking = sum(
        item.get("severity") in ("high", "medium") for item in after_defects.values()
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "before": {
            "inspection_path": str(before_file),
            "inspection_sha256": sha256_file(before_file),
            "artifact": before["artifact"],
        },
        "after": {
            "inspection_path": str(after_file),
            "inspection_sha256": sha256_file(after_file),
            "artifact": after["artifact"],
        },
        "resolved_defects": [before_defects[key] for key in resolved_keys],
        "introduced_defects": [after_defects[key] for key in introduced_keys],
        "persistent_defects": [after_defects[key] for key in persistent_keys],
        "blocking_defect_count": {"before": before_blocking, "after": after_blocking},
        "mechanically_improved": (
            after_blocking < before_blocking and not introduced_keys
        ),
        "passes_geometry_checks": {
            "before": before.get("passes_geometry_checks", False),
            "after": after.get("passes_geometry_checks", False),
        },
        "dimensions_changed": (
            before["artifact"]["width"], before["artifact"]["height"]
        )
        != (after["artifact"]["width"], after["artifact"]["height"]),
        "pixel_difference": _pixel_difference(before_artifact, after_artifact),
        "judgement_limit": (
            "This comparison reports mechanical changes only; skills/evaluators decide whether "
            "the revision is analytically or visually better."
        ),
    }
    destination = (
        Path(output_path).expanduser().resolve()
        if output_path
        else after_file.parent / "comparison.json"
    )
    write_json(destination, report)
    report["comparison_path"] = str(destination)
    report["comparison_sha256"] = sha256_file(destination)
    return report

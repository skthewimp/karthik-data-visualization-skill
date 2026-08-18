from __future__ import annotations

from pathlib import Path
import json

from PIL import Image


def build_review_views(
    artifact: Path,
    output_dir: Path,
    prefix: str,
    layout_metadata: Path | None = None,
) -> list[Path]:
    """Build artifact-bound full, delivery, panel, hierarchy, and dense-region views."""
    try:
        with Image.open(artifact) as opened:
            exact = opened.convert("RGB")

        full_path = output_dir / f"{prefix}-full.png"
        exact.save(full_path)

        preview = exact.copy()
        preview.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        preview_path = output_dir / f"{prefix}-delivery.png"
        preview.save(preview_path)

        width, height = exact.size
        crop_width = max(1, min(width, round(width * 0.6)))
        crop_height = max(1, min(height, round(height * 0.6)))
        starts = (
            (0, 0),
            (max(0, width - crop_width), 0),
            (0, max(0, height - crop_height)),
            (max(0, width - crop_width), max(0, height - crop_height)),
        )
        crops: list[Image.Image] = []
        for left, top in starts:
            crop = exact.crop((left, top, left + crop_width, top + crop_height))
            crop.thumbnail((900, 900), Image.Resampling.LANCZOS)
            crops.append(crop)
        gap = 12
        cell_width = max(crop.width for crop in crops)
        cell_height = max(crop.height for crop in crops)
        sheet = Image.new("RGB", (cell_width * 2 + gap, cell_height * 2 + gap), "white")
        for index, crop in enumerate(crops):
            x = (index % 2) * (cell_width + gap)
            y = (index // 2) * (cell_height + gap)
            sheet.paste(crop, (x, y))
        detail_path = output_dir / f"{prefix}-details.png"
        sheet.save(detail_path)
        views = [full_path, preview_path, detail_path]
        metadata = None
        if layout_metadata and layout_metadata.is_file():
            metadata = json.loads(layout_metadata.read_text(encoding="utf-8"))
        if metadata:
            width, height = exact.size

            def crop_bbox(name: str, bbox: dict, padding: int = 18) -> None:
                left = max(0, int(float(bbox["x"])) - padding)
                top = max(0, int(float(bbox["y"])) - padding)
                right = min(width, int(float(bbox["x"]) + float(bbox["width"])) + padding)
                bottom = min(height, int(float(bbox["y"]) + float(bbox["height"])) + padding)
                if right <= left or bottom <= top:
                    return
                target = output_dir / f"{prefix}-{name}.png"
                exact.crop((left, top, right, bottom)).save(target)
                views.append(target)

            for index, panel in enumerate(metadata.get("plot_areas", []), start=1):
                crop_bbox(f"panel-{index:02d}", panel["bbox"])

            hierarchy_roles = ("title", "subtitle", "panel_heading", "legend", "footer")
            hierarchy_items = [
                item
                for item in metadata.get("elements", [])
                if item.get("role") in hierarchy_roles
            ] + metadata.get("legends", [])
            for role in hierarchy_roles:
                role_items = [
                    item for item in hierarchy_items if item.get("role") == role
                ]
                if role == "legend":
                    role_items = metadata.get("legends", [])
                if not role_items:
                    continue
                left = min(float(item["bbox"]["x"]) for item in role_items)
                top = min(float(item["bbox"]["y"]) for item in role_items)
                right = max(
                    float(item["bbox"]["x"]) + float(item["bbox"]["width"])
                    for item in role_items
                )
                bottom = max(
                    float(item["bbox"]["y"]) + float(item["bbox"]["height"])
                    for item in role_items
                )
                crop_bbox(
                    f"hierarchy-{role.replace('_', '-')}",
                    {"x": left, "y": top, "width": right - left, "height": bottom - top},
                )

            repeated = [
                item
                for item in metadata.get("elements", [])
                if item.get("role") in ("annotation", "label", "legend_text", "tick_label")
            ]
            if repeated:
                densest = sorted(
                    repeated,
                    key=lambda item: sum(
                        1
                        for other in repeated
                        if abs(float(item["bbox"]["x"]) - float(other["bbox"]["x"])) < width * 0.2
                        and abs(float(item["bbox"]["y"]) - float(other["bbox"]["y"])) < height * 0.2
                    ),
                    reverse=True,
                )[: min(4, len(repeated))]
                for index, item in enumerate(densest, start=1):
                    bbox = item["bbox"]
                    crop_bbox(
                        f"dense-{index:02d}",
                        {
                            "x": max(0, float(bbox["x"]) - width * 0.12),
                            "y": max(0, float(bbox["y"]) - height * 0.12),
                            "width": min(width, float(bbox["width"]) + width * 0.24),
                            "height": min(height, float(bbox["height"]) + height * 0.24),
                        },
                        padding=0,
                    )
        return views
    except (OSError, ValueError):
        return []

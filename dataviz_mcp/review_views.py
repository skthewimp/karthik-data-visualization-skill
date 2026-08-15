from __future__ import annotations

from pathlib import Path

from PIL import Image


def build_review_views(
    artifact: Path,
    output_dir: Path,
    prefix: str,
) -> list[Path]:
    """Build delivery-size and overlapping detail views from one exact raster."""
    try:
        with Image.open(artifact) as opened:
            exact = opened.convert("RGB")

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
        return [preview_path, detail_path]
    except (OSError, ValueError):
        return []

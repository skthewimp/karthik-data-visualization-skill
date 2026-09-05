"""Content-sized table plans. Semantic treatment remains the table skill's decision."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from .layout import PROFILES, line_px


def _metrics(texts, family, size, dpi, bold=False):
    """Batch grid/ragg metrics; report a portable fallback rather than claiming parity."""
    candidates = {""}
    for text in texts:
        for line in text.split("\n"):
            candidates.add(line)
            words = line.split()
            candidates.update(" ".join(words[i:j]) for i in range(len(words))
                              for j in range(i + 1, len(words) + 1))
    strings = sorted(candidates)
    if shutil.which("Rscript"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "input.csv").open("w") as f:
                writer = csv.writer(f)
                writer.writerow(["text"])
                writer.writerows([s] for s in strings)
            script = '''args <- commandArgs(TRUE)
library(grid)
ragg::agg_png(args[3], width=100, height=100, res=as.numeric(args[6]))
pushViewport(viewport(gp=gpar(fontfamily=args[4], fontsize=as.numeric(args[5]), fontface=args[7])))
x <- read.csv(args[1], stringsAsFactors=FALSE, na.strings=NULL, blank.lines.skip=FALSE, colClasses="character")$text
w <- convertWidth(stringWidth(x), "in", valueOnly=TRUE)*as.numeric(args[6])
write.table(w, args[2], row.names=FALSE, col.names=FALSE)
dev.off()
'''
            (root / "metrics.R").write_text(script)
            result = subprocess.run(["Rscript", "--vanilla", str(root / "metrics.R"),
                str(root / "input.csv"), str(root / "widths"), str(root / "probe.png"),
                family, str(size), str(dpi), "bold" if bold else "plain"],
                capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                widths = [float(s) for s in (root / "widths").read_text().split()]
                if len(widths) == len(strings):
                    return dict(zip(strings, widths)), "grid/ragg"
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    renderer = RendererAgg(100, 100, dpi)
    font = FontProperties(family=family, size=size, weight="bold" if bold else "normal")
    return {s: renderer.get_text_width_height_descent(s, font, False)[0] for s in strings}, "matplotlib/Agg (verify in target renderer)"


def _wrap(text, width, metrics):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if current and metrics[candidate] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return "\n".join(lines)


def recommend_table_layout(
    columns: list[dict[str, Any]] | None = None,
    content_path: str | None = None,
    delivery_profile: str = "chat",
    typography: dict[str, Any] | None = None,
    delivery: dict[str, Any] | None = None,
    treatment: dict[str, Any] | None = None,
    title: str = "",
    subtitle: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Plan from columns {header, cells, identifier?, max_width_px?, max_header_lines?, visual_width_px?}.

    Pass the complete header (label, units and any description), using explicit
    newlines for semantic breaks. Optional max_header_lines constrains wrapping;
    exceeding it or max_width_px produces cannot_fit rather than a clipped header.

    Cells are final display strings; columns may additionally carry semantic metadata.
    content_path accepts a local JSON object with columns, title, subtitle, notes.
    typography: family, body_pt, header_pt, minimum_body_pt, minimum_header_pt,
    padding_x_px, padding_y_px. delivery: max_width_px, max_height_px, dpi,
    display_width_px, minimum_text_px, allow_split. Pixel sizes refer to export pixels
    except display_width_px and minimum_text_px, which refer to the displayed artifact.
    treatment is a skill-selected plan with kind (text/emphasis/bar/dot/shading/sparkline),
    scope (column/row/table), commensurable, and any renderer-specific scale/focal details.
    Width selection balances measured wrapping and shared row heights at fixed type
    and padding, preferring feasible delivery, fewer pages and a smaller footprint.
    Returned pages use zero-based column indices and half-open row ranges.
    """
    if content_path:
        if columns is not None:
            raise ValueError("Supply columns or content_path, not both")
        content = json.loads(Path(content_path).read_text())
        columns = content["columns"]
        title, subtitle, notes = (content.get(k, v) for k, v in
                                  [("title", title), ("subtitle", subtitle), ("notes", notes)])
    cols = columns or []
    if not cols:
        raise ValueError("At least one column is required")
    for i, c in enumerate(cols):
        if not isinstance(c, dict) or not isinstance(c.get("header"), str) or not isinstance(c.get("cells"), list):
            raise ValueError(
                f"Column {i} requires full header text and a cells list; character counts "
                "cannot establish fit. Use header='' only for an intentionally blank header."
            )
        budget = c.get("max_header_lines")
        if budget is not None and (isinstance(budget, bool) or not isinstance(budget, int) or budget < 1):
            raise ValueError("max_header_lines must be a positive integer")
    cells = [[str(v) if v is not None else "" for v in c["cells"]] for c in cols]
    n = len(cells[0])
    if any(len(c) != n for c in cells):
        raise ValueError("Columns must contain the same number of cells")
    profile = dict(PROFILES[delivery_profile])
    profile.update(delivery or {})
    typo = {"family": "sans", "body_pt": 11, "header_pt": 12,
            "minimum_body_pt": 11, "minimum_header_pt": 11}
    typo.update(typography or {})
    dpi, max_w, max_h = (float(profile[k]) for k in ("dpi", "max_width_px", "max_height_px"))
    if min(dpi, max_w, max_h, *(float(typo[k]) for k in
           ("body_pt", "header_pt", "minimum_body_pt", "minimum_header_pt"))) <= 0:
        raise ValueError("Dimensions and type sizes must be positive")
    display_w = float(profile.get("display_width_px", max_w))
    minimum_px = float(profile.get("minimum_text_px", 0))
    if display_w <= 0 or minimum_px < 0:
        raise ValueError("Display width must be positive and minimum_text_px nonnegative")
    # Cap the export at the width that preserves the requested display font floor.
    body = max(float(typo["body_pt"]), float(typo["minimum_body_pt"]), minimum_px * 72 / dpi)
    header = max(float(typo["header_pt"]), float(typo["minimum_header_pt"]), minimum_px * 72 / dpi)
    if minimum_px:
        max_w = min(max_w, display_w * min(body, header) * dpi / 72 / minimum_px)
    # Compact spacing scales with type; explicit delivery-specific padding wins.
    em_px = body * dpi / 72
    px = float(typo.get("padding_x_px", 0.35 * em_px))
    py = float(typo.get("padding_y_px", 0.15 * em_px))
    if min(px, py) < 0:
        raise ValueError("Padding must be nonnegative")
    plan = dict(treatment or {"kind": "text"})
    kind, scope = plan.get("kind", "text"), plan.get("scope", "column")
    if kind not in {"text", "emphasis", "bar", "dot", "shading", "sparkline"}:
        raise ValueError("Unknown treatment kind")
    if scope not in {"column", "row", "table"}:
        raise ValueError("Unknown comparison scope")
    if kind in {"bar", "dot", "shading", "sparkline"} and scope in {"row", "table"} and not plan.get("commensurable"):
        raise ValueError("A shared scale requires explicit commensurability")
    headers = [c["header"] for c in cols]
    bm, backend = _metrics([v for c in cells for v in c], typo["family"], body, dpi)
    if kind == "emphasis":
        bold_metrics, bold_backend = _metrics([v for c in cells for v in c], typo["family"], body, dpi, True)
        bm = {text: max(width, bold_metrics[text]) for text, width in bm.items()}
        if bold_backend != backend:
            backend = bold_backend
    hm, header_backend = _metrics(headers + [title, subtitle, notes], typo["family"], header, dpi, True)
    warnings = []
    blocks = {k: _wrap(v, max(1, max_w - 2 * px), hm) for k, v in
              [("title", title), ("subtitle", subtitle), ("notes", notes)] if v}
    bands = sum((v.count("\n") + 1) * line_px(header, dpi) + 2 * py for v in blocks.values())
    block_width = max([max(hm[line] for line in b.split("\n")) + 2 * px
                       for b in blocks.values()] + [0])
    options = []
    for c, values, label in zip(cols, cells, headers):
        visual = float(c.get("visual_width_px", 0))
        if visual < 0:
            raise ValueError("visual_width_px must be nonnegative")
        natural = max([bm[line] + visual for v in values for line in v.split("\n")] +
                      [hm[line] for line in label.split("\n")])
        limit = float(c.get("max_width_px", max_w)) - 2 * px
        if limit <= visual:
            raise ValueError("Column width must leave room for text after padding and visuals")
        # Every change in word wrapping occurs at a measured phrase width. Search
        # those breakpoints, not character-count caps or a fixed fill percentage.
        token = max([bm[w] + visual for v in values for w in v.split()] +
                    [hm[w] for w in label.split()] + [visual])
        upper = max(token, min(natural, limit))
        candidates = {token, upper}
        for text, metrics, extra in [(label, hm, 0)] + [(v, bm, visual) for v in values]:
            for paragraph in text.split("\n"):
                words = paragraph.split()
                candidates.update(metrics[" ".join(words[i:j])] + extra
                    for i in range(len(words)) for j in range(i + 1, len(words) + 1)
                    if token <= metrics[" ".join(words[i:j])] + extra <= upper)
        variants, seen = [], set()
        for available in sorted(candidates):
            wh = _wrap(label, available, hm)
            wc = [_wrap(v, available - visual, bm) for v in values]
            signature = (wh, tuple(wc))
            if signature in seen:
                continue
            seen.add(signature)
            variants.append({"width": math.ceil(available + 2 * px),
                "header": wh, "cells": wc,
                "header_over_budget": (c.get("max_header_lines") is not None and
                                       wh.count("\n") + 1 > c["max_header_lines"]),
                "header_height": (wh.count("\n") + 1) * line_px(header, dpi) + 2 * py,
                "heights": [(v.count("\n") + 1) * line_px(body, dpi) + 2 * py for v in wc]})
        feasible = [v for v in variants if not v["header_over_budget"]
                    and v["width"] <= c.get("max_width_px", math.inf)]
        # Enforce each column's constraints before comparing table footprints.
        # Keep impossible variants only to return intact content with cannot_fit.
        options.append(feasible or variants)

    ids = [i for i, c in enumerate(cols) if c.get("identifier")]
    remaining = [i for i in range(len(cols)) if i not in ids]

    def arrange(chosen):
        widths = [v["width"] for v in chosen]
        hh = max(v["header_height"] for v in chosen)
        heights = [max(v["heights"][r] for v in chosen) for r in range(n)]
        groups, group = [], list(ids)
        for i in remaining:
            if sum(widths[j] for j in group + [i]) > max_w and len(group) > len(ids):
                groups.append(group)
                group = list(ids)
            group.append(i)
        groups.append(group)
        ranges, start, used = [], 0, hh + bands
        for r, height in enumerate(heights):
            if used + height > max_h and r > start:
                ranges.append([start, r])
                start, used = r, hh + bands
            used += height
        ranges.append([start, n])
        pages = [{"columns": g, "rows": rr,
                  "width_px": math.ceil(max(sum(widths[j] for j in g), block_width)),
                  "height_px": math.ceil(hh + bands + sum(heights[rr[0]:rr[1]]))}
                 for g in groups for rr in ranges]
        return widths, hh, heights, pages

    def score(chosen):
        _, hh, heights, pages = arrange(chosen)
        overflow = (any(p["width_px"] > max_w or p["height_px"] > max_h for p in pages)
                    or any(v["header_over_budget"] or v["width"] > c.get("max_width_px", math.inf)
                           for c, v in zip(cols, chosen)))
        # Prefer feasible delivery, then fewer continuations, then less allocated
        # space at unchanged type/padding. Shared row/header heights make excess
        # wrapping expensive across the whole table, not just the changed column.
        return (overflow, len(pages), sum(p["width_px"] * p["height_px"] for p in pages),
                hh + sum(heights))

    def tighten(chosen):
        current = score(chosen)
        while True:
            improved = False
            for i, variants in enumerate(options):
                best, best_score = chosen[i], current
                for variant in variants:
                    trial = chosen[:i] + [variant] + chosen[i + 1:]
                    trial_score = score(trial)
                    if trial_score < best_score:
                        best, best_score = variant, trial_score
                if best_score < current:
                    chosen[i], current, improved = best, best_score, True
            if not improved:
                return chosen

    # Start from both ends: shared heights can make several columns need to wrap
    # together, so a widest-only greedy pass misses useful compact arrangements.
    alternatives = [tighten([v[0] for v in options]), tighten([v[-1] for v in options])]
    chosen = min(alternatives, key=score)
    widths, hh, heights, pages = arrange(chosen)
    wrapped_headers = [v["header"] for v in chosen]
    wrapped_cells = [v["cells"] for v in chosen]
    impossible = any(p["width_px"] > max_w or p["height_px"] > max_h for p in pages)
    for i, (c, v) in enumerate(zip(cols, chosen)):
        if v["header_over_budget"] or v["width"] > c.get("max_width_px", math.inf):
            impossible = True
            warnings.append(
                f"Column {i}: complete header/content exceeds a supplied column width "
                "or header-line limit. Widen or revise the wording/continuation plan; "
                "do not clip, truncate or shrink the header."
            )
    split = len(pages) > 1
    if split and not profile.get("allow_split", True):
        impossible = True
    status = "cannot_fit" if impossible else "split" if split else "fits"
    if status != "fits":
        warnings.append("Split/continuation required; retain all content and repeat headers and identifiers." if not impossible else
                        "Content cannot fit these constraints. Change delivery, supported wording, or form; do not shrink type.")
    if backend != "grid/ragg" or header_backend != backend:
        warnings.append("Metrics are not from the target R renderer; render and inspect before accepting fit.")
    return {"status": status, "measurement_backend": backend, "dpi": dpi,
            "body_pt": body, "header_pt": header, "font_family": typo["family"],
            "padding_x_px": px, "padding_y_px": py,
            "col_widths_px": widths, "row_heights_px": heights, "header_height_px": hh,
            "headers": wrapped_headers, "cells": wrapped_cells, "blocks": blocks,
            "block_font_pt": header, "reserved_band_px": bands,
            "pages": pages, "treatment": plan, "warnings": warnings,
            "delivery": profile}

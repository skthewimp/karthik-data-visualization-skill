# Mechanical rendering and inspection through MCP

The motivating failure was not analytical. An agent produced a reasonable account of ten years of global coffee prices, but the delivered chart still had labels crossing the series, poor wrapping, and overlapping annotations. The skills already described what good annotation and evaluation looked like. What they lacked was a reliable way to test the file that had actually been rendered.

This MCP layer addresses that narrow problem. The skills still contain the judgement; the server supplies mechanical capabilities beneath them.

## Architectural boundary

| Layer | Owns |
|---|---|
| Skills and agent | Question, definitions, denominators, evidence, claim, chart choice, annotation significance and wording, critique, release verdict |
| MCP capabilities | Matplotlib execution, export bundles, geometry metadata, exact-file hashing, clipping and collision checks, revision comparison |

The MVP deliberately does not include `profile_dataset` or `run_analysis`. There is no reusable profiler or query engine in this repo yet. Adding generic versions would create a second analytical stack instead of exposing existing reliable machinery.

It also does not make a `Send`, `Revise`, or `Redesign` decision. A collision detector cannot decide whether the title states the right claim, whether the comparison set is honest, or whether an event annotation implies causality without evidence.

## Why render metadata is primary

The renderer already knows where it placed axes, text, annotations, and paths. Recovering all of that from pixels would be less accurate and harder to test.

`render_chart` therefore produces one bundle:

```text
chart.png
chart-spec.json
layout-metadata.json
manifest.json
```

The PNG remains the deliverable and the source of truth for its dimensions and SHA-256 hash. `layout-metadata.json` records the geometry used to inspect it: canvas and plot bounds, text and annotation boxes, line paths, legend bounds, and data-to-pixel transforms. `manifest.json` binds the artifact, spec, and metadata hashes together.

`inspect_rendered_chart` rejects metadata whose artifact hash or dimensions do not match the PNG. If no metadata is available, it records the raster hash and dimensions but marks geometry checks incomplete. It does not convert an unknown result into a pass.

## Generation sequence

The intellectual stages remain unchanged:

```text
intake
→ analysis contract
→ data preparation
→ facts table
→ chart selection
→ chart spec
→ render bundle
→ deterministic inspection of the exact PNG
→ independent evaluation
→ narrow repair when required
→ delivery
```

The orchestrator now requires exact-artifact inspection after rendering when the capability is available. The evaluator uses a matching inspection report as mechanical evidence. It still performs the independent visual and analytical read.

## Repair sequence and version binding

```text
render candidate
→ inspect exact artifact and matching metadata
→ attach the artifact and inspection hashes to the case iteration
→ issue the blind review request
→ run dataviz-eval against that exact version
→ reveal context only after the blind read
→ apply the minimum pass set
→ render and inspect again
→ stop when the release line passes
```

The existing `dataviz-fix` state machine remains the owner of original, current, best, and historical artifacts. Case schema 10 adds the render manifest, chart spec, layout metadata, and inspection report to each iteration. It rejects:

- a bundle whose artifact, spec, or metadata hash no longer matches;
- an inspection report for a different artifact;
- an evaluation that cites the wrong deterministic inspection hash.

The repairer receives named defects and element IDs rather than an invitation to redesign the chart. Mechanical failures are fixed first. Elements that already pass remain preservation constraints, and the loop stops when the pass line is met.

## Mechanical checks

The first version reports five defect codes:

| Code | Meaning | Severity |
|---|---|---|
| `OUT_OF_BOUNDS` | A rendered text element extends outside the canvas | High |
| `TEXT_CLIPPED` | An annotation or label crosses an active plot clipping boundary | High |
| `LABEL_LABEL_COLLISION` | Two annotation boxes intersect | High |
| `ANNOTATION_SERIES_COLLISION` | An annotation box intersects a recorded line path | High |
| `LONG_UNWRAPPED_ANNOTATION` | Annotation text exceeds the configured character limit without a line break | Medium |

`passes_geometry_checks` is true only when metadata is present, supported checks are complete, and no high- or medium-severity defect remains.

Current collision coverage is deliberately honest:

- text geometry and Matplotlib line paths are supported;
- scatter collections, bars and other patches, images, and non-Matplotlib renderers are not yet represented as collision paths;
- the report sets `checks_complete` to false when unsupported non-line marks are present;
- raster-only inspection does not attempt OCR or infer hidden geometry from pixels.

## Revision comparison

`compare_chart_artifacts` validates both artifact hashes before comparing them. It reports:

- resolved, introduced, and persistent defects;
- before-and-after blocking defect counts;
- dimensions and pixel-change measurements;
- `mechanically_improved`, which is true only when blocking defects fall and no new defect is introduced.

This is a mechanical result, not a taste score. A substantively worse chart can still have fewer collisions, so the skills and independent evaluator retain the final decision.

## Tested failure cases

The core suite creates deterministic fixtures for:

- an annotation crossing a line;
- two annotation boxes overlapping;
- an annotation outside the canvas;
- clipped text;
- long unwrapped annotation text;
- a clean chart;
- missing-data line segments, to prevent false bridges across `NaN` gaps;
- unsupported non-line marks, to verify that incomplete coverage stays explicit.

The end-to-end coffee fixture renders a deliberately bad multi-annotation time series, detects four geometry defects, changes annotation placement only, renders again, and reaches zero defects. The comparison report confirms that the second artifact resolves the failures without introducing a new one.

## Implementation map

| Path | Responsibility |
|---|---|
| `dataviz_mcp/rendering.py` | Trusted builder execution and metadata-first render bundle |
| `dataviz_mcp/inspection.py` | Exact-artifact geometry checks and defect report |
| `dataviz_mcp/comparison.py` | Hash-validated revision comparison |
| `dataviz_mcp/server.py` | Three-tool stdio MCP surface |
| `dataviz_mcp/review_views.py` | Shared deterministic delivery/detail views used by the local runner |
| `dataviz-fix/*/scripts/case_manager.py` | Versioned case state and inspection/evaluation binding |
| `tester/local_runner.py` | One bounded creator, inspection, and blind-review cycle |
| `dataviz_mcp/tests/` | Capability, protocol, geometry, and coffee repair tests |

Installation, client registration, tool parameters, and the chart-builder contract are in [`dataviz_mcp/README.md`](../dataviz_mcp/README.md).

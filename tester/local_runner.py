from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any
from uuid import uuid4

from dataviz_mcp import stage_contracts as sc
from dataviz_mcp.artifacts import read_json, sha256_file, write_json
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.review_views import build_review_views


RUNNABLE_STATES = ("critique", "design", "build", "revise", "redesign")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_environment(extra: dict[str, str]) -> dict[str, str]:
    """Keep the local CLI usable without passing provider secrets to chart code."""
    allowed = {
        "CODEX_HOME",
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "SHELL",
        "SSL_CERT_FILE",
        "TMPDIR",
        "USER",
    }
    env = {name: value for name, value in os.environ.items() if name in allowed}
    env.update(extra)
    return env


class LocalCodexRunner:
    """Run one creator pass and one independent reviewer pass in the background."""

    def __init__(self, client: Any, repo_root: Path, enabled: bool | None = None):
        self.client = client
        self.repo_root = repo_root.resolve()
        self.executable = shutil.which("codex")
        self.enabled = (
            os.getenv("DATAVIZ_ENABLE_LOCAL_RUNNER") == "1" if enabled is None else enabled
        )
        self.model = os.getenv("DATAVIZ_CODEX_MODEL", "").strip()
        self.reasoning_effort = os.getenv("DATAVIZ_CODEX_REASONING_EFFORT", "").strip()
        self.timeout_seconds = int(os.getenv("DATAVIZ_RUN_TIMEOUT_SECONDS", "900"))
        self.jobs: dict[str, dict[str, Any]] = {}
        self.active_cases: set[str] = set()
        self.lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self.enabled and self.executable is not None

    def public_config(self) -> dict[str, object]:
        estimate = self.estimated_cycle_tokens()
        return {
            "provider_runner": self.available,
            "runner": "local-codex" if self.available else None,
            "model": self.model or "Codex default",
            "reasoning_effort": self.reasoning_effort or "Codex default",
            "run_scope": "one creator pass plus one fresh reviewer pass",
            "estimated_cycle_tokens": estimate,
        }

    def estimated_cycle_tokens(self) -> int | None:
        completed: list[int] = []
        cases_root = self.client.root / "cases"
        if not cases_root.is_dir():
            return None
        for path in cases_root.glob("*/case.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            by_iteration: dict[int, dict[str, int]] = {}
            for event in data.get("telemetry", {}).get("events", []):
                iteration = event.get("iteration")
                stage = event.get("stage")
                if not isinstance(iteration, int) or stage not in ("creator", "reviewer"):
                    continue
                by_iteration.setdefault(iteration, {})[stage] = int(event.get("total_tokens", 0))
            for stages in by_iteration.values():
                if "creator" in stages and "reviewer" in stages:
                    completed.append(stages["creator"] + stages["reviewer"])
        return int(median(completed)) if completed else None

    def _skill_path(self, name: str) -> Path:
        """Resolve a required skill from the checkout or installed runtime."""
        candidates = [self.repo_root / name / "codex" / "SKILL.md"]
        codex_home = os.getenv("CODEX_HOME")
        if codex_home:
            candidates.append(Path(codex_home).expanduser() / "skills" / name / "SKILL.md")
        candidates.extend(
            (
                Path.home() / ".codex" / "skills" / name / "SKILL.md",
                Path.home() / ".claude" / "skills" / name / "SKILL.md",
            )
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise RuntimeError(f"Required installed skill not found: {name}")

    def start(self, case_id: str) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError(
                "Local runner is disabled. Set DATAVIZ_ENABLE_LOCAL_RUNNER=1 and restart the app."
            )
        case = self.client.status(case_id)
        if case["state"] not in RUNNABLE_STATES:
            raise ValueError(
                f"Case is {case['state']}; local run requires {', '.join(RUNNABLE_STATES)}"
            )
        exhausted = case["budget_status"]["exhausted"]
        if exhausted:
            raise ValueError(
                f"Cannot start while {', '.join(item.replace('_', ' ') for item in exhausted)} is exhausted"
            )
        token_limit = case["limits"].get("max_tokens")
        estimate = self.estimated_cycle_tokens()
        if token_limit is not None and estimate is not None:
            remaining = token_limit - case["telemetry"]["total_tokens"]
            if remaining < estimate:
                raise ValueError(
                    f"Measured cycle estimate is {estimate:,} tokens but only {remaining:,} remain; increase the token limit before running"
                )
        with self.lock:
            if case_id in self.active_cases:
                raise ValueError("A local run is already active for this case")
            job_id = uuid4().hex
            job = {
                "job_id": job_id,
                "case_id": case_id,
                "status": "queued",
                "stage": "creator",
                "started_at": now_iso(),
                "updated_at": now_iso(),
                "finished_at": None,
                "error": None,
                "events": [],
            }
            self.jobs[job_id] = job
            self.active_cases.add(case_id)
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return self.get(job_id)

    def get(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            if job_id not in self.jobs:
                raise KeyError(job_id)
            return json.loads(json.dumps(self.jobs[job_id]))

    def _event(self, job_id: str, stage: str, message: str) -> None:
        with self.lock:
            job = self.jobs[job_id]
            job["stage"] = stage
            job["updated_at"] = now_iso()
            job["events"].append({"at": now_iso(), "stage": stage, "message": message})

    def _finish(self, job_id: str, status: str, error: str | None = None) -> None:
        with self.lock:
            job = self.jobs[job_id]
            job["status"] = status
            job["error"] = error
            job["updated_at"] = now_iso()
            job["finished_at"] = now_iso()
            self.active_cases.discard(job["case_id"])

    def _run_job(self, job_id: str) -> None:
        with self.lock:
            job = self.jobs[job_id]
            job["status"] = "running"
            case_id = job["case_id"]
        try:
            case = self.client.status(case_id)
            case_dir = self.client.root / "cases" / case_id
            iteration_number = len(case["iterations"]) + 1
            candidate_path = case_dir / f"runner-{job_id}-candidate-{iteration_number:02d}.png"
            self._run_creator_stages(
                job_id,
                case,
                case_id,
                case_dir,
                candidate_path,
                iteration_number,
                case["context_version"],
            )
            if not candidate_path.is_file():
                raise RuntimeError(f"Creator did not write the required artifact: {candidate_path}")
            case = self.client.status(case_id)
            if not any(
                item.get("context_version") == case["context_version"]
                for item in case.get("semantic_preflights", [])
            ):
                raise RuntimeError(
                    "Creator finished without recording the required semantic preflight"
                )
            self.client.run("build-check", "--case", case_id)
            iterate_args: list[object] = [
                "iterate",
                "--case",
                case_id,
                "--output",
                candidate_path,
                "--summary",
                "Local runner candidate",
            ]
            manifest_path = case_dir / "manifest.json"
            layout_path: Path | None = None
            if manifest_path.is_file():
                try:
                    manifest = read_json(manifest_path)
                    if manifest.get("artifact", {}).get("sha256") == sha256_file(candidate_path):
                        iterate_args.extend(("--bundle-manifest", manifest_path))
                        layout_path = Path(manifest["layout_metadata"]["path"])
                except (KeyError, TypeError, ValueError):
                    layout_path = None
            self.client.run(*iterate_args)
            case = self.client.status(case_id)
            if case["state"] != "blind_review" or len(case["iterations"]) < iteration_number:
                raise RuntimeError(
                    "Creator finished without recording exactly one candidate through case_manager.py"
                )
            recorded_artifact = Path(case["iterations"][-1]["artifact"]["path"])
            inspection_path = case_dir / f"runner-{job_id}-inspection-{iteration_number:02d}.json"
            inspection = inspect_rendered_chart(
                str(recorded_artifact),
                str(layout_path) if layout_path else None,
                str(inspection_path),
            )
            review_views = build_review_views(
                recorded_artifact,
                case_dir,
                f"inspection-{iteration_number:02d}",
                layout_path,
            )
            inspection.pop("inspection_sha256", None)
            inspection["review_views"] = [
                {"path": str(view), "sha256": sha256_file(view)}
                for view in review_views
            ]
            write_json(inspection_path, inspection)
            self.client.run(
                "inspect",
                "--case",
                case_id,
                "--report",
                inspection_path,
            )

            self._event(job_id, "reviewer", f"Preparing blind review for candidate {iteration_number}")
            request = self.client.run("review-request", "--case", case_id)
            case = self.client.status(case_id)
            artifact = Path(case["iterations"][-1]["artifact"]["path"])
            reviewer_prompt = self._reviewer_prompt(
                case_id, Path(request["request"]), case_dir, iteration_number
            )
            usage = self._invoke(
                job_id,
                "reviewer",
                reviewer_prompt,
                self._reviewer_images(
                    Path(case["original"]["path"]),
                    artifact,
                    case_dir,
                    iteration_number,
                ),
                case_dir,
            )
            self._record_usage(case_id, "reviewer", iteration_number, usage)
            case = self.client.status(case_id)
            response_path = case_dir / f"review-response-{iteration_number:02d}.json"
            if case["state"] != "context_reveal" or not response_path.is_file():
                raise RuntimeError(
                    "Reviewer finished without freezing the blind read and writing the revealed response"
                )
            self.client.run(
                "evaluate",
                "--case",
                case_id,
                "--iteration",
                iteration_number,
                "--report",
                response_path,
            )
            case = self.client.status(case_id)
            if not any(item["iteration"] == iteration_number for item in case["evaluations"]):
                raise RuntimeError(
                    "Reviewer finished without recording the independent evaluation through case_manager.py"
                )
            self._event(job_id, "complete", f"Cycle ended in {case['state']}")
            self._finish(job_id, "complete")
        except Exception as exc:  # background boundary: preserve the failure for the UI
            reason = f"Local runner failed: {exc}"
            with self.lock:
                failed_stage = self.jobs[job_id]["stage"]
            self._event(job_id, "failed", reason)
            try:
                state = self.client.status(case_id)["state"]
                if state in (
                    "build",
                    "blind_review",
                    "context_reveal",
                    "revise",
                    "redesign",
                    "user_review",
                ):
                    self.client.run(
                        "stop",
                        "--case",
                        case_id,
                        "--kind",
                        "renderer_failure" if failed_stage == "creator" else "other",
                        "--reason",
                        reason,
                    )
            except Exception:
                pass
            self._finish(job_id, "failed", reason)

    def _invoke(
        self,
        job_id: str,
        stage: str,
        prompt: str,
        images: list[Path],
        case_dir: Path,
    ) -> dict[str, float | int]:
        command = [
            str(self.executable),
            "exec",
            "--ephemeral",
            "--json",
            "--color",
            "never",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "-C",
            str(case_dir),
        ]
        if self.model:
            command.extend(("--model", self.model))
        if self.reasoning_effort:
            command.extend(
                ("--config", f'model_reasoning_effort="{self.reasoning_effort}"')
            )
        for image in images:
            command.extend(("--image", str(image)))
        command.append("-")
        log_path = case_dir / f"local-{job_id}-{stage}.jsonl"
        matplotlib_root = case_dir / ".matplotlib"
        cache_root = case_dir / ".cache"
        matplotlib_root.mkdir(exist_ok=True)
        cache_root.mkdir(exist_ok=True)
        started = time.monotonic()
        result = subprocess.run(
            command,
            cwd=case_dir,
            env=safe_environment(
                {
                    "DATAVIZ_FIX_ROOT": str(self.client.root),
                    "MPLCONFIGDIR": str(matplotlib_root),
                    "PYTHONPATH": str(self.repo_root),
                    "XDG_CACHE_HOME": str(cache_root),
                }
            ),
            input=prompt,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        elapsed = round(time.monotonic() - started, 3)
        log_path.write_text(result.stdout, encoding="utf-8")
        if result.stderr:
            log_path.with_suffix(".stderr.log").write_text(result.stderr, encoding="utf-8")
        self._event(job_id, stage, f"Codex exited {result.returncode} after {elapsed:.1f}s")
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "no process output").strip()
            raise RuntimeError(detail[-1200:])
        usage = self._parse_usage(result.stdout)
        usage["latency_seconds"] = elapsed
        return usage

    def _record_usage(
        self,
        case_id: str,
        stage: str,
        iteration: int,
        usage: dict[str, float | int],
    ) -> None:
        self.client.run(
            "usage",
            "--case",
            case_id,
            "--stage",
            stage,
            "--iteration",
            iteration,
            "--calls",
            1,
            "--input-tokens",
            usage["input_tokens"],
            "--output-tokens",
            usage["output_tokens"],
            "--cached-input-tokens",
            usage["cached_input_tokens"],
            "--latency-seconds",
            usage["latency_seconds"],
        )

    @staticmethod
    def _parse_usage(output: str) -> dict[str, int]:
        usage = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
        for line in output.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "turn.completed" or not isinstance(event.get("usage"), dict):
                continue
            raw = event["usage"]
            usage = {
                "input_tokens": int(raw.get("input_tokens", 0)),
                "output_tokens": int(raw.get("output_tokens", 0)),
                "cached_input_tokens": int(raw.get("cached_input_tokens", 0)),
            }
        return usage

    def _run_creator_stages(
        self,
        job_id: str,
        case: dict[str, Any],
        case_id: str,
        case_dir: Path,
        candidate_path: Path,
        iteration: int,
        context_version: int,
    ) -> None:
        """Drive the repair pipeline as separate scoped calls - no single monolith pass.

        Each call opens only the skills its stage needs (per ``stage_contracts``), and the
        structured artifact of one stage is the input of the next. Diagnose and select emit
        JSON; build renders the candidate PNG and runs the case-manager workflow.
        """
        source_images = self._creator_images(case)
        diagnose_path = case_dir / f"diagnose-{iteration:02d}.json"
        select_path = case_dir / f"select-{iteration:02d}.json"

        # Stage 1 - diagnose and extract. Skills: brief, extract, critique.
        self._event(job_id, "diagnose", f"Diagnosing source for candidate {iteration}")
        usage = self._invoke(
            job_id,
            "diagnose",
            self._diagnose_prompt(case_id, case_dir, diagnose_path, iteration),
            source_images,
            case_dir,
        )
        self._record_usage(case_id, "creator", iteration, usage)
        if not diagnose_path.is_file():
            raise RuntimeError(f"Diagnose stage did not write the brief artifact: {diagnose_path}")

        # Stage 2 - select the form cold. Skills: selector. No image.
        self._event(job_id, "select", f"Selecting the form for candidate {iteration}")
        usage = self._invoke(
            job_id,
            "select",
            self._select_prompt(case_id, case_dir, diagnose_path, select_path, iteration),
            [],
            case_dir,
        )
        self._record_usage(case_id, "creator", iteration, usage)
        if not select_path.is_file():
            raise RuntimeError(f"Select stage did not write the plan artifact: {select_path}")
        builder, active = self._read_builder_choice(select_path)

        # Stage 3 - build. Skills: the chosen builder skill (+ annotations/explainer).
        self._event(job_id, "build", f"Building candidate {iteration} ({builder})")
        usage = self._invoke(
            job_id,
            "build",
            self._build_prompt(
                case_id,
                case_dir,
                candidate_path,
                diagnose_path,
                select_path,
                iteration,
                context_version,
                builder,
                active,
            ),
            source_images,
            case_dir,
        )
        self._record_usage(case_id, "creator", iteration, usage)

    @staticmethod
    def _read_builder_choice(select_path: Path) -> tuple[str, tuple[str, ...]]:
        """Read builder (chart/table) and active conditionals from the select artifact."""
        builder = "chart"
        active: list[str] = []
        try:
            plan = read_json(select_path)
            if plan.get("builder") in ("chart", "table"):
                builder = plan["builder"]
            if plan.get("needs_annotations"):
                active.append("chart-annotations")
            if plan.get("needs_explainer"):
                active.append("chart-explainer")
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return builder, tuple(active)

    def _stage_skill_directive(
        self,
        stage: sc.Stage,
        builder: str | None = None,
        active: tuple[str, ...] = (),
        extra: tuple[str, ...] = (),
    ) -> str:
        """The 'open and follow' line plus guardrails and focus for one stage.

        The skill subset is the authority of ``stage_contracts``; the runner resolves each
        name to its installed SKILL.md so Codex opens only that stage's skills.
        """
        names = list(stage.skill_names(builder=builder, active_conditions=active))
        for name in extra:
            if name not in names:
                names.append(name)
        paths: list[str] = []
        for name in names:
            try:
                paths.append(str(self._skill_path(name)))
            except RuntimeError:
                if name in extra:
                    continue  # optional/environmental skill (e.g. installed writing style)
                raise
        follow = (
            f"Open and follow {', '.join(paths)}. These are required inputs, not optional references."
            if paths
            else "No stage skill is bundled for this stage; apply the prior artifacts directly."
        )
        return f"{sc.GUARDRAIL_PREAMBLE.strip()}\n\n{stage.instructions.strip()}\n\n{follow}"

    def _diagnose_prompt(
        self, case_id: str, case_dir: Path, diagnose_path: Path, iteration: int
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        directive = self._stage_skill_directive(sc.stage("repair", "diagnose"))
        return f"""{directive}

You are the diagnose-and-extract stage for case {case_id}, iteration {iteration}. The attached image is the source. Read the current case using:

DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} status --case {case_id}

Do not choose a form and do not render. Work only inside {case_dir}; do not edit the checked-out repository or any skill. Produce the repair brief (key messages and required content, explicit drops with reasons, audience and medium, and the edit-vs-redesign mode) and recover the full period-by-category data table - a value for every period and every category, series, stack, or facet (colour is data). Difficulty of recovery is never grounds to drop a message or category; put uncertain values and unreadable labels in the limitations and keep the categories.

Save the structured repair brief and attach it with `critique` (the only state-changing case-manager command you may run in this stage). Also write the diagnose artifact as JSON to {diagnose_path} for the next stage. Stop after {diagnose_path} exists."""

    def _select_prompt(
        self,
        case_id: str,
        case_dir: Path,
        diagnose_path: Path,
        select_path: Path,
        iteration: int,
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        directive = self._stage_skill_directive(sc.stage("repair", "select"))
        return f"""{directive}

You are the form-selection stage for case {case_id}, iteration {iteration}. No image is attached - select from the brief, not the picture. Read the diagnose artifact at {diagnose_path} and the recorded context using:

DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} status --case {case_id}

Choose the form cold: the source chart's form gets no vote. Set `builder` to `table` when the intent is exact lookup or the values are not commensurable on one scale, otherwise `chart` - this decides which builder skill the build stage loads. Set `needs_annotations` and `needs_explainer` from whether the plan genuinely calls for on-chart marks or accompanying prose. Produce the design, the layout plan under the declared delivery condition, and an observable acceptance check for every fatal or major problem and every preservation requirement.

Save and attach a complete `design-contract`, including the selector decision whenever form is implicated (the only state-changing case-manager commands you may run in this stage). Also write the select artifact as JSON to {select_path}, with the `builder`, `needs_annotations`, and `needs_explainer` fields, for the next stage. Do not render. Stop after {select_path} exists."""

    def _build_prompt(
        self,
        case_id: str,
        case_dir: Path,
        candidate_path: Path,
        diagnose_path: Path,
        select_path: Path,
        iteration: int,
        context_version: int,
        builder: str,
        active: tuple[str, ...],
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        directive = self._stage_skill_directive(
            sc.stage("repair", "build"),
            builder=builder,
            active=active,
            extra=("karthik-writing-style",),
        )
        semantic_path = case_dir / f"semantic-preflight-v{context_version}.json"
        revision_instruction = (
            "The first attached image is the source. The second is the latest candidate. "
            "Continue from the latest candidate and its generating code in the case directory. "
            "Preserve what already passes and apply only the active corrections and minimum pass set. "
            "Do not restart from the source unless the latest verdict is Redesign."
            if iteration > 1
            else "The attached image is the source. Build the first candidate from it."
        )
        return f"""{directive}

You are the build stage for case {case_id}, iteration {iteration}. The chosen builder is `{builder}`. Read the diagnose artifact at {diagnose_path} and the select artifact at {select_path}, and the recorded context using:

DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} status --case {case_id}

{revision_instruction}

Build exactly one candidate to the plan, carrying every key message with its required content. Work only inside {case_dir}; do not edit the checked-out repository or any skill. Render exactly one real PNG to {candidate_path} and inspect that exact export. Do not run iterate, review-request, blind-submit, evaluate, accept, or diagnose. The wrapper will record the artifact after your process exits.

Before starting the renderer, satisfy the recorded workflow state. Before Revise, attach a `revision-contract` mapping every open evaluator action and new user check. Probe renderers with `dataviz_mcp.rendering.probe_renderers`, save and attach `renderer-selection`, then audit measure, time/context, universe/denominator, claim strength, and audience units. Write the complete context-version {context_version} report to {semantic_path}, run `semantic-preflight`, and finally run `build-check`. These workflow commands are the only state-changing case-manager commands you may run. Treat every structured field marked `inferred` as a hypothesis, not user intent. Each required value must be an observable delivered state.

Treat the active change and preservation checks as the edit boundary. Make each literal requested removal, addition, and relocation; do not retain or restore a forbidden element as a fallback. Expand shared edits across every applicable panel, facet, row, or series; do not stop after fixing one repeated instance. Preserve untouched elements unless a dependent adjustment is necessary for the requested change.

Apply the installed writing or brand-style skill, if one is attached above, to every title, subtitle, annotation, note, and other reader-facing phrase; if none is available, apply the prompt's stated preferences. Accurate copy still fails when it uses generic AI phrasing. Before accepting a palette, identify the closest pair of competing encoded colours and verify that they remain distinct at delivery size, in grayscale, and under common colour-vision deficiencies. A palette name or brand match is not evidence of distinction.

Python, R, Matplotlib, ggplot2, ragg, NumPy, Pillow, and this repo's `dataviz_mcp` package may be available. Use `render_and_inspect_chart(..., renderer="auto")`; it must choose ggplot2 for a supported R builder when the probe succeeds. For a table build, render the gtable through the same path with `content="table"`. Use Matplotlib only for an explicit requirement or a recorded unavailable/unsupported ggplot2 reason. In either renderer, define the visible design deliberately. Write the complete bundle into `{case_dir}` with artifact name `{candidate_path.name}`. An unchanged or perceptually unchanged artifact cannot satisfy an active correction. Copy an artifact unchanged only when no active correction or unresolved evaluator action requires a change. Stop after the inspected PNG exists at {candidate_path}."""

    @staticmethod
    def _creator_images(case: dict[str, Any]) -> list[Path]:
        images = [Path(case["original"]["path"])]
        if case.get("iterations"):
            images.append(Path(case["iterations"][-1]["artifact"]["path"]))
        return images

    @staticmethod
    def _reviewer_images(
        source: Path,
        artifact: Path,
        case_dir: Path,
        iteration: int,
    ) -> list[Path]:
        """Add deterministic delivery and detail views of the exact candidate."""
        images = [source, artifact]
        views = build_review_views(
            artifact,
            case_dir,
            f"review-{iteration:02d}",
        )
        if len(views) >= 3:
            # Retain the historical filenames used by case packets and tests.
            preview_path = case_dir / f"review-delivery-{iteration:02d}.png"
            detail_path = case_dir / f"review-details-{iteration:02d}.png"
            views[1].replace(preview_path)
            views[2].replace(detail_path)
            images.extend((preview_path, detail_path))
            images.extend(views[3:])
        return images

    def _reviewer_prompt(
        self, case_id: str, request_path: Path, case_dir: Path, iteration: int
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        skill = self._skill_path("dataviz-eval")
        visual_skill = self._skill_path("karthik-data-visualization")
        writing_skill = self._skill_path("karthik-writing-style")
        return f"""Open and follow {skill}.

You are a fresh independent reviewer for case {case_id}, iteration {iteration}. You did not create the chart. The first attached image is the source; the second is the exact delivered candidate. When present, the third is a representative delivery-size preview and the fourth is an overlapping detail sheet derived from the exact candidate. Inspect every supplied view. A clean full view cannot override a collision, mismatch, or ambiguity visible in a delivery or detail view.

Open only the blind request at {request_path}. Do not open case.json, creator files, or any reveal file before freezing the blind read. Follow the request exactly: write the blind response, run `DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} blind-submit --case {case_id}`, then open the generated reveal and complete its response template with artifact-specific evidence. Do not run evaluate; the wrapper will validate and record your response after your process exits.

After the blind response is frozen and intent is revealed, open and follow {visual_skill} and {writing_skill}. Use them for the mandatory presentation checks. For Colour distinction, test the closest competing encoded colours at delivery size, in grayscale, and under common colour-vision deficiencies. For Copy style, inspect every title, subtitle, annotation, and note against the applicable writing skill; factual accuracy alone is not a pass.

Inspect the artifact visually before opening any deterministic inspection named in the blind request. Then incorporate that exact-hash inspection result. A complete failing geometry check cannot be overridden by a clean-looking overview; an incomplete raster-only report is unknown, not a pass.

When completing the revealed response, copy both saved `blind_reads` strings byte-for-byte from the frozen blind response. Do not shorten, paraphrase, correct, or otherwise rewrite them after intent is revealed.

Treat active user checks as the change contract. Required actions must not conflict with them. For a narrow repair, judge changed regions absolutely and untouched regions for preservation and regression. Count required replacements in every applicable panel, facet, row, or series; one repaired repeated instance cannot pass for missing siblings. Put unchanged pre-existing defects outside the authorized scope in `baseline_concerns`, not `required_actions`, unless they block the requested correction or materially mislead.

Do not modify the chart, source, skills, or creator files. Stop after the revealed response file exists.
"""

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

from dataviz_mcp.artifacts import read_json, sha256_file
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.review_views import build_review_views


RUNNABLE_STATES = ("build", "revise", "redesign")


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
            self.client.run("build-check", "--case", case_id)
            candidate_path = case_dir / f"runner-{job_id}-candidate-{iteration_number:02d}.png"
            self._event(job_id, "creator", f"Building candidate {iteration_number}")
            creator_prompt = self._creator_prompt(
                case_id, case_dir, candidate_path, iteration_number
            )
            usage = self._invoke(
                job_id,
                "creator",
                creator_prompt,
                self._creator_images(case),
                case_dir,
            )
            self._record_usage(case_id, "creator", iteration_number, usage)
            if not candidate_path.is_file():
                raise RuntimeError(f"Creator did not write the required artifact: {candidate_path}")
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
            inspect_rendered_chart(
                str(recorded_artifact),
                str(layout_path) if layout_path else None,
                str(inspection_path),
            )
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

    def _creator_prompt(
        self,
        case_id: str,
        case_dir: Path,
        candidate_path: Path,
        iteration: int,
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        skill = self.repo_root / "dataviz-fix" / "codex" / "SKILL.md"
        revision_instruction = (
            "The first attached image is the source. The second is the latest candidate. "
            "Continue from the latest candidate and its generating code in the case directory. "
            "Preserve what already passes and apply only the active corrections and minimum pass set. "
            "Do not restart from the source unless the latest verdict is Redesign."
            if iteration > 1
            else "The attached image is the source. Build the first candidate from it."
        )
        return f"""Open and follow {skill}.

You are the chart creator for case {case_id}, not its reviewer. Build exactly one candidate for iteration {iteration}. Read the current case using:

DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} status --case {case_id}

{revision_instruction}

Inspect the recorded context and acceptance checks. Work only inside {case_dir}. Do not edit the checked-out repository or any skill. Render exactly one real PNG to {candidate_path} and inspect that exact export. Do not run iterate, review-request, blind-submit, evaluate, accept, diagnose, or any state-changing case-manager command. The wrapper will record the artifact after your process exits. Stop after the inspected PNG exists at the required path.

Treat the active change and preservation checks as the edit boundary. Make each literal requested removal, addition, and relocation; do not retain or restore a forbidden element as a fallback. Expand shared edits across every applicable panel, facet, row, or series; do not stop after fixing one repeated instance. Preserve untouched elements unless a dependent adjustment is necessary for the requested change.

Python, Matplotlib, NumPy, Pillow, and this repo's `dataviz_mcp` package are available with writable cache directories already configured. Use one Python rendering script with a `build_chart()` function. For a Matplotlib candidate, call `dataviz_mcp.rendering.render_chart` with output_dir `{case_dir}` and artifact_name `{candidate_path.name}` so the wrapper can preserve render metadata and run complete geometry checks. Tag annotation and series artists with stable gids such as `annotation:event-id` and `series:metric-id`. Use no more than six shell calls; do not install packages, probe alternative renderers, or compile another language. An unchanged or perceptually unchanged artifact cannot satisfy an active correction. Copy an artifact unchanged only when no active correction or unresolved evaluator action requires a change.
"""

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
        if views:
            # Retain the historical filenames used by case packets and tests.
            preview_path = case_dir / f"review-delivery-{iteration:02d}.png"
            detail_path = case_dir / f"review-details-{iteration:02d}.png"
            views[0].replace(preview_path)
            views[1].replace(detail_path)
            images.extend((preview_path, detail_path))
        return images

    def _reviewer_prompt(
        self, case_id: str, request_path: Path, case_dir: Path, iteration: int
    ) -> str:
        manager = self.repo_root / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
        skill = self.repo_root / "dataviz-eval" / "codex" / "SKILL.md"
        return f"""Open and follow {skill}.

You are a fresh independent reviewer for case {case_id}, iteration {iteration}. You did not create the chart. The first attached image is the source; the second is the exact delivered candidate. When present, the third is a representative delivery-size preview and the fourth is an overlapping four-region detail sheet derived deterministically from that exact candidate. Inspect every supplied view. A clean full view cannot override a collision, mismatch, or ambiguity visible in a delivery or detail view.

Open only the blind request at {request_path}. Do not open case.json, creator files, or any reveal file before freezing the blind read. Follow the request exactly: write the blind response, run `DATAVIZ_FIX_ROOT={self.client.root} python3 {manager} blind-submit --case {case_id}`, then open the generated reveal and complete its response template with artifact-specific evidence. Do not run evaluate; the wrapper will validate and record your response after your process exits.

Inspect the artifact visually before opening any deterministic inspection named in the blind request. Then incorporate that exact-hash inspection result. A complete failing geometry check cannot be overridden by a clean-looking overview; an incomplete raster-only report is unknown, not a pass.

When completing the revealed response, copy both saved `blind_reads` strings byte-for-byte from the frozen blind response. Do not shorten, paraphrase, correct, or otherwise rewrite them after intent is revealed.

Treat active user checks as the change contract. Required actions must not conflict with them. For a narrow repair, judge changed regions absolutely and untouched regions for preservation and regression. Count required replacements in every applicable panel, facet, row, or series; one repaired repeated instance cannot pass for missing siblings. Put unchanged pre-existing defects outside the authorized scope in `baseline_concerns`, not `required_actions`, unless they block the requested correction or materially mislead.

Do not modify the chart, source, skills, or creator files. Stop after the revealed response file exists.
"""

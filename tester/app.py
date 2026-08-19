from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from tester.local_runner import LocalCodexRunner


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_MANAGER = REPO_ROOT / "dataviz-fix" / "codex" / "scripts" / "case_manager.py"
STATIC_ROOT = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
CONTEXT_FIELDS = (
    "audience",
    "purpose",
    "question",
    "hypothesis",
    "message",
    "medium",
    "dimensions",
    "expansion_available",
    "source_notes",
    "preserve",
    "accessibility",
    "brand",
    "tooling",
    "output_constraints",
)
class ContextUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    source: str = Field(default="user", pattern="^(user|inferred|unknown)$")
    reason: str = "Context updated in the tester"
    clear: list[str] = Field(default_factory=list)
    audience: str | None = None
    purpose: str | None = None
    question: str | None = None
    hypothesis: str | None = None
    message: str | None = None
    medium: str | None = None
    dimensions: str | None = None
    expansion_available: str | None = Field(default=None, pattern="^(yes|no|unknown)$")
    source_notes: str | None = None
    preserve: str | None = None
    accessibility: str | None = None
    brand: str | None = None
    tooling: str | None = None
    output_constraints: str | None = None


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    target: str
    current: str
    required: str
    why: str = ""
    supersedes: list[int] = Field(default_factory=list)
    supersedes_actions: list[str] = Field(default_factory=list)


class RequestCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(pattern="^(change|preserve)$")
    text: str
    target: str
    current: str
    required: str
    why: str = ""


class SemanticDimensionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: str = Field(pattern="^(clear|repair|unknown)$")
    observed: str
    risk: str
    required: str


class SemanticPreflightInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measure: SemanticDimensionInput
    time_context: SemanticDimensionInput
    universe_denominator: SemanticDimensionInput
    claim_strength: SemanticDimensionInput
    audience_units: SemanticDimensionInput


class WorkflowReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: dict


class LimitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int | None = Field(default=None, gt=0)
    max_stalled_evaluations: int | None = Field(default=None, gt=0)
    max_elapsed_minutes: float | None = Field(default=None, gt=0)
    max_tokens: int | None = Field(default=None, gt=0)
    max_cost_usd: float | None = Field(default=None, gt=0)


class StopInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(
        pattern="^(user_stop|iteration_budget|time_budget|token_budget|cost_budget|no_progress|missing_context|missing_evidence|renderer_failure|other)$"
    )
    reason: str


class ResumeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str
    to: str | None = Field(default=None, pattern="^(build|revise|redesign|user_review)$")


def runtime_root() -> Path:
    configured = os.getenv("DATAVIZ_TESTER_ROOT")
    return Path(configured).expanduser().resolve() if configured else REPO_ROOT / ".dataviz-tester"


def validate_case_id(case_id: str) -> str:
    if not SAFE_CASE_ID.fullmatch(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_id


class CaseManagerClient:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def run(self, *args: object) -> dict:
        env = os.environ.copy()
        env["DATAVIZ_FIX_ROOT"] = str(self.root)
        result = subprocess.run(
            [sys.executable, str(CASE_MANAGER), *map(str, args)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Case manager failed").strip()
            raise HTTPException(status_code=409, detail=detail)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Case manager returned invalid JSON") from exc

    def status(self, case_id: str) -> dict:
        return self.run("status", "--case", validate_case_id(case_id))


def validate_raster(path: Path) -> None:
    head = path.read_bytes()[:16]
    if path.suffix.lower() == ".png" and head.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if path.suffix.lower() in (".jpg", ".jpeg") and head.startswith(b"\xff\xd8\xff"):
        return
    raise HTTPException(status_code=400, detail="Upload a real PNG or JPEG file")


async def save_upload(upload: UploadFile, directory: Path) -> Path:
    suffix = Path(upload.filename or "chart.png").suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        raise HTTPException(status_code=400, detail="The local tester currently accepts PNG and JPEG")
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, suffix=suffix, delete=False) as handle:
        target = Path(handle.name)
        total = 0
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Upload exceeds 15 MB")
            handle.write(chunk)
    try:
        validate_raster(target)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    return target


def decorate_case(data: dict) -> dict:
    case_id = data["case_id"]
    decorated = json.loads(json.dumps(data))
    decorated["artifact_urls"] = {
        "original": f"/api/cases/{case_id}/artifacts/original",
        "latest": f"/api/cases/{case_id}/artifacts/latest" if data["iterations"] else None,
        "best": f"/api/cases/{case_id}/artifacts/best" if data.get("best_candidate") else None,
    }
    for iteration in decorated["iterations"]:
        iteration["artifact"]["url"] = (
            f"/api/cases/{case_id}/artifacts/iteration-{iteration['number']}"
        )
    return decorated


def create_app(root: Path | None = None, runner_enabled: bool | None = None) -> FastAPI:
    client = CaseManagerClient(root or runtime_root())
    runner = LocalCodexRunner(client, REPO_ROOT, enabled=runner_enabled)
    app = FastAPI(title="Dataviz repair tester", version="0.1.0")
    app.state.case_manager = client
    app.state.local_runner = runner
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_ROOT / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "local-case-console", **runner.public_config()}

    @app.post("/api/cases")
    async def create_case(
        chart: UploadFile = File(...),
        request: str = Form(default=""),
        audience: str = Form(default=""),
        purpose: str = Form(default=""),
        question: str = Form(default=""),
        hypothesis: str = Form(default=""),
        message: str = Form(default=""),
        medium: str = Form(default=""),
        dimensions: str = Form(default=""),
        preserve: str = Form(default=""),
        max_iterations: int = Form(default=6),
        max_tokens: int | None = Form(default=None),
        max_cost_usd: float | None = Form(default=None),
    ):
        if max_iterations < 1:
            raise HTTPException(status_code=422, detail="max_iterations must be greater than zero")
        if max_cost_usd is not None and max_cost_usd <= 0:
            raise HTTPException(status_code=422, detail="max_cost_usd must be greater than zero")
        if max_tokens is not None and max_tokens <= 0:
            raise HTTPException(status_code=422, detail="max_tokens must be greater than zero")
        session_id = f"tester-{uuid4().hex}"
        upload = await save_upload(chart, client.root / "incoming" / session_id)
        args: list[object] = [
            "start",
            "--session",
            session_id,
            "--image",
            upload,
            "--creator",
            f"tester:{session_id}",
            "--context-source",
            "user",
            "--max-iterations",
            max_iterations,
        ]
        for option, value in (
            ("--request", request),
            ("--audience", audience),
            ("--purpose", purpose),
            ("--question", question),
            ("--hypothesis", hypothesis),
            ("--message", message),
            ("--medium", medium),
            ("--dimensions", dimensions),
            ("--preserve", preserve),
        ):
            if value.strip():
                args.extend((option, value.strip()))
        if max_cost_usd is not None:
            args.extend(("--max-cost-usd", max_cost_usd))
        if max_tokens is not None:
            args.extend(("--max-tokens", max_tokens))
        created = client.run(*args)
        return decorate_case(client.status(created["case_id"]))

    @app.get("/api/cases/{case_id}")
    def get_case(case_id: str):
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/context")
    def update_context(case_id: str, update: ContextUpdate):
        args: list[object] = [
            "context",
            "--case",
            validate_case_id(case_id),
            "--source",
            update.source,
            "--reason",
            update.reason,
        ]
        if update.text:
            args.extend(("--text", update.text))
        if update.clear:
            args.extend(("--clear", ",".join(update.clear)))
        for field in CONTEXT_FIELDS:
            value = getattr(update, field)
            if value is not None:
                args.extend(("--" + field.replace("_", "-"), value))
        client.run(*args)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/feedback")
    def add_feedback(case_id: str, feedback: FeedbackInput):
        args = [
            "feedback",
            "--case",
            validate_case_id(case_id),
            "--text",
            feedback.text,
            "--target",
            feedback.target,
            "--current",
            feedback.current,
            "--required",
            feedback.required,
            "--why",
            feedback.why,
        ]
        if feedback.supersedes:
            args.extend(("--supersedes", ",".join(map(str, feedback.supersedes))))
        if feedback.supersedes_actions:
            args.extend(("--supersedes-actions", ",".join(feedback.supersedes_actions)))
        client.run(*args)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/checks")
    def add_request_check(case_id: str, check: RequestCheckInput):
        args = [
            "check",
            "--case",
            validate_case_id(case_id),
            "--kind",
            check.kind,
            "--text",
            check.text,
            "--target",
            check.target,
            "--current",
            check.current,
            "--required",
            check.required,
            "--why",
            check.why,
        ]
        client.run(*args)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/semantic-preflight")
    def add_semantic_preflight(case_id: str, preflight: SemanticPreflightInput):
        case_id = validate_case_id(case_id)
        case = client.status(case_id)
        case_dir = client.root / "cases" / case_id
        report_path = case_dir / f"tester-semantic-preflight-v{case['context_version']}.json"
        report_path.write_text(
            json.dumps(
                {
                    "context_version": case["context_version"],
                    "dimensions": preflight.model_dump(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        client.run(
            "semantic-preflight",
            "--case",
            case_id,
            "--report",
            report_path,
        )
        return decorate_case(client.status(case_id))

    def attach_workflow_report(
        case_id: str, command: str, payload: WorkflowReportInput
    ) -> dict:
        case_id = validate_case_id(case_id)
        case_dir = client.root / "cases" / case_id
        report_path = case_dir / f"tester-{command}-{uuid4().hex}.json"
        report_path.write_text(
            json.dumps(payload.report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        client.run(command, "--case", case_id, "--report", report_path)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/critique")
    def add_critique(case_id: str, payload: WorkflowReportInput):
        return attach_workflow_report(case_id, "critique", payload)

    @app.post("/api/cases/{case_id}/design-contract")
    def add_design_contract(case_id: str, payload: WorkflowReportInput):
        return attach_workflow_report(case_id, "design-contract", payload)

    @app.post("/api/cases/{case_id}/revision-contract")
    def add_revision_contract(case_id: str, payload: WorkflowReportInput):
        return attach_workflow_report(case_id, "revision-contract", payload)

    @app.post("/api/cases/{case_id}/renderer-selection")
    def add_renderer_selection(case_id: str, payload: WorkflowReportInput):
        return attach_workflow_report(case_id, "renderer-selection", payload)

    @app.post("/api/cases/{case_id}/iterations")
    async def add_iteration(
        case_id: str,
        chart: UploadFile = File(...),
        summary: str = Form(default="Manual candidate upload"),
    ):
        case_id = validate_case_id(case_id)
        upload = await save_upload(chart, client.root / "incoming" / case_id)
        client.run(
            "iterate",
            "--case",
            case_id,
            "--output",
            upload,
            "--summary",
            summary,
        )
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/limits")
    def update_limits(case_id: str, update: LimitUpdate):
        args: list[object] = ["limits", "--case", validate_case_id(case_id)]
        for field, value in update.model_dump(exclude_none=True).items():
            args.extend(("--" + field.replace("_", "-"), value))
        client.run(*args)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/stop")
    def stop_case(case_id: str, stop: StopInput):
        client.run(
            "stop",
            "--case",
            validate_case_id(case_id),
            "--kind",
            stop.kind,
            "--reason",
            stop.reason,
        )
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/resume")
    def resume_case(case_id: str, resume: ResumeInput):
        args: list[object] = [
            "resume",
            "--case",
            validate_case_id(case_id),
            "--reason",
            resume.reason,
        ]
        if resume.to:
            args.extend(("--to", resume.to))
        client.run(*args)
        return decorate_case(client.status(case_id))

    @app.post("/api/cases/{case_id}/run")
    def run_local_cycle(case_id: str):
        case_id = validate_case_id(case_id)
        try:
            return runner.start(case_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        if not re.fullmatch(r"[a-f0-9]{32}", job_id):
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            return runner.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/api/cases/{case_id}/artifacts/{selector}")
    def artifact(case_id: str, selector: str):
        data = client.status(case_id)
        if selector == "original":
            artifact_data = data["original"]
        elif selector == "latest" and data["iterations"]:
            artifact_data = data["iterations"][-1]["artifact"]
        elif selector == "best" and data.get("best_candidate"):
            artifact_data = data["best_candidate"]["artifact"]
        elif selector.startswith("iteration-"):
            try:
                number = int(selector.split("-", 1)[1])
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Artifact not found") from exc
            iteration = next((item for item in data["iterations"] if item["number"] == number), None)
            if iteration is None:
                raise HTTPException(status_code=404, detail="Artifact not found")
            artifact_data = iteration["artifact"]
        else:
            raise HTTPException(status_code=404, detail="Artifact not found")
        artifact_path = Path(artifact_data["path"]).resolve()
        case_root = (client.root / "cases" / validate_case_id(case_id)).resolve()
        if not artifact_path.is_relative_to(case_root) or not artifact_path.is_file():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(artifact_path)

    return app


app = create_app()

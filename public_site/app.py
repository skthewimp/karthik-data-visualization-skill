from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from public_site.runner import OpenAIRepairRunner, read_case, safety_id, write_case


REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PROMPT_CHARS = 1200
MAX_PIXELS = 25_000_000
COOKIE_NAME = "dataviz_session"


def runtime_root() -> Path:
    configured = os.getenv("DATAVIZ_PUBLIC_ROOT")
    return Path(configured).expanduser().resolve() if configured else REPO_ROOT / ".dataviz-public"


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class PublicAccessStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.cases_root = self.root / "cases"
        self.cases_root.mkdir(exist_ok=True)
        self.database = self.root / "public.sqlite3"
        self.salt = self._load_salt()
        self._initialise()

    def _load_salt(self) -> str:
        configured = os.getenv("DATAVIZ_QUOTA_SALT")
        if configured:
            return configured
        path = self.root / ".quota-salt"
        if not path.exists():
            path.write_text(secrets.token_hex(32), encoding="ascii")
            path.chmod(0o600)
        return path.read_text(encoding="ascii").strip()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS public_cases (
                    case_id TEXT PRIMARY KEY,
                    session_hash TEXT NOT NULL,
                    ip_hash TEXT NOT NULL,
                    retries_used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS daily_quota (
                    day TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    quota_key TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    PRIMARY KEY (day, scope, quota_key)
                );
                """
            )

    def session_hash(self, token: str) -> str:
        return hash_value(f"{self.salt}:session:{token}")

    def ip_hash(self, address: str) -> str:
        return hash_value(f"{self.salt}:ip:{address}")

    def reserve_case(self, session_hash: str, ip_hash: str) -> None:
        global_limit = int(os.getenv("DATAVIZ_DAILY_CASE_LIMIT", "50"))
        ip_limit = int(os.getenv("DATAVIZ_DAILY_IP_LIMIT", "3"))
        day = utc_day()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for scope, key, limit in (
                ("global", "all", global_limit),
                ("ip", ip_hash, ip_limit),
            ):
                row = connection.execute(
                    "SELECT count FROM daily_quota WHERE day=? AND scope=? AND quota_key=?",
                    (day, scope, key),
                ).fetchone()
                count = int(row["count"]) if row else 0
                if count >= limit:
                    message = (
                        "Today’s repair allowance has been used. Try again tomorrow."
                        if scope == "global"
                        else "This connection has used today’s repair allowance. Try again tomorrow."
                    )
                    raise HTTPException(status_code=429, detail=message)
            for scope, key in (("global", "all"), ("ip", ip_hash)):
                connection.execute(
                    """
                    INSERT INTO daily_quota(day, scope, quota_key, count) VALUES (?, ?, ?, 1)
                    ON CONFLICT(day, scope, quota_key) DO UPDATE SET count=count+1
                    """,
                    (day, scope, key),
                )

    def register_case(self, case_id: str, session_hash: str, ip_hash: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO public_cases VALUES (?, ?, ?, 0, ?)",
                (case_id, session_hash, ip_hash, datetime.now(timezone.utc).isoformat()),
            )

    def cleanup_expired(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT case_id FROM public_cases WHERE created_at < ?",
                (cutoff.isoformat(),),
            ).fetchall()
            connection.execute(
                "DELETE FROM public_cases WHERE created_at < ?",
                (cutoff.isoformat(),),
            )
            connection.execute(
                "DELETE FROM daily_quota WHERE day < ?",
                ((datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat(),),
            )
        for row in rows:
            case_dir = (self.cases_root / row["case_id"]).resolve()
            if case_dir.parent == self.cases_root and case_dir.is_dir():
                shutil.rmtree(case_dir)

    def recover_interrupted(self) -> None:
        for path in self.cases_root.glob("*/case.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("status") not in ("queued", "processing"):
                continue
            data["status"] = "failed"
            data["error"] = "The service restarted before this repair finished. Please start again."
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            write_case(path.parent, data)

    def require_case(self, case_id: str, session_hash: str) -> sqlite3.Row:
        if not case_id or any(character not in "abcdef0123456789" for character in case_id):
            raise HTTPException(status_code=404, detail="Repair not found")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM public_cases WHERE case_id=? AND session_hash=?",
                (case_id, session_hash),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Repair not found")
        return row

    def use_retry(self, case_id: str, session_hash: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE public_cases SET retries_used=1
                WHERE case_id=? AND session_hash=? AND retries_used=0
                """,
                (case_id, session_hash),
            )
            if cursor.rowcount != 1:
                raise HTTPException(status_code=409, detail="This chart has already used its retry")

    def release_retry(self, case_id: str, session_hash: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE public_cases SET retries_used=0 WHERE case_id=? AND session_hash=?",
                (case_id, session_hash),
            )


def client_address(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def session_for(request: Request) -> tuple[str, bool]:
    token = request.cookies.get(COOKIE_NAME)
    if token and len(token) >= 32:
        return token, False
    return secrets.token_urlsafe(32), True


def set_session_cookie(response: Response, token: str, secure: bool) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=60 * 60 * 24,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


async def save_image(upload: UploadFile, directory: Path) -> Path:
    suffix = Path(upload.filename or "chart.png").suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        raise HTTPException(status_code=400, detail="Upload a PNG or JPEG chart")
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, suffix=suffix, delete=False) as handle:
        temporary = Path(handle.name)
        total = 0
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                temporary.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="The chart exceeds 8 MB")
            handle.write(chunk)
    try:
        with Image.open(temporary) as image:
            image.verify()
        with Image.open(temporary) as image:
            if image.width * image.height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="The chart has too many pixels")
            if image.width < 320 or image.height < 240:
                raise HTTPException(status_code=400, detail="Upload a chart at least 320 × 240 pixels")
            target = directory / "original.png"
            image.convert("RGB").save(target, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="Upload a valid PNG or JPEG chart") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return target


def public_case(data: dict[str, Any], retries_used: bool) -> dict[str, Any]:
    latest = data.get("iterations", [])[-1] if data.get("iterations") else None
    review = latest.get("review") if latest else None
    return {
        "case_id": data["case_id"],
        "status": data["status"],
        "error": data.get("error"),
        "prompt": data["prompt"],
        "original_url": f"/api/cases/{data['case_id']}/original",
        "repaired_url": f"/api/cases/{data['case_id']}/repaired" if latest else None,
        "download_url": f"/api/cases/{data['case_id']}/download" if latest else None,
        "review": review,
        "can_retry": bool(latest and not retries_used),
        "values_note": "Values are reconstructed from the screenshot and may be approximate.",
    }


def create_app(
    root: Path | None = None,
    runner: OpenAIRepairRunner | Any | None = None,
    secure_cookie: bool | None = None,
) -> FastAPI:
    access = PublicAccessStore(root or runtime_root())
    access.cleanup_expired()
    access.recover_interrupted()
    repair_runner = runner or OpenAIRepairRunner()
    cookie_secure = (
        os.getenv("DATAVIZ_SECURE_COOKIE", "1") == "1"
        if secure_cookie is None
        else secure_cookie
    )
    cleanup_stop = threading.Event()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        def cleanup_loop() -> None:
            while not cleanup_stop.wait(60 * 60):
                access.cleanup_expired()

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        try:
            yield
        finally:
            cleanup_stop.set()
            cleanup_thread.join(timeout=1)

    app = FastAPI(
        title="Dataviz repair",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.access = access
    app.state.runner = repair_runner
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

    def identity(request: Request) -> tuple[str, str]:
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            raise HTTPException(status_code=404, detail="Repair not found")
        return token, access.session_hash(token)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_ROOT / "index.html")

    @app.get("/healthz")
    def health() -> dict[str, object]:
        return {"status": "ok", **repair_runner.public_config()}

    @app.post("/api/cases")
    async def create_case(
        request: Request,
        response: Response,
        chart: UploadFile = File(...),
        prompt: str = Form(...),
    ) -> dict[str, Any]:
        prompt = " ".join(prompt.split()).strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="Tell me what you want fixed")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise HTTPException(status_code=422, detail="Keep the prompt under 1,200 characters")
        token, is_new = session_for(request)
        session_hash = access.session_hash(token)
        ip_hash = access.ip_hash(client_address(request))
        case_id = uuid4().hex
        case_dir = access.cases_root / case_id
        try:
            original = await save_image(chart, case_dir)
            access.reserve_case(session_hash, ip_hash)
        except Exception:
            if case_dir.parent == access.cases_root and case_dir.is_dir():
                shutil.rmtree(case_dir)
            raise
        data = {
            "case_id": case_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
            "prompt": prompt,
            "original": original.name,
            "pending_feedback": None,
            "iterations": [],
            "job": None,
            "error": None,
        }
        write_case(case_dir, data)
        access.register_case(case_id, session_hash, ip_hash)
        try:
            repair_runner.start(case_dir, safety_id(session_hash))
        except (RuntimeError, ValueError) as exc:
            data["status"] = "failed"
            data["error"] = str(exc)
            write_case(case_dir, data)
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if is_new:
            set_session_cookie(response, token, cookie_secure)
        return public_case(read_case(case_dir), retries_used=False)

    @app.get("/api/cases/{case_id}")
    def get_case(case_id: str, request: Request) -> dict[str, Any]:
        _, session_hash = identity(request)
        row = access.require_case(case_id, session_hash)
        return public_case(
            read_case(access.cases_root / case_id), bool(row["retries_used"])
        )

    @app.post("/api/cases/{case_id}/retry")
    def retry_case(
        case_id: str,
        request: Request,
        feedback: str = Form(...),
    ) -> dict[str, Any]:
        _, session_hash = identity(request)
        row = access.require_case(case_id, session_hash)
        data = read_case(access.cases_root / case_id)
        feedback = " ".join(feedback.split()).strip()
        if not feedback:
            raise HTTPException(status_code=422, detail="Tell me what to change")
        if len(feedback) > MAX_PROMPT_CHARS:
            raise HTTPException(status_code=422, detail="Keep the retry under 1,200 characters")
        if data["status"] != "ready":
            raise HTTPException(status_code=409, detail="Wait for the current repair to finish")
        if row["retries_used"]:
            raise HTTPException(status_code=409, detail="This chart has already used its retry")
        access.use_retry(case_id, session_hash)
        data["pending_feedback"] = feedback
        data["status"] = "queued"
        data["error"] = None
        write_case(access.cases_root / case_id, data)
        try:
            repair_runner.start(access.cases_root / case_id, safety_id(session_hash))
        except (RuntimeError, ValueError) as exc:
            access.release_retry(case_id, session_hash)
            data["status"] = "ready"
            data["pending_feedback"] = None
            write_case(access.cases_root / case_id, data)
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return public_case(read_case(access.cases_root / case_id), retries_used=True)

    def artifact(case_id: str, request: Request, repaired: bool) -> tuple[Path, str]:
        _, session_hash = identity(request)
        access.require_case(case_id, session_hash)
        data = read_case(access.cases_root / case_id)
        if repaired:
            if not data.get("iterations"):
                raise HTTPException(status_code=404, detail="Repaired chart not found")
            path = access.cases_root / case_id / data["iterations"][-1]["artifact"]
            name = "repaired-chart.png"
        else:
            path = access.cases_root / case_id / data["original"]
            name = "original-chart.png"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Chart not found")
        return path, name

    @app.get("/api/cases/{case_id}/original")
    def original(case_id: str, request: Request) -> FileResponse:
        path, _ = artifact(case_id, request, False)
        return FileResponse(path, media_type="image/png")

    @app.get("/api/cases/{case_id}/repaired")
    def repaired(case_id: str, request: Request) -> FileResponse:
        path, _ = artifact(case_id, request, True)
        return FileResponse(path, media_type="image/png")

    @app.get("/api/cases/{case_id}/download")
    def download(case_id: str, request: Request) -> FileResponse:
        path, name = artifact(case_id, request, True)
        return FileResponse(path, media_type="image/png", filename=name)

    return app


app = create_app()

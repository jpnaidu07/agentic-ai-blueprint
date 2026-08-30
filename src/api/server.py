"""Same-origin development API with authenticated resources and isolated demo routes."""

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.tender.api import router
from src.tender.security import authenticate
from src.tender.store import Store

if os.getenv("BLUEPRINT_LOAD_DOTENV", "true").lower() == "true":
    load_dotenv()
logger = logging.getLogger("blueprint.requests")


class BodyLimit:
    """Bound request bodies before multipart parsing or file spooling."""

    def __init__(self, app, limit=11 * 1024 * 1024):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                return await JSONResponse({"detail": "Request exceeds 11 MiB"}, 413)(
                    scope, receive, send
                )
            messages.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(messages)

        async def replay():
            try:
                return next(iterator)
            except StopIteration:
                return await receive()

        await self.app(scope, replay, send)


def create_app(database_url=None, scanner=None):
    @asynccontextmanager
    async def lifespan(app):
        url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/tender.sqlite")
        if url == "sqlite:///data/tender.sqlite":
            Path("data").mkdir(exist_ok=True)
        app.state.tender_store = Store(url)
        app.state.malware_scanner = scanner
        yield
        app.state.tender_store.engine.dispose()

    app = FastAPI(
        title="Agentic AI Blueprint — Tender Reference", version="0.2.0", lifespan=lifespan
    )
    app.add_middleware(BodyLimit)
    app.include_router(router)
    ui_dir = Path(__file__).resolve().parents[1] / "tender" / "ui"
    if ui_dir.is_dir():
        app.mount("/static", StaticFiles(directory=ui_dir), name="static")

    @app.middleware("http")
    async def request_metadata(request: Request, call_next):
        request_id = uuid.uuid4().hex
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        # No query strings, tokens, filenames, prompts, evidence or request/response bodies.
        route = request.scope.get("route")
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "route": getattr(route, "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                }
            )
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    def dashboard():
        return (ui_dir / "index.html").read_text(encoding="utf-8")

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "mode": "development-reference",
            "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
            "llm_configured": bool(os.getenv("LLM_MODEL")),
            "live_provider_verified": False,
        }

    @app.get("/api/me")
    def me(principal=Depends(authenticate)):
        return {
            "user_id": principal.user_id,
            "role": principal.role,
            "tender_ids": principal.tender_ids,
        }

    def demo_access(principal=Depends(authenticate)):
        principal.authorize(roles={"admin", "evaluator"})
        if os.getenv("ENABLE_DEMO_ROUTES", "false").lower() != "true":
            raise HTTPException(404, "Infrastructure simulation routes are disabled")
        return principal

    class ProblemRequest(BaseModel):
        problem_id: str = Field(pattern="^P[123]$")
        mode: str = Field(default="improved", pattern="^(brute_force|improved)$")
        target_id: str | None = Field(default=None, max_length=80)

    @app.post("/api/problems/run", dependencies=[Depends(demo_access)])
    def run_problem(body: ProblemRequest):
        from src.solutions.problem1_disk_health.improved_agent import run_disk_triage_improved
        from src.solutions.problem2_patch_automation.improved_agent import (
            run_patch_automation_improved,
        )
        from src.solutions.problem3_log_triage.improved_agent import run_log_triage_improved

        if body.mode != "improved":
            raise HTTPException(422, "Brute-force baselines are CLI-only educational examples")
        runners = {
            "P1": (run_disk_triage_improved, "SV-10492"),
            "P2": (run_patch_automation_improved, "CL-PROD-01"),
            "P3": (run_log_triage_improved, "INC-LOG-992"),
        }
        run, target = runners[body.problem_id]
        return run(body.target_id or target)

    class StreamRequest(BaseModel):
        prompt: str = Field(min_length=3, max_length=10000)

    @app.post("/api/agent/stream", dependencies=[Depends(demo_access)])
    def stream(body: StreamRequest):
        from src.agent.llm_client import LLMClient
        from src.agent.orchestrator import AgentOrchestrator

        # This route is explicitly a simulation; it cannot reach live provider/tool accounts.
        orchestrator = AgentOrchestrator(LLMClient(provider="mock"))

        def events():
            for event in orchestrator.run_stream(body.prompt, task_id=uuid.uuid4().hex):
                yield "data: " + json.dumps(event.to_dict()) + "\n\n"

        # A synchronous iterator runs in Starlette's threadpool, not the event loop.
        return StreamingResponse(events(), media_type="text/event-stream")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.server:app", host=os.getenv("BIND_HOST", "127.0.0.1"), port=8000)

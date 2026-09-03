"""Loopback-only developer control plane. Run one process; never publish this API."""

import argparse
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from src.blueprint import specs
from src.workbench.contracts import (
    Action,
    Approval,
    Brief,
    Connection,
    ModelList,
    Question,
    RunRequest,
    SpecEdit,
    Stage,
)
from src.workbench.engine import Engine
from src.workbench.jobs import Jobs
from src.workbench.providers import PROVIDERS, Providers
from src.workbench.runtime import Runtime
from src.workbench.security import Sessions, WorkbenchError, local_path
from src.workbench.system import inspect_system


class RequestLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD"}:
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > 2_000_000:
                return await JSONResponse({"detail": "Request exceeds 2 MB"}, 413)(
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


def create_app(root=None, token=None, port=8080, providers=None, runtime_factory=Runtime):
    root = Path(root or Path(__file__).resolve().parents[2]).resolve()
    state = root / ".workbench"
    if state.is_symlink() or not state.resolve().is_relative_to(root):
        raise ValueError("Workbench state must stay inside the checkout")
    state.mkdir(exist_ok=True)
    sessions = Sessions(token or secrets.token_urlsafe(32))
    jobs = Jobs(state)
    runtime = runtime_factory(root, state)
    providers = providers or Providers()
    engine = Engine(root, state, providers, jobs, runtime)

    @asynccontextmanager
    async def lifespan(app):
        yield
        jobs.cancelled.set()
        runtime.close()
        sessions.items.clear()

    app = FastAPI(
        title="Agentic AI Blueprint · Local Workbench",
        version="0.4.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.sessions, app.state.jobs, app.state.runtime, app.state.engine = (
        sessions,
        jobs,
        runtime,
        engine,
    )
    app.add_middleware(RequestLimit)
    ui = Path(__file__).parent / "ui"
    app.mount("/assets", StaticFiles(directory=ui), name="assets")

    @app.middleware("http")
    async def boundary(request, call_next):
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        host = request.headers.get("host", "")
        origin = request.headers.get("origin")
        if (
            not request.client
            or request.client.host not in {"127.0.0.1", "::1"}
            or host not in allowed
        ):
            return JSONResponse(
                {
                    "detail": "This workbench accepts loopback requests with its configured Host only."
                },
                403,
            )
        if origin and origin != f"http://{host}":
            return JSONResponse({"detail": "Cross-origin requests are forbidden."}, 403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site requests are forbidden."}, 403)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            }
        )
        return response

    @app.exception_handler(WorkbenchError)
    async def safe_error(request, exc):
        return JSONResponse({"detail": str(exc)}, 409)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            {
                "detail": "Request failed validation. Check field values and required confirmations; secret inputs are not echoed."
            },
            422,
        )

    @app.exception_handler(ValidationError)
    async def model_validation_error(request, exc):
        return JSONResponse(
            {
                "detail": "Specification/schema validation failed. Check required fields, relationships and module values."
            },
            422,
        )

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return JSONResponse(
            {
                "detail": "The operation failed validation. Check current specs, dependencies and model configuration."
            },
            422,
        )

    @app.exception_handler(yaml.YAMLError)
    async def yaml_error(request, exc):
        return JSONResponse({"detail": "Invalid YAML. No parsed input is echoed."}, 422)

    def authenticated(request: Request):
        return sessions.require(request)

    def connection(session):
        if not session.connection:
            raise WorkbenchError("Connect and test an LLM in Model connection first.")
        return session.connection.model_copy(deep=True)

    def idle():
        if jobs.active:
            raise WorkbenchError("Wait for the active operation before editing or approving specs.")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (ui / "index.html").read_text(encoding="utf-8")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "blueprint-workbench", "version": "0.4.0"}

    @app.post("/api/session")
    def pair(request: Request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or len(header) > 4096:
            raise HTTPException(401, "Enter the pairing token printed by the local server.")
        key, session = sessions.pair(header[7:])
        # Cookies are not port-scoped: never expose an ambient workbench credential
        # to a generated application running on another localhost port.
        return {"session_token": key, "csrf": session.csrf, "connected": False}

    @app.get("/api/session")
    def session_info(session=Depends(authenticated)):
        return {
            "csrf": session.csrf,
            "connected": bool(session.connection),
            "provider": session.connection.provider if session.connection else None,
            "model": session.connection.model if session.connection else None,
        }

    @app.delete("/api/session")
    def logout(request: Request, session=Depends(authenticated)):
        jobs.cancelled.set()
        sessions.clear(request)
        return {
            "message": "Session disconnected. Any in-flight provider call releases its key when it finishes."
        }

    @app.get("/api/system", dependencies=[Depends(authenticated)])
    def system():
        return inspect_system(root)

    @app.get("/api/providers", dependencies=[Depends(authenticated)])
    def provider_list():
        return PROVIDERS

    @app.post("/api/providers/models")
    def provider_models(body: ModelList, session=Depends(authenticated)):
        return providers.models(body.provider, body.api_key.get_secret_value())

    @app.post("/api/connection")
    def connect(body: Connection, session=Depends(authenticated)):
        from src.agent.llm_client import LLMError

        try:
            result = providers.probe(body)
        except LLMError as exc:
            raise WorkbenchError(str(exc)) from None
        session.connection = body
        return result

    @app.delete("/api/connection")
    def disconnect(session=Depends(authenticated)):
        session.connection = None
        jobs.cancelled.set()
        return {
            "message": "Model disconnected. A running call, if any, will finish/cancel at its next safe boundary."
        }

    def catalog():
        items = []
        for file in sorted((root / "skills").glob("*/SKILL.md")):
            text = local_path(root, file.relative_to(root).as_posix()).read_text(encoding="utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1]) if text.startswith("---") else {}
            items.append(
                {
                    "id": file.relative_to(root).as_posix(),
                    "name": metadata.get("name", file.parent.name),
                    "description": metadata.get("description", ""),
                    "kind": "skill",
                }
            )
        for relative in [
            "templates/use-case.yaml",
            "blueprint/tender-use-case.yaml",
            "docs/workbench.md",
            "docs/workflow.md",
            "docs/providers.md",
            "README.md",
            *[
                f"blueprint/schemas/{name}.schema.json"
                for name in ("use-case", "design", "decomposition")
            ],
            ".agents/skills/blueprint-workflow/SKILL.md",
            *[
                file.relative_to(root).as_posix()
                for file in sorted((root / "skills").glob("*/references/*.md"))
            ],
        ]:
            if (root / relative).is_file():
                items.append(
                    {
                        "id": relative,
                        "name": Path(relative).name
                        if not relative.startswith(".agents")
                        else "blueprint-workflow",
                        "description": relative,
                        "kind": "reference",
                    }
                )
        return items

    @app.get("/api/catalog", dependencies=[Depends(authenticated)])
    def get_catalog():
        return {
            "modules": [{"number": n, "name": name} for n, name in enumerate(specs.MODULES, 1)],
            "items": catalog(),
        }

    @app.get("/api/catalog/content", dependencies=[Depends(authenticated)])
    def catalog_content(item: str):
        if item not in {entry["id"] for entry in catalog()}:
            raise HTTPException(404, "Catalog item not found")
        file = root / item
        if (
            not file.resolve().is_relative_to(root)
            or file.is_symlink()
            or file.stat().st_size > 200000
        ):
            raise WorkbenchError("Catalog file is not a bounded repository resource.")
        return {"content": file.read_text(encoding="utf-8"), "path": item}

    @app.get("/api/solutions", dependencies=[Depends(authenticated)])
    def solutions():
        result = []
        for path in sorted((root / "solutions").glob("*")):
            if path.is_dir() and not path.name.startswith("."):
                try:
                    info = engine.overview(path.name)
                    case = specs.read_yaml(path / "capability/capability.yaml")
                    result.append(
                        {
                            "name": path.name,
                            "title": case.get("title", path.name),
                            "stage": info["stage"],
                            "approved": info["approved"],
                            "completed": sum(t["state"] == "complete" for t in info["tasks"]),
                            "tasks": len(info["tasks"]),
                            "reference": info["reference"],
                        }
                    )
                except (ValueError, OSError, yaml.YAMLError):
                    result.append(
                        {
                            "name": path.name,
                            "title": path.name,
                            "stage": "needs-repair",
                            "approved": False,
                            "completed": 0,
                            "tasks": 0,
                        }
                    )
        return result

    @app.get("/api/solutions/{name}", dependencies=[Depends(authenticated)])
    def solution(name: str):
        return engine.overview(name)

    @app.post("/api/solutions")
    def create(body: Brief, session=Depends(authenticated)):
        conn = connection(session)
        return jobs.start("capability", body.name, lambda job: engine.capability(body, conn, job))

    @app.post("/api/solutions/{name}/stages")
    def stage(name: str, body: Stage, session=Depends(authenticated)):
        specs.safe_solution(root, name)
        conn = connection(session)
        return jobs.start(body.stage, name, lambda job: engine.stage(name, body.stage, conn, job))

    @app.put("/api/solutions/{name}/specs", dependencies=[Depends(authenticated)])
    def edit(name: str, body: SpecEdit):
        if not body.confirmed:
            raise WorkbenchError("Confirm that you reviewed the edit and its dependent stages.")
        with jobs.lock:
            idle()
            return engine.edit(name, body.section, body.content, body.sha256)

    @app.post("/api/solutions/{name}/approve", dependencies=[Depends(authenticated)])
    def approve(name: str, body: Approval):
        if not body.confirmed:
            raise WorkbenchError("Review all three specifications and confirm approval.")
        with jobs.lock:
            idle()
            path = specs.safe_solution(root, name)
            if specs.spec_digest(path) != body.spec_digest:
                raise WorkbenchError(
                    "Specs changed after you opened them. Refresh and review before approval."
                )
            specs.approve(path, body.reviewer)
        return {
            "message": "Approved current specs for local engineering; this is not a procurement or production approval."
        }

    @app.post("/api/solutions/{name}/run")
    def run(name: str, body: RunRequest, session=Depends(authenticated)):
        specs.safe_solution(root, name)
        conn = None if name == "government-tender-processing" else connection(session)
        return jobs.start("implementation", name, lambda job: engine.run(name, body, conn, job))

    @app.post("/api/ask")
    def ask(body: Question, session=Depends(authenticated)):
        conn = connection(session)
        return jobs.start("advice", body.solution, lambda job: engine.ask(body, conn, job))

    @app.get("/api/jobs", dependencies=[Depends(authenticated)])
    def list_jobs():
        return jobs.list()

    @app.get("/api/jobs/{job_id}", dependencies=[Depends(authenticated)])
    def get_job(job_id: str):
        return jobs.get(job_id)

    @app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(authenticated)])
    def cancel(job_id: str):
        if jobs.active != job_id:
            raise WorkbenchError("That job is not running.")
        jobs.cancelled.set()
        return {
            "message": "Cancellation requested. The current bounded provider/process operation must finish before the next safe boundary."
        }

    @app.post("/api/actions", dependencies=[Depends(authenticated)])
    def action(body: Action):
        return jobs.start(
            "setup",
            body.solution,
            lambda job: runtime.action(body, lambda message: jobs.event(job, message)),
        )

    @app.get("/api/apps", dependencies=[Depends(authenticated)])
    def apps():
        return [
            {
                "solution": key,
                "url": value.get("url"),
                "kind": value["kind"],
                "running": runtime.running(value),
            }
            for key, value in list(runtime.apps.items())
            if value.get("url")
        ]

    @app.post("/api/apps/{name}/credentials", dependencies=[Depends(authenticated)])
    def credentials(name: str):
        if name != "government-tender-processing" or name not in runtime.apps:
            raise HTTPException(404, "No local role tokens for this app")
        return {
            "tokens": runtime.apps[name]["tokens"],
            "warning": "Development identities for synthetic documents only. Keep roles separate; an evaluator cannot approve their own work.",
        }

    return app


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use an unprivileged port between 1024 and 65535")
    token = os.getenv("WORKBENCH_TOKEN") or secrets.token_urlsafe(32)
    app = create_app(args.root, token, args.port)
    print(
        f"\nBlueprint Workbench: http://127.0.0.1:{args.port}\nLocal pairing token (paste in UI; do not share): {token}\nKeys are session-only. Keep this server local. Ctrl+C stops managed apps.\n",
        flush=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, proxy_headers=False)


if __name__ == "__main__":
    main()

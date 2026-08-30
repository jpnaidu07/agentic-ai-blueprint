"""
FastAPI Server for Enterprise Agentic AI Platform.
Provides REST APIs, SSE real-time thought trace streaming, problem runners, and UI hosting.
"""

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent.orchestrator import AgentOrchestrator
from src.agent.llm_client import LLMClient
from src.connectors.mock_ome_api import MOCK_FLEET_DB, MockRedfishClient
from src.evals.eval_harness import run_evaluation_benchmark
from src.tools.mcp_server import MCPServer
from src.solutions.problem1_disk_health.brute_force import run_disk_triage_brute_force
from src.solutions.problem1_disk_health.improved_agent import run_disk_triage_improved
from src.solutions.problem2_patch_automation.brute_force import run_patch_automation_brute_force
from src.solutions.problem2_patch_automation.improved_agent import run_patch_automation_improved
from src.solutions.problem3_log_triage.brute_force import run_log_triage_brute_force
from src.solutions.problem3_log_triage.improved_agent import run_log_triage_improved

app = FastAPI(title="Agentic AI Blueprint API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static UI files
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
if os.path.exists(UI_DIR):
    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_path = os.path.join(UI_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Agentic AI Blueprint Server Running</h1>")

@app.get("/api/health")
async def health_check():
    client = LLMClient()
    return {
        "status": "HEALTHY",
        "system": "Dell PowerEdge / Polaris Agent Runtime",
        "target_hardware": "Intel Core Ultra 9 285H, 32GB RAM, Intel Arc 140T GPU (16GB)",
        "active_llm_provider": client.active_provider,
        "active_model": client.model,
        "mcp_tools_registered": len(MCPServer.list_tools())
    }

class ProblemRunRequest(BaseModel):
    problem_id: str  # P1, P2, P3
    mode: str = "improved"  # brute_force or improved
    target_id: Optional[str] = None

@app.post("/api/problems/run")
async def run_problem(req: ProblemRunRequest):
    if req.problem_id == "P1":
        if req.mode == "brute_force":
            res = run_disk_triage_brute_force("ALERT: SMART threshold exceeded on SV-10492 Drive bay 2")
        else:
            res = run_disk_triage_improved(req.target_id or "SV-10492")
        return res

    elif req.problem_id == "P2":
        if req.mode == "brute_force":
            res = run_patch_automation_brute_force("inventory.csv")
        else:
            res = run_patch_automation_improved(req.target_id or "CL-PROD-01")
        return res

    elif req.problem_id == "P3":
        if req.mode == "brute_force":
            res = run_log_triage_brute_force("sample raw logs")
        else:
            res = run_log_triage_improved(req.target_id or "INC-LOG-992")
        return res

    return JSONResponse(status_code=400, content={"error": "Invalid problem_id. Use P1, P2, or P3."})

@app.get("/api/agent/stream")
async def stream_agent(prompt: str, task_id: str = "TASK-STREAM-01"):
    """Server-Sent Events (SSE) stream for real-time Thought, Action, Observation, and Synthesis."""
    orchestrator = AgentOrchestrator()

    async def event_generator():
        for event in orchestrator.run_stream(user_prompt=prompt, task_id=task_id):
            payload = json.dumps(event.to_dict())
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/telemetry/fleet")
async def get_fleet_telemetry():
    """Returns mock Dell OME fleet nodes and drive health status."""
    nodes = []
    for k, v in MOCK_FLEET_DB.items():
        nodes.append({
            "server_id": v.server_id,
            "model": v.model,
            "chassis_id": v.chassis_id,
            "power_state": v.power_state,
            "running_vms": v.running_vms_count,
            "drives_count": len(v.drives),
            "critical_drives": sum(1 for d in v.drives if d.health_status == "Critical" or d.reallocated_sector_count > 50)
        })
    return {"total_servers_simulated": len(nodes), "nodes": nodes}

@app.get("/api/evals/benchmark")
async def get_benchmark_scorecard():
    """Runs and returns the live evaluation scorecard."""
    scorecard = run_evaluation_benchmark()
    return scorecard

@app.post("/api/mcp/call")
async def mcp_call(request: Request):
    body = await request.json()
    tool_name = body.get("name")
    arguments = body.get("arguments", {})
    res = MCPServer.call_tool(tool_name, arguments)
    return res

from src.connectors.slack_discord_connector import SlackDiscordConnector, SlackCommandRequest, DiscordWebhookPayload

@app.post("/api/integrations/slack/events")
async def slack_slash_command(request: Request):
    """Handles incoming Slack slash commands (e.g. /triage SV-10492, /patch CL-PROD-01)."""
    form_data = await request.form()
    cmd_req = SlackCommandRequest(
        command=form_data.get("command", "/triage"),
        text=form_data.get("text", "SV-10492"),
        user_name=form_data.get("user_name", "operator"),
        channel_id=form_data.get("channel_id", "C01234567")
    )
    return SlackDiscordConnector.handle_slack_slash_command(cmd_req)

@app.post("/api/integrations/discord/webhook")
async def discord_webhook(payload: DiscordWebhookPayload):
    """Simulates sending an alert to a Discord operational webhook."""
    return SlackDiscordConnector.format_discord_notification(
        title="Fleet Telemetry Alert",
        description=payload.content
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enterprise Agentic AI Platform on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


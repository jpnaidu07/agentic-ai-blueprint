"""
Problem 1: Disk Health Triage - explicit offline tool demonstration.
Demonstrates autonomous ReAct loop, Redfish REST API queries, local lexical runbook retrieval, and idempotent ticketing.
"""

from typing import Any, Dict

from src.agent.llm_client import LLMClient
from src.agent.orchestrator import AgentOrchestrator


def run_disk_triage_improved(server_id: str = "SV-10492") -> Dict[str, Any]:
    """Runs the explicit offline ReAct demonstration for disk health triage."""
    orchestrator = AgentOrchestrator(LLMClient(provider="mock"))
    prompt = (
        f"Perform an automated disk health triage for server {server_id}. "
        "Query Redfish storage telemetry, check Dell PowerEdge runbooks via RAG, "
        "and dispatch an idempotent service ticket if predictive failure thresholds are exceeded."
    )
    events = list(orchestrator.run_stream(user_prompt=prompt, task_id=f"TASK-DISK-{server_id}"))

    synthesis_event = next((e for e in reversed(events) if e.event_type == "SYNTHESIS"), None)
    tool_events = [e for e in events if e.event_type == "ACTION_DISPATCHED"]

    succeeded = {
        e.data["tool"] for e in events if e.event_type == "OBSERVATION" and e.data["success"]
    }
    return {
        "mode": "OFFLINE_DEMO",
        "task_id": f"TASK-DISK-{server_id}",
        "tools_called": len(tool_events),
        "tools_invoked": [e.data.get("tool") for e in tool_events],
        "rag_grounded": "rag_search_runbook" in succeeded,
        "idempotent_ticket_created": "submit_service_ticket" in succeeded,
        "final_synthesis": synthesis_event.data.get("response") if synthesis_event else "",
        "total_latency_ms": synthesis_event.data.get("total_latency_ms")
        if synthesis_event
        else 0.0,
        "events": [e.to_dict() for e in events],
    }


if __name__ == "__main__":
    result = run_disk_triage_improved("SV-10492")
    print("Offline Demonstration Result:", result)

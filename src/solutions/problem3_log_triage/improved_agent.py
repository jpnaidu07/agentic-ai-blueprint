"""
Problem 3: Distributed Log Triage - explicit offline tool demonstration.
Demonstrates semantic chunking, cross-service temporal correlation, local lexical post-mortem retrieval, and verified config fixes.
"""

from typing import Any, Dict

from src.agent.llm_client import LLMClient
from src.agent.orchestrator import AgentOrchestrator


def run_log_triage_improved(incident_id: str = "INC-LOG-992") -> Dict[str, Any]:
    """Runs the explicit offline ReAct demonstration for distributed log root cause analysis."""
    orchestrator = AgentOrchestrator(LLMClient(provider="mock"))
    prompt = (
        f"Perform root cause analysis on distributed incident {incident_id}. "
        "Correlate multi-service log timestamps across OME Core, Kafka, and PostgreSQL. "
        "Search the local demonstration index for matching historical post-mortems, calculate confidence score, "
        "and formulate an actionable config fix and test verification script."
    )
    events = list(orchestrator.run_stream(user_prompt=prompt, task_id=f"TASK-RCA-{incident_id}"))

    synthesis_event = next((e for e in reversed(events) if e.event_type == "SYNTHESIS"), None)
    tool_events = [e for e in events if e.event_type == "ACTION_DISPATCHED"]

    succeeded = {
        e.data["tool"] for e in events if e.event_type == "OBSERVATION" and e.data["success"]
    }
    return {
        "mode": "OFFLINE_DEMO",
        "incident_id": incident_id,
        "tools_called": len(tool_events),
        "tools_invoked": [e.data.get("tool") for e in tool_events],
        "cross_service_correlated": "correlate_logs" in succeeded,
        "historical_kb_matched": "search_incident_kb" in succeeded,
        "token_usage_estimated": len(prompt)
        // 4,  # Prompt-only approximation, not measured billing
        "final_synthesis": synthesis_event.data.get("response") if synthesis_event else "",
        "total_latency_ms": synthesis_event.data.get("total_latency_ms")
        if synthesis_event
        else 0.0,
        "events": [e.to_dict() for e in events],
    }


if __name__ == "__main__":
    result = run_log_triage_improved("INC-LOG-992")
    print("Offline Demonstration Log Triage Result:", result)

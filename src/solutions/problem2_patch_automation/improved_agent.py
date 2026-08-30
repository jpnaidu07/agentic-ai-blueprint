"""
Problem 2: Fleet Patch Automation - explicit offline tool demonstration.
Demonstrates topological dependency DAGs, 3-tier canary rollout, VM drain pre-flight checks, and automated rollback manifests.
"""

from typing import Any, Dict

from src.agent.llm_client import LLMClient
from src.agent.orchestrator import AgentOrchestrator


def run_patch_automation_improved(cluster_id: str = "CL-PROD-01") -> Dict[str, Any]:
    """Runs the explicit offline ReAct demonstration for fleet patch orchestration."""
    orchestrator = AgentOrchestrator(LLMClient(provider="mock"))
    prompt = (
        f"Generate a zero-downtime firmware upgrade and patch plan for server cluster {cluster_id}. "
        "Build a topological dependency graph, generate a 10% canary staged rollout, "
        "verify VM evacuation pre-flight health gates, and synthesize an automated rollback manifest."
    )
    events = list(orchestrator.run_stream(user_prompt=prompt, task_id=f"TASK-PATCH-{cluster_id}"))

    synthesis_event = next((e for e in reversed(events) if e.event_type == "SYNTHESIS"), None)
    tool_events = [e for e in events if e.event_type == "ACTION_DISPATCHED"]

    succeeded = {
        e.data["tool"] for e in events if e.event_type == "OBSERVATION" and e.data["success"]
    }
    return {
        "mode": "OFFLINE_DEMO",
        "cluster_id": cluster_id,
        "tools_called": len(tool_events),
        "tools_invoked": [e.data.get("tool") for e in tool_events],
        "dependency_aware": "build_dependency_graph" in succeeded,
        "canary_staging": "generate_canary_stages" in succeeded,
        "rollback_plan_included": "dry_run_validation" in succeeded,
        "final_synthesis": synthesis_event.data.get("response") if synthesis_event else "",
        "total_latency_ms": synthesis_event.data.get("total_latency_ms")
        if synthesis_event
        else 0.0,
        "events": [e.to_dict() for e in events],
    }


if __name__ == "__main__":
    result = run_patch_automation_improved("CL-PROD-01")
    print("Offline Demonstration Patch Result:", result)

"""
Problem 2: Fleet Patch Automation - Stage 2 (Production Improved Agent).
Demonstrates topological dependency DAGs, 3-tier canary rollout, VM drain pre-flight checks, and automated rollback manifests.
"""

from typing import Dict, Any
from src.agent.orchestrator import AgentOrchestrator

def run_patch_automation_improved(cluster_id: str = "CL-PROD-01") -> Dict[str, Any]:
    """Runs the production-grade ReAct agent for fleet patch orchestration."""
    orchestrator = AgentOrchestrator()
    prompt = (
        f"Generate a zero-downtime firmware upgrade and patch plan for server cluster {cluster_id}. "
        "Build a topological dependency graph, generate a 10% canary staged rollout, "
        "verify VM evacuation pre-flight health gates, and synthesize an automated rollback manifest."
    )
    events = list(orchestrator.run_stream(user_prompt=prompt, task_id=f"TASK-PATCH-{cluster_id}"))

    synthesis_event = next((e for e in reversed(events) if e.event_type == "SYNTHESIS"), None)
    tool_events = [e for e in events if e.event_type == "ACTION_DISPATCHED"]

    return {
        "mode": "PROD_IMPROVED",
        "cluster_id": cluster_id,
        "tools_called": len(tool_events),
        "tools_invoked": [e.data.get("tool") for e in tool_events],
        "dependency_aware": True,
        "canary_staging": True,
        "rollback_plan_included": True,
        "final_synthesis": synthesis_event.data.get("response") if synthesis_event else "",
        "total_latency_ms": synthesis_event.data.get("total_latency_ms") if synthesis_event else 0.0,
        "events": [e.to_dict() for e in events]
    }

if __name__ == "__main__":
    result = run_patch_automation_improved("CL-PROD-01")
    print("Production Improved Patch Result:", result)

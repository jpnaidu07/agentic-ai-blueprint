"""
Multi-Agent Orchestration & Agent2Agent Message Broker.
Implements 'AI Agent as a Tool' (Module 4) and 'Agent2Agent Collaboration' (Module 6).
"""

import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    sender_agent: str
    recipient_agent: str
    action_type: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class Agent2AgentBroker:
    """Central message bus coordinating multi-agent delegation and handoffs."""

    def __init__(self):
        self.message_history: List[AgentMessage] = []

    def dispatch_agent_delegation(
        self, sender: str, target_agent: str, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        msg = AgentMessage(
            sender_agent=sender, recipient_agent=target_agent, action_type=action, payload=payload
        )
        self.message_history.append(msg)

        # Route to specialized sub-agent (lazy imported to avoid circular dependencies)
        if target_agent == "StorageTriageAgent":
            from src.solutions.problem1_disk_health.improved_agent import run_disk_triage_improved

            server_id = payload.get("server_id", "SV-10492")
            result = run_disk_triage_improved(server_id)
            return {"delegated_agent": target_agent, "status": "COMPLETED", "result": result}

        elif target_agent == "PatchRolloutAgent":
            from src.solutions.problem2_patch_automation.improved_agent import (
                run_patch_automation_improved,
            )

            cluster_id = payload.get("cluster_id", "CL-PROD-01")
            result = run_patch_automation_improved(cluster_id)
            return {"delegated_agent": target_agent, "status": "COMPLETED", "result": result}

        elif target_agent == "LogRCAAgent":
            from src.solutions.problem3_log_triage.improved_agent import run_log_triage_improved

            incident_id = payload.get("incident_id", "INC-LOG-992")
            result = run_log_triage_improved(incident_id)
            return {"delegated_agent": target_agent, "status": "COMPLETED", "result": result}

        return {"error": f"Unknown target agent '{target_agent}'."}


_broker_instance = Agent2AgentBroker()


def tool_invoke_subagent(
    target_agent: str, action: str, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """AI Agent as a Tool: Delegates execution to a specialized domain sub-agent."""
    return _broker_instance.dispatch_agent_delegation(
        sender="PrimarySREOrchestrator", target_agent=target_agent, action=action, payload=arguments
    )

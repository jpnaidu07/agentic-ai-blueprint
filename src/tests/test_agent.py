"""
Unit Tests for Agent Core Modules (LLM Client, Memory, Guardrails, Planner, Tools, Vector Store).
"""

import pytest
import os
from src.agent.llm_client import LLMClient
from src.agent.memory import WorkingMemory, EpisodicMemory, StructuredAuditMemory
from src.agent.guardrails import AgentGuardrails
from src.agent.planner import TaskPlanner
from src.rag.vector_store import get_vector_store
from src.connectors.mock_ticketing_api import get_ticketing_service, ServiceTicketRequest
from src.tools.mcp_server import MCPServer

def test_guardrails_sanitizer():
    raw_prompt = "Server SV-10492 api_key='sk-1234567890abcdef1234567890abcdef1234567890abcdef' password='admin'"
    sanitized = AgentGuardrails.sanitize_input(raw_prompt)
    assert "[REDACTED_SECRET]" in sanitized or "[REDACTED_TOKEN]" in sanitized
    assert "sk-1234567890" not in sanitized

def test_guardrails_command_blocker():
    res_safe = AgentGuardrails.validate_command_safety("racadm get bios.sysinformation")
    assert res_safe.is_safe is True

    res_dangerous = AgentGuardrails.validate_command_safety("rm -rf /var/log/dell")
    assert res_dangerous.is_safe is False
    assert "Dangerous command pattern detected" in res_dangerous.violation_reason

def test_working_memory():
    wm = WorkingMemory()
    wm.add_thought("Checking disk SMART status")
    wm.add_action("redfish_query_storage", {"server_id": "SV-10492"})
    wm.add_observation({"health": "Critical"})

    trace = wm.get_trace()
    assert len(trace) == 3
    assert trace[0]["type"] == "THOUGHT"
    assert trace[1]["type"] == "ACTION"
    assert trace[2]["type"] == "OBSERVATION"

def test_episodic_memory():
    em = EpisodicMemory(max_messages=4)
    for i in range(6):
        em.add_message("user", f"message {i}")
    msgs = em.get_messages()
    assert len(msgs) == 4
    assert msgs[-1]["content"] == "message 5"

def test_structured_audit_sqlite(tmp_path):
    db_file = str(tmp_path / "test_audit.sqlite")
    audit = StructuredAuditMemory(db_file)
    audit.log_execution("TASK-T1", "Prompt", {"step": 1}, "Done", "SUCCESS", 15.2)
    audit.record_idempotency("IDEM-123", "SV-10492", "TICKET_CREATE", {"ticket_id": "INC-100"})

    cached = audit.get_idempotency_record("IDEM-123")
    assert cached is not None
    assert cached["ticket_id"] == "INC-100"

def test_vector_store_retrieval():
    store = get_vector_store()
    results = store.search("PERC H740P disk replacement hot swap", top_k=1)
    assert len(results) >= 1
    assert results[0]["id"] == "KB-8821"

def test_idempotent_ticketing():
    service = get_ticketing_service()
    req = ServiceTicketRequest(
        server_id="SV-TEST-01",
        component="Drive 0:1:0",
        priority="CRITICAL",
        idempotency_key="UNIQUE-TEST-TOKEN-999"
    )
    resp1 = service.create_ticket(req)
    assert resp1.idempotent_cached is False

    resp2 = service.create_ticket(req)
    assert resp2.idempotent_cached is True
    assert resp1.ticket_id == resp2.ticket_id

def test_mcp_server():
    tools = MCPServer.list_tools()
    assert len(tools) >= 5
    tool_names = [t["name"] for t in tools]
    assert "redfish_query_storage" in tool_names

    res = MCPServer.call_tool("redfish_query_storage", {"server_id": "SV-10492"})
    assert "drives" in res
    assert res["critical_drives_count"] >= 1

"""
Unit Tests for Agent Core Modules (LLM Client, Memory, Guardrails, Planner, Tools, Vector Store).
"""

import os

from src.agent.guardrails import AgentGuardrails
from src.agent.memory import EpisodicMemory, StructuredAuditMemory, WorkingMemory
from src.connectors.mock_ticketing_api import ServiceTicketRequest, get_ticketing_service
from src.rag.vector_store import get_vector_store
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
        idempotency_key="UNIQUE-TEST-TOKEN-999",
    )
    resp1 = service.create_ticket(req)
    assert resp1.idempotent_cached is False

    resp2 = service.create_ticket(req)
    assert resp2.idempotent_cached is True
    assert resp1.ticket_id == resp2.ticket_id


def test_mcp_server():
    tools = MCPServer.list_tools()
    assert len(tools) >= 6
    tool_names = [t["name"] for t in tools]
    assert "redfish_query_storage" in tool_names
    assert "invoke_subagent" in tool_names

    res = MCPServer.call_tool("redfish_query_storage", {"server_id": "SV-10492"})
    assert "drives" in res
    assert res["critical_drives_count"] >= 1


def test_file_storage_memory(tmp_path):
    from src.agent.memory import FileStorageMemory

    storage = FileStorageMemory(base_dir=str(tmp_path))
    manifest_path = storage.save_manifest("test-manifest-01", {"cluster": "CL-PROD-01", "stage": 1})
    assert os.path.exists(manifest_path)

    loaded = storage.load_manifest("test-manifest-01")
    assert loaded["cluster"] == "CL-PROD-01"


def test_agent_as_a_tool_delegation():
    from src.agent.agent2agent import tool_invoke_subagent

    delegated_res = tool_invoke_subagent(
        target_agent="StorageTriageAgent", action="triage", arguments={"server_id": "SV-10492"}
    )
    assert delegated_res["status"] == "COMPLETED"
    assert "INC-" in delegated_res["result"]["final_synthesis"]


def test_slack_discord_connector():
    from src.connectors.slack_discord_connector import SlackCommandRequest, SlackDiscordConnector

    req = SlackCommandRequest(
        command="/triage", text="SV-10492", user_name="oncall_sre", channel_id="C99999"
    )
    slack_resp = SlackDiscordConnector.handle_slack_slash_command(req)
    assert "blocks" in slack_resp
    assert "Agentic AI Execution Result" in slack_resp["text"]

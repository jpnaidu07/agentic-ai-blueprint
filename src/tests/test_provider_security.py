import json

import httpx
import pytest

from src.agent.llm_client import LLMClient, LLMError, ModelConfig
from src.agent.memory import FileStorageMemory
from src.agent.orchestrator import AgentOrchestrator
from src.tools.mcp_server import MCPServer


def test_provider_error_never_returns_mock():
    client = LLMClient(
        config=ModelConfig(model="test-model", api_key="test-only", retries=0),
        transport=httpx.MockTransport(lambda _: httpx.Response(503)),
    )
    with pytest.raises(LLMError, match="no simulated"):
        client.chat([{"role": "user", "content": "hello"}])


def test_missing_credentials_fail_closed(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY"):
        LLMClient(provider="openai", model="test-model")


@pytest.mark.parametrize(
    "provider,base",
    [
        ("openai", "https://api.openai.com/v1"),
        ("azure", "https://example.openai.azure.com/openai/v1"),
        ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
        ("anthropic", "https://api.anthropic.com/v1"),
        ("ollama", "http://localhost:11434/v1"),
        ("openai-compatible", "https://example.com/v1"),
    ],
)
def test_provider_request_contract(provider, base):
    def respond(request):
        assert str(request.url) == base + "/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == "configured-model"
        assert body["tools"][0]["function"]["name"] == "lookup"
        assert body["top_p"] == 0.8
        assert (
            "max_completion_tokens" in body
            if provider in {"openai", "azure"}
            else "max_tokens" in body
        )
        return httpx.Response(
            200,
            json={
                "model": "configured-model",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"ok":true}', "tool_calls": []},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    config = ModelConfig(
        provider=provider,
        model="configured-model",
        base_url=base,
        api_key="test-only",
        top_p=0.8,
        tool_calling=True,
        structured_output=True,
    )
    result = LLMClient(config=config, transport=httpx.MockTransport(respond)).chat(
        [{"role": "user", "content": "hello"}],
        tools=[
            {"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}
        ],
        output_schema=None
        if provider == "anthropic"
        else {
            "type": "object",
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}},
        },
    )
    assert result.usage["completion_tokens"] == 4 and not result.simulated


def test_refusal_and_invalid_schema_are_errors():
    for choice in [
        {"finish_reason": "length", "message": {"content": "partial"}},
        {"message": {"refusal": "refused"}},
        {"message": {"content": '{"wrong":1}'}},
    ]:
        config = ModelConfig(model="test", api_key="test-only", structured_output=True)
        client = LLMClient(
            config=config,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"choices": [choice]})
            ),
        )
        with pytest.raises(LLMError):
            client.chat(
                [{"role": "user", "content": "hello"}],
                output_schema={"type": "object", "required": ["correct"]},
            )


@pytest.mark.parametrize("identifier", ["../escape", "..\\escape", "C:\\escape", "a/b", "a:b", ""])
def test_file_memory_path_traversal(tmp_path, identifier):
    memory = FileStorageMemory(str(tmp_path))
    for call, args in [
        (memory.save_manifest, ({},)),
        (memory.load_manifest, ()),
        (memory.save_report, ("body",)),
    ]:
        with pytest.raises(ValueError):
            call(identifier, *args)


def test_tools_reject_missing_extra_and_wrong_type_arguments():
    for args in [
        {},
        {"server_id": None},
        {"server_id": 3},
        {"server_id": "SV-10492", "shell": "unsafe"},
    ]:
        assert "error" in MCPServer.call_tool("redfish_query_storage", args)
    assert "error" in MCPServer.call_tool(
        "generate_canary_stages", {"cluster_id": "CL-PROD-01", "canary_percent": 101}
    )


def test_orchestrator_redacts_audit_prompt(tmp_path):
    import sqlite3

    db = tmp_path / "audit.sqlite"
    orchestrator = AgentOrchestrator(LLMClient(provider="mock"), str(db))
    list(
        orchestrator.run_stream(
            "disk triage SV-10492 password=private-value", task_id="secret-test"
        )
    )
    with sqlite3.connect(db) as conn:
        assert (
            "private-value" not in conn.execute("SELECT user_prompt FROM executions").fetchone()[0]
        )

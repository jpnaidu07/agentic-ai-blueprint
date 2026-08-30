"""MCP-shaped local tool catalog for the offline infrastructure demonstrations.

This validates discovery/call contracts but does not implement an MCP transport.
A production MCP server remains a design option, not a claimed feature.
"""

from typing import Any, Dict, List

from jsonschema import ValidationError, validate

from src.agent.agent2agent import tool_invoke_subagent
from src.tools.disk_tools import (
    tool_rag_search_runbook,
    tool_redfish_query_storage,
    tool_submit_service_ticket,
)
from src.tools.log_tools import (
    tool_correlate_logs,
    tool_search_incident_kb,
    tool_synthesize_rca_report,
)
from src.tools.patch_tools import (
    tool_build_dependency_graph,
    tool_dry_run_validation,
    tool_generate_canary_stages,
)

MCP_TOOLS_MANIFEST = [
    {
        "name": "redfish_query_storage",
        "description": "Queries Dell Redfish storage API for drive health and SMART telemetry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "server_id": {"type": "string", "description": "Target server ID (e.g. SV-10492)"}
            },
            "required": ["server_id"],
        },
    },
    {
        "name": "rag_search_runbook",
        "description": "Searches Dell hardware maintenance runbooks in local vector store.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "submit_service_ticket",
        "description": "Submits an automated service ticket with SHA-256 idempotency key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "server_id": {"type": "string"},
                "component": {"type": "string"},
                "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                "runbook_id": {"type": "string"},
            },
            "required": ["server_id", "component", "priority"],
        },
    },
    {
        "name": "build_dependency_graph",
        "description": "Calculates topological upgrade sequence across chassis and compute sleds.",
        "input_schema": {
            "type": "object",
            "properties": {"cluster_id": {"type": "string"}},
            "required": ["cluster_id"],
        },
    },
    {
        "name": "correlate_logs",
        "description": "Correlates multi-service error logs and aligns timeline offsets.",
        "input_schema": {
            "type": "object",
            "properties": {"incident_id": {"type": "string"}},
            "required": ["incident_id"],
        },
    },
    {
        "name": "invoke_subagent",
        "description": "AI Agent as a Tool: Delegates execution to a specialized domain sub-agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_agent": {
                    "type": "string",
                    "enum": ["StorageTriageAgent", "PatchRolloutAgent", "LogRCAAgent"],
                },
                "action": {"type": "string"},
                "arguments": {"type": "object"},
            },
            "required": ["target_agent", "action"],
        },
    },
]


TOOL_HANDLERS = {
    "redfish_query_storage": lambda args: tool_redfish_query_storage(args.get("server_id", "")),
    "rag_search_runbook": lambda args: tool_rag_search_runbook(args.get("query", "")),
    "submit_service_ticket": lambda args: tool_submit_service_ticket(
        server_id=args.get("server_id", ""),
        component=args.get("component", ""),
        priority=args.get("priority", "CRITICAL"),
        runbook_id=args.get("runbook_id"),
    ),
    "build_dependency_graph": lambda args: tool_build_dependency_graph(args.get("cluster_id", "")),
    "generate_canary_stages": lambda args: tool_generate_canary_stages(
        args.get("cluster_id", ""), args.get("canary_percent", 10)
    ),
    "dry_run_validation": lambda args: tool_dry_run_validation(args.get("cluster_id", "")),
    "correlate_logs": lambda args: tool_correlate_logs(args.get("incident_id", "")),
    "search_incident_kb": lambda args: tool_search_incident_kb(args.get("query", "")),
    "synthesize_rca_report": lambda args: tool_synthesize_rca_report(args.get("incident_id", "")),
    "invoke_subagent": lambda args: tool_invoke_subagent(
        target_agent=args.get("target_agent", "StorageTriageAgent"),
        action=args.get("action", "triage"),
        arguments=args.get("arguments", {}),
    ),
}


for name, field_name in [
    ("generate_canary_stages", "cluster_id"),
    ("dry_run_validation", "cluster_id"),
    ("search_incident_kb", "query"),
    ("synthesize_rca_report", "incident_id"),
]:
    MCP_TOOLS_MANIFEST.append(
        {
            "name": name,
            "description": f"Offline demonstration: {name}",
            "input_schema": {
                "type": "object",
                "properties": {field_name: {"type": "string", "minLength": 1}},
                "required": [field_name],
            },
        }
    )
for item in MCP_TOOLS_MANIFEST:
    item["input_schema"]["additionalProperties"] = False
    item.update(
        {
            "output_schema": {"type": "object"},
            "authentication": "local process or authenticated demo API",
            "authorization": "synthetic fixture resources only",
            "timeout_seconds": 30,
            "retry_policy": "none; retry only explicitly idempotent operations",
            "errors": "error object",
        }
    )
    for prop in item["input_schema"]["properties"].values():
        if prop.get("type") == "string":
            prop.update({"minLength": 1, "maxLength": 2000})
    if item["name"] == "generate_canary_stages":
        item["input_schema"]["properties"]["canary_percent"] = {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
        }


class MCPServer:
    @staticmethod
    def list_tools() -> List[Dict[str, Any]]:
        return MCP_TOOLS_MANIFEST

    @staticmethod
    def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {"error": f"Tool '{tool_name}' not registered in MCP catalog."}
        try:
            schema = next(
                item["input_schema"] for item in MCP_TOOLS_MANIFEST if item["name"] == tool_name
            )
            validate(arguments, schema)
            return handler(arguments)
        except ValidationError:
            return {"error": "Tool arguments do not match its registered input schema"}
        except Exception:
            return {"error": "Tool execution failed"}

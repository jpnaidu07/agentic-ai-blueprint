"""
Model Context Protocol (MCP) JSON-RPC 2.0 Server Interface.
Allows standard AI agents (e.g. Claude Desktop, Cursor, Custom Agents) to discover and call enterprise infrastructure tools.
"""

from typing import Dict, Any, List
from pydantic import BaseModel
from src.tools.disk_tools import tool_redfish_query_storage, tool_rag_search_runbook, tool_submit_service_ticket
from src.tools.patch_tools import tool_build_dependency_graph, tool_generate_canary_stages, tool_dry_run_validation
from src.tools.log_tools import tool_correlate_logs, tool_search_incident_kb, tool_synthesize_rca_report

MCP_TOOLS_MANIFEST = [
    {
        "name": "redfish_query_storage",
        "description": "Queries Dell Redfish storage API for drive health and SMART telemetry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "server_id": {"type": "string", "description": "Target server ID (e.g. SV-10492)"}
            },
            "required": ["server_id"]
        }
    },
    {
        "name": "rag_search_runbook",
        "description": "Searches Dell hardware maintenance runbooks in local vector store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
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
                "runbook_id": {"type": "string"}
            },
            "required": ["server_id", "component", "priority"]
        }
    },
    {
        "name": "build_dependency_graph",
        "description": "Calculates topological upgrade sequence across chassis and compute sleds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string"}
            },
            "required": ["cluster_id"]
        }
    },
    {
        "name": "correlate_logs",
        "description": "Correlates multi-service error logs and aligns timeline offsets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"}
            },
            "required": ["incident_id"]
        }
    }
]

TOOL_HANDLERS = {
    "redfish_query_storage": lambda args: tool_redfish_query_storage(args.get("server_id", "")),
    "rag_search_runbook": lambda args: tool_rag_search_runbook(args.get("query", "")),
    "submit_service_ticket": lambda args: tool_submit_service_ticket(
        server_id=args.get("server_id", ""),
        component=args.get("component", ""),
        priority=args.get("priority", "CRITICAL"),
        runbook_id=args.get("runbook_id")
    ),
    "build_dependency_graph": lambda args: tool_build_dependency_graph(args.get("cluster_id", "")),
    "generate_canary_stages": lambda args: tool_generate_canary_stages(args.get("cluster_id", "")),
    "dry_run_validation": lambda args: tool_dry_run_validation(args.get("cluster_id", "")),
    "correlate_logs": lambda args: tool_correlate_logs(args.get("incident_id", "")),
    "search_incident_kb": lambda args: tool_search_incident_kb(args.get("query", "")),
    "synthesize_rca_report": lambda args: tool_synthesize_rca_report(args.get("incident_id", ""))
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
            return handler(arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

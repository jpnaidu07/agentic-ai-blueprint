"""
Storage Telemetry and Disk SMART Diagnostic Tools.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from src.connectors.mock_ome_api import MockRedfishClient
from src.connectors.mock_ticketing_api import ServiceTicketRequest, get_ticketing_service
from src.rag.vector_store import get_vector_store


class RedfishStorageQueryArgs(BaseModel):
    server_id: str = Field(description="Target server ID (e.g. SV-10492)")


class RAGRunbookQueryArgs(BaseModel):
    query: str = Field(description="Search terms for hardware runbooks")


class SubmitTicketArgs(BaseModel):
    server_id: str
    component: str
    priority: str
    runbook_id: Optional[str] = None
    idempotency_key: Optional[str] = None


def tool_redfish_query_storage(server_id: str) -> Dict[str, Any]:
    """Queries Redfish API for server storage components and SMART telemetry."""
    storage_data = MockRedfishClient.get_server_storage(server_id)
    if not storage_data:
        return {"error": f"Server {server_id} not found in Redfish inventory."}

    # Identify degraded or predictive failure drives
    critical_drives = []
    for drive in storage_data.get("drives", []):
        if drive["health_status"] == "Critical" or drive["reallocated_sector_count"] > 50:
            critical_drives.append(drive)

    return {
        "server_id": server_id,
        "model": storage_data["model"],
        "total_drives": len(storage_data.get("drives", [])),
        "critical_drives_count": len(critical_drives),
        "critical_drives": critical_drives,
        "drives": storage_data.get("drives", []),
    }


def tool_rag_search_runbook(query: str) -> Dict[str, Any]:
    """Retrieves verified Dell hardware runbooks from the local vector database."""
    store = get_vector_store()
    results = store.search(query, top_k=2)
    return {"query": query, "matched_runbooks": results}


def tool_submit_service_ticket(
    server_id: str,
    component: str,
    priority: str = "CRITICAL",
    runbook_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Submits an automated service ticket with SHA-256 idempotency verification."""
    ticketing_service = get_ticketing_service()
    req = ServiceTicketRequest(
        server_id=server_id,
        component=component,
        priority=priority,
        runbook_id=runbook_id,
        idempotency_key=idempotency_key,
    )
    resp = ticketing_service.create_ticket(req)
    return resp.model_dump()

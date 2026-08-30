"""
Mock Enterprise Ticketing Connector (ServiceNow / Jira API).
Enforces SHA-256 idempotency verification to prevent duplicate incident dispatches.
"""

import hashlib
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ServiceTicketRequest(BaseModel):
    server_id: str
    component: str
    priority: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    runbook_id: Optional[str] = None
    description: Optional[str] = None
    idempotency_key: Optional[str] = None

class ServiceTicketResponse(BaseModel):
    ticket_id: str
    server_id: str
    component: str
    status: str
    idempotent_cached: bool
    created_at: float

class MockTicketingService:
    def __init__(self):
        self.ticket_store: Dict[str, Dict[str, Any]] = {}
        self.idempotency_index: Dict[str, str] = {}  # idempotency_key -> ticket_id
        self._seq = 772910

    def create_ticket(self, request: ServiceTicketRequest) -> ServiceTicketResponse:
        # Calculate or use provided idempotency key
        hour_window = int(time.time() // 3600)
        idem_key = request.idempotency_key or hashlib.sha256(
            f"{request.server_id}:{request.component}:{request.priority}:{hour_window}".encode()
        ).hexdigest()

        # Check if already created
        if idem_key in self.idempotency_index:
            existing_ticket_id = self.idempotency_index[idem_key]
            existing = self.ticket_store[existing_ticket_id]
            return ServiceTicketResponse(
                ticket_id=existing_ticket_id,
                server_id=existing["server_id"],
                component=existing["component"],
                status=existing["status"],
                idempotent_cached=True,
                created_at=existing["created_at"]
            )

        # Create new ticket
        self._seq += 1
        ticket_id = f"INC-{self._seq}"
        ticket_record = {
            "ticket_id": ticket_id,
            "server_id": request.server_id,
            "component": request.component,
            "priority": request.priority,
            "runbook_id": request.runbook_id,
            "status": "DISPATCHED",
            "created_at": time.time()
        }
        self.ticket_store[ticket_id] = ticket_record
        self.idempotency_index[idem_key] = ticket_id

        return ServiceTicketResponse(
            ticket_id=ticket_id,
            server_id=request.server_id,
            component=request.component,
            status="DISPATCHED",
            idempotent_cached=False,
            created_at=ticket_record["created_at"]
        )

_ticketing_service_instance = MockTicketingService()

def get_ticketing_service() -> MockTicketingService:
    return _ticketing_service_instance

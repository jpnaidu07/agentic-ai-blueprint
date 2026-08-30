"""Local bearer-token identities with explicit role and tender scopes."""

import hashlib
import hmac
import json
import os
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    tender_ids: tuple[str, ...]

    def authorize(self, tender_id=None, roles=None):
        if roles and self.role not in roles:
            raise HTTPException(403, "Role is not authorized for this operation")
        if tender_id and "*" not in self.tender_ids and tender_id not in self.tender_ids:
            raise HTTPException(404, "Tender not found")


def authenticate(request: Request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or len(header) > 4096:
        raise HTTPException(
            401, "Bearer authentication required", headers={"WWW-Authenticate": "Bearer"}
        )
    digest = hashlib.sha256(header[7:].encode()).hexdigest()
    try:
        records = json.loads(os.getenv("AUTH_USERS", "[]"))
        for record in records:
            if hmac.compare_digest(digest, record["token_sha256"]):
                if record["role"] not in {"admin", "evaluator", "reviewer", "viewer"}:
                    break
                return Principal(record["user_id"], record["role"], tuple(record["tender_ids"]))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(503, "Authentication configuration is invalid") from None
    raise HTTPException(401, "Invalid bearer credentials", headers={"WWW-Authenticate": "Bearer"})

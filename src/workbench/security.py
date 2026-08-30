"""Local pairing, expiring sessions and credential-safe artifact boundaries."""

import re
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, Request

from src.workbench.contracts import Connection

SECRET = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,}|AIza[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)


class WorkbenchError(ValueError):
    """A message that is safe to show without request/provider contents."""


def no_secrets(text):
    if SECRET.search(text):
        raise WorkbenchError(
            "Credential-like text detected. Keep keys in the connection form, not briefs, specs or source files."
        )


def local_path(base: Path, relative: str):
    if not relative or "\\" in relative or ":" in relative or relative.startswith("/"):
        raise WorkbenchError("Use a relative workspace path.")
    parts = Path(relative).parts
    if any(p in {"..", ".git", ".env", ".workbench"} or p.startswith(".") for p in parts):
        raise WorkbenchError("Hidden, parent and credential paths are not accessible.")
    if any(
        p.endswith((".", " "))
        or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\..*)?", p)
        or any(ord(c) < 32 or c in '<>"|?*' for c in p)
        for p in parts
    ):
        raise WorkbenchError("Use portable filenames without device names or special characters.")
    target = base / relative
    if not target.resolve().is_relative_to(base.resolve()):
        raise WorkbenchError("Path escapes the selected workspace.")
    cursor = target
    while cursor != base:
        if cursor.is_symlink():
            raise WorkbenchError("Symbolic links are not allowed in workbench artifacts.")
        cursor = cursor.parent
    return target


@dataclass
class Session:
    expires: float
    csrf: str
    connection: Connection | None = None


class Sessions:
    def __init__(self, token):
        if len(token) < 24:
            raise ValueError("Workbench pairing token must have at least 24 characters")
        self.token = token
        self.items = {}
        self.lock = threading.RLock()
        self.attempts = []

    def pair(self, supplied):
        with self.lock:
            now = time.monotonic()
            self.attempts = [t for t in self.attempts if t > now - 60]
            if len(self.attempts) >= 10:
                raise HTTPException(429, "Too many pairing attempts. Wait one minute.")
            self.attempts.append(now)
            if not secrets.compare_digest(supplied, self.token):
                raise HTTPException(401, "Invalid local pairing token")
            self.items = {key: value for key, value in self.items.items() if value.expires > now}
            if len(self.items) >= 16:
                raise HTTPException(
                    429, "Too many local sessions. Restart the workbench to clear them."
                )
            key = secrets.token_urlsafe(32)
            session = Session(now + 8 * 3600, secrets.token_urlsafe(32))
            self.items[key] = session
            return key, session

    def require(self, request: Request):
        header = request.headers.get("Authorization", "")
        key = header[7:] if header.startswith("Bearer ") else ""
        with self.lock:
            session = self.items.get(key)
            if not session or session.expires < time.monotonic():
                self.items.pop(key, None)
                raise HTTPException(401, "Pair this browser with the local workbench.")
            if request.method not in {"GET", "HEAD"} and not secrets.compare_digest(
                request.headers.get("X-Workbench-CSRF", ""), session.csrf
            ):
                raise HTTPException(403, "Missing session CSRF token")
            return session

    def clear(self, request):
        with self.lock:
            header = request.headers.get("Authorization", "")
            self.items.pop(header[7:] if header.startswith("Bearer ") else "", None)

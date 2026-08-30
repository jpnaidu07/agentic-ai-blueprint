"""
Multi-Tier Memory Implementation:
1. Working Memory (Scratchpad for active ReAct trace)
2. Episodic Memory (Multi-turn conversation history buffer)
3. Structured Persistent Store (SQLite audit log & idempotency registry)
"""

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class WorkingMemory:
    """Ephemeral scratchpad for a single agent reasoning loop."""

    def __init__(self):
        self.scratchpad: List[Dict[str, Any]] = []
        self.extracted_entities: Dict[str, Any] = {}

    def add_thought(self, thought: str):
        self.scratchpad.append({"type": "THOUGHT", "content": thought, "timestamp": time.time()})

    def add_action(self, tool_name: str, tool_args: Dict[str, Any]):
        self.scratchpad.append(
            {"type": "ACTION", "tool": tool_name, "args": tool_args, "timestamp": time.time()}
        )

    def add_observation(self, observation: Any):
        self.scratchpad.append(
            {"type": "OBSERVATION", "content": observation, "timestamp": time.time()}
        )

    def get_trace(self) -> List[Dict[str, Any]]:
        return self.scratchpad

    def clear(self):
        self.scratchpad.clear()
        self.extracted_entities.clear()


class EpisodicMemory:
    """Multi-turn conversation buffer with token-aware sliding window."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_messages:
            self.history = self.history[-self.max_messages :]

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.history)


class StructuredAuditMemory:
    """SQLite-backed persistent audit log and idempotency registry."""

    def __init__(self, db_path: str = "agent_audit.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                task_id TEXT PRIMARY KEY,
                user_prompt TEXT,
                plan_json TEXT,
                final_response TEXT,
                status TEXT,
                latency_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tool_invocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                tool_name TEXT,
                args_json TEXT,
                result_json TEXT,
                success INTEGER,
                execution_time_ms REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                idempotency_key TEXT PRIMARY KEY,
                resource_id TEXT,
                action_type TEXT,
                response_payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def log_execution(
        self,
        task_id: str,
        prompt: str,
        plan: Dict[str, Any],
        response: str,
        status: str,
        latency_ms: float,
    ):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO executions (task_id, user_prompt, plan_json, final_response, status, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (task_id, prompt, json.dumps(plan), response, status, latency_ms),
        )
        conn.commit()
        conn.close()

    def log_tool_call(
        self,
        task_id: str,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        success: bool,
        exec_ms: float,
    ):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tool_invocations (task_id, tool_name, args_json, result_json, success, execution_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                task_id,
                tool_name,
                json.dumps(args),
                json.dumps(result, default=str),
                1 if success else 0,
                exec_ms,
            ),
        )
        conn.commit()
        conn.close()

    def get_idempotency_record(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT response_payload FROM idempotency_keys WHERE idempotency_key = ?",
            (idempotency_key,),
        )
        row = cur.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    def record_idempotency(
        self, idempotency_key: str, resource_id: str, action_type: str, response: Dict[str, Any]
    ):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO idempotency_keys (idempotency_key, resource_id, action_type, response_payload)
            VALUES (?, ?, ?, ?)
        """,
            (idempotency_key, resource_id, action_type, json.dumps(response)),
        )
        conn.commit()
        conn.close()


class FileStorageMemory:
    """File-system persistent memory for rollback manifests, patch plans, and generated artifacts."""

    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = base_dir
        self.manifest_dir = os.path.join(base_dir, "manifests")
        self.reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(self.manifest_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def save_manifest(self, manifest_id: str, data: Dict[str, Any]) -> str:
        path = self._safe_path(self.manifest_dir, manifest_id, ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load_manifest(self, manifest_id: str) -> Optional[Dict[str, Any]]:
        path = self._safe_path(self.manifest_dir, manifest_id, ".json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_report(self, report_id: str, content: str) -> str:
        path = self._safe_path(self.reports_dir, report_id, ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    @staticmethod
    def _safe_path(directory, identifier, suffix):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", identifier):
            raise ValueError("Invalid storage identifier")
        base = Path(directory).resolve()
        target = (base / (identifier + suffix)).resolve()
        if target.parent != base:
            raise ValueError("Storage path escapes its directory")
        return str(target)

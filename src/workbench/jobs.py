"""Single-writer jobs with durable progress; API keys never enter the job database."""

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from src.agent.llm_client import LLMError
from src.workbench.security import WorkbenchError, no_secrets


class Jobs:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.database = directory / "jobs.sqlite"
        self.lock = threading.RLock()
        self.active = None
        self.cancelled = threading.Event()
        with self.db() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, kind TEXT, solution TEXT, state TEXT, created TEXT, events TEXT, result TEXT)"
            )
            conn.execute("UPDATE jobs SET state='interrupted' WHERE state='running'")
            if "request" not in {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}:
                conn.execute("ALTER TABLE jobs ADD COLUMN request TEXT DEFAULT '{}'")

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.database, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get(self, job_id):
        with self.db() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise WorkbenchError("Job not found")
        value = dict(row)
        value["events"] = json.loads(value["events"])
        value["result"] = json.loads(value["result"])
        value["request"] = json.loads(value["request"] or "{}")
        return value

    def list(self):
        with self.db() as conn:
            ids = conn.execute("SELECT id FROM jobs ORDER BY created DESC LIMIT 50").fetchall()
        return [self.get(row[0]) for row in ids]

    def event(self, job_id, message, level="info"):
        no_secrets(message)
        with self.lock:
            events = self.get(job_id)["events"]
            events.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "message": message[:10000],
                    "level": level,
                }
            )
            with self.db() as conn:
                conn.execute(
                    "UPDATE jobs SET events=? WHERE id=?", (json.dumps(events[-250:]), job_id)
                )

    def check_cancelled(self):
        if self.cancelled.is_set():
            raise WorkbenchError(
                "Run cancelled. Finished artifacts remain; inspect status before resuming."
            )

    def start(self, kind, solution, function, request=None):
        with self.lock:
            if self.active:
                raise WorkbenchError(
                    "Another operation is running. Wait or cancel it before changing this workspace."
                )
            job_id = uuid.uuid4().hex
            self.active = job_id
            self.cancelled.clear()
            with self.db() as conn:
                conn.execute(
                    "INSERT INTO jobs (id,kind,solution,state,created,events,result,request) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        job_id,
                        kind,
                        solution,
                        "running",
                        datetime.now(timezone.utc).isoformat(),
                        "[]",
                        "{}",
                        json.dumps(request or {}),
                    ),
                )

        def work():
            state, result = "succeeded", {}
            try:
                result = function(job_id) or {}
                self.check_cancelled()
                no_secrets(json.dumps(result))
                if result.get("outcome") == "needs-attention":
                    state = "needs-attention"
                if result.get("exit_code", 0) != 0:
                    state = "failed"
            except (WorkbenchError, LLMError) as exc:
                state, result = (
                    "cancelled" if self.cancelled.is_set() else "blocked",
                    {"message": str(exc)},
                )
            except Exception:
                state, result = (
                    "failed",
                    {
                        "message": "Operation failed safely. Check model/schema compatibility, current specs and local prerequisites; no provider response or credentials were logged."
                    },
                )
            finally:
                with self.lock:
                    with self.db() as conn:
                        conn.execute(
                            "UPDATE jobs SET state=?,result=? WHERE id=?",
                            (state, json.dumps(result), job_id),
                        )
                    self.active = None

        threading.Thread(target=work, name=f"workbench-{job_id[:8]}", daemon=True).start()
        return self.get(job_id)

"""Transactional relational persistence, revision locks and append-only audit events."""

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    select,
)
from sqlalchemy.pool import StaticPool

metadata = MetaData()
tenders = Table(
    "tenders",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("payload", Text, nullable=False),
    Column("revision", Integer, nullable=False, default=0),
    Column("state", String(32), nullable=False, default="OPEN"),
)
bids = Table(
    "bids",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False, index=True),
    Column("bidder", String(200), nullable=False),
)
documents = Table(
    "documents",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False, index=True),
    Column("bid_id", ForeignKey("bids.id"), nullable=True),
    Column("scope", String(64), nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("payload", Text, nullable=False),
    Column("content", LargeBinary, nullable=False),
    UniqueConstraint("tender_id", "scope", "sha256"),
)
facts = Table(
    "facts",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False, index=True),
    Column("bid_id", ForeignKey("bids.id"), nullable=False),
    Column("criterion_id", String(40), nullable=False),
    Column("document_id", ForeignKey("documents.id"), nullable=False),
    Column("payload", Text, nullable=False),
    Column("reviewed_by", String(200), nullable=False),
)
evaluations = Table(
    "evaluations",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False, index=True),
    Column("revision", Integer, nullable=False),
    Column("input_digest", String(64), nullable=False),
    Column("idempotency_key", String(100), nullable=False),
    Column("payload", Text, nullable=False),
    Column("created_by", String(200), nullable=False),
    Column("state", String(32), nullable=False),
    UniqueConstraint("tender_id", "idempotency_key"),
)
decisions = Table(
    "decisions",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("evaluation_id", ForeignKey("evaluations.id"), nullable=False, unique=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False),
    Column("actor", String(200), nullable=False),
    Column("payload", Text, nullable=False),
)
audit = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tender_id", ForeignKey("tenders.id"), nullable=False, index=True),
    Column("actor", String(200), nullable=False),
    Column("kind", String(100), nullable=False),
    Column("payload", Text, nullable=False),
    Column("created_at", String(40), nullable=False),
    Column("previous_hash", String(64), nullable=False),
    Column("event_hash", String(64), nullable=False),
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Store:
    def __init__(self, url):
        options = {}
        if url.startswith("sqlite"):
            options["connect_args"] = {"check_same_thread": False, "timeout": 20}
            if ":memory:" in url:
                options["poolclass"] = StaticPool
        self.engine = create_engine(url, **options)
        if url.startswith("sqlite"):

            @event.listens_for(self.engine, "connect")
            def configure(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")

        metadata.create_all(self.engine)
        # SQLite protects audit/evidence against accidental SQL update/delete as well as API mutations.
        if url.startswith("sqlite"):
            with self.engine.begin() as conn:
                for table in ("audit_events", "facts", "decisions"):
                    for operation in ("UPDATE", "DELETE"):
                        conn.exec_driver_sql(
                            f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only table'); END"
                        )

    def log(self, conn, tender_id, actor, kind, payload):
        previous = (
            conn.execute(
                select(audit.c.event_hash)
                .where(audit.c.tender_id == tender_id)
                .order_by(audit.c.id.desc())
                .limit(1)
            ).scalar()
            or "0" * 64
        )
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {
            "tender_id": tender_id,
            "actor": actor,
            "kind": kind,
            "payload": payload,
            "created_at": timestamp,
            "previous_hash": previous,
        }
        conn.execute(
            audit.insert().values(**{**body, "payload": canonical(payload)}, event_hash=sha(body))
        )

    def lock(self, conn, tender_id, mutate=False):
        # An actual write serializes SQLite; PostgreSQL holds the row lock until commit.
        conn.execute(
            tenders.update()
            .where(tenders.c.id == tender_id)
            .values(revision=tenders.c.revision + (1 if mutate else 0))
        )
        row = conn.execute(select(tenders).where(tenders.c.id == tender_id)).mappings().first()
        if not row:
            from fastapi import HTTPException

            raise HTTPException(404, "Tender not found")
        return row

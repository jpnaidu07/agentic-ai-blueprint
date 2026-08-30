# Tender reference design decisions

## Boundaries and selected stack

The generic methodology is in `blueprint/`, `src/blueprint/` and `skills/`.
This solution's authoritative artifacts live here. Its reusable application code
is under `src/tender/`, exposed by `src/api/server.py`; the implementation mapping
is in `../implementation/README.md`. Keeping shared Python imports under one
package avoids duplicating source into generated solution folders.

FastAPI, Pydantic and SQLAlchemy support typed HTTP contracts, validation and
explicit database transactions. PostgreSQL is selected for concurrent local
development; SQLite uses the same query layer for tests and a single-process
demo. A same-origin HTML/CSS/JavaScript portal avoids an extra Node build and
authentication boundary. React/Angular and Spring Boot are valid alternatives
for organizations with those standards, but are not required by these capabilities.

The core containers are limited to 2 GiB each, rather than deploying a broker,
Redis, vector database and observability stack without a demonstrated need.
An optional local-AI container has an 8 GiB cap. These are configured limits, not
measured capacity guarantees on the target laptop.

## Data and memory

The actual relational tables are `tenders`, `bids`, `documents`, `facts`,
`evaluations`, `decisions` and `audit_events`. IDs and foreign keys retain tender,
bid, document and evaluation relationships. Versioned policy and report fields
are JSON serialized inside SQL rows. Original PDF bytes are database BLOBs for
transactional development persistence; no vector database owns these records.

Domain mapping: TenderAgency and tender metadata are fields in `tenders`;
TenderRequirement / eligibility / technical / commercial criteria are the frozen
policy; TenderSection is represented by page/chunk offsets; Bidder is the bid's
label; BidDocument is `documents`; Certification/ComplianceResult/Exception/Risk
are represented through criteria and reviewed observations; Evaluation/Score/
Recommendation/EvaluationEvidence are the immutable evaluation snapshot plus
referenced facts; AuditEvent and committee decisions have dedicated tables.
This reference does not pretend that all these concepts have independent
normalized tables. Bidder master data, richer non-numeric compliance and changing
criterion catalogs need migrations and additional domain models.

Working extraction state lives only in one request. Long-term knowledge is
page-aware document text; there is no conversational memory shared across tenders.
General-purpose file memory remains available for manifests with bounded IDs.
Production document volume should move to encrypted, versioned object storage
with a transactional outbox, malware quarantine and lifecycle policy.

## Document pipeline and evidence

Validate authorization, MIME, suffix and PDF signature before processing. The
ASGI body limit bounds memory before multipart spooling. Reject encrypted,
interactive, annotated, attachment-bearing and scanned-only PDFs explicitly.
Use pypdf's layout extraction and retain page boundaries, text offsets, original
SHA-256 and parser/scanner versions. Repeating identical content within a
tender/bid scope returns the same document ID without creating a new revision.

Fixed-size overlapping chunks within each page are a baseline, not full semantic
or table understanding. Complex tables, cross-page sections, OCR, DOCX and XLSX
require parser adapters. Compressed PDF streams can exhaust a process before a
post-extraction text limit is reached; production must use a separate parser
worker with CPU/memory/time limits. The local reference is not a safe public
arbitrary-PDF upload service.

The optional model step reads one selected page and the approved criteria. Prompt
`tender-extraction-v1` treats the page as untrusted data, returns a typed proposal
and cannot call tools. Schema validation, known-criterion validation and exact
quote matching precede an audit event. A human verifies value, units, meaning and
confidence before creating a fact. A valid quote alone does not prove a valid
numeric interpretation; the review note and reviewer identity make that boundary
explicit. Documents do not become instructions, and tool permissions do not come
from text filters.

## Retrieval and search

The runnable API provides lexical BM25 with tender and optional bid filtering
before ranking. Results return document, page, section, tender and bidder IDs.
The library accepts a supplied embedder and fuses lexical/semantic ranks using
reciprocal-rank fusion. No embedding provider, vector index or embedding cache is
silently activated. A production hybrid path should persist embeddings indexed
by document digest and model version, apply ACL filters in the vector query and
evaluate reranking. It remains an extension, not a claimed deployed feature.

Portfolio counts and participation filters query structured SQL. Scores and L1
come from deterministic evaluation snapshots. Search never converts unrestricted
natural-language text into SQL or invents an answer when no evidence is found.

## Deterministic policy and review

Criteria define category, numeric target, normalization and weight. Eligibility
uses `at_least` or `at_most`, has zero weight and gates ranking. Non-mandatory
weights must total exactly 100. Higher-is-better scores use `min(value / target, 1)`;
lower-is-better scores use `min(target / value, 1)`, with a zero value receiving
full points for noncommercial lower-is-better criteria. Commercial price must be
positive; its baseline is the lowest complete eligible bid. Currency and tax
comparability are committee responsibilities in this reference.

Use Decimal arithmetic, round criterion contributions to four decimals, and the
total to two. Equal rounded totals share a rank. No arbitrary identifier decides
a winning bidder. Missing facts or confidence below 0.8 produce NEEDS_REVIEW;
failed eligibility produces INELIGIBLE. Confidence is a review signal, not a
calibrated guarantee. Absence of a certificate must be explicitly evidenced,
not inferred from a failed lexical search.

Evaluation snapshots include frozen policy, fact revisions, evidence hashes,
producer/reviewer information, timestamp and scoring version. Every mutation
locks the tender row and advances its revision. Evaluations bind an idempotency
key to an input digest. A changed input with a reused key returns 409. Committee
review requires an independent user, the current revision and no unresolved bid.
Approval freezes this tender version; rejected evaluations remain retained and
can be superseded. No automatic procurement award or external notification exists.

## Workflow and recovery

Implemented state transitions are synchronous and transactional: OPEN -> evidence
revisions -> PENDING_REVIEW -> APPROVED or REJECTED. Invalid operations roll back.
Row locks serialize concurrent uploads, evaluations and decisions for a tender.
Duplicate documents and repeated identical evaluations are idempotent. There is
no unbounded agent loop or autonomous retry of mutations.

Durable distributed jobs, parallel agent graphs, cancellation, compensation,
event brokers and outbox workers are design extensions for long-running/OCR
work, not stub services advertised as complete. Add them only with explicit
state, timeout, retry and recovery contracts.

## Security, governance and operations

Local bearer identities have admin/evaluator/reviewer/viewer roles and tender ID
scopes. Documents inherit the tender ACL. Credentials are hashed in configuration;
tokens stay in browser memory. Authentication, role and scope checks precede
queries and model transfer. There is no CORS wildcard, unauthenticated tool API,
public Slack webhook or GET endpoint that runs a mutation.

All core writes log actor, timestamp, type and payload in a per-tender hash chain.
SQLite adds SQL triggers against fact, decision and audit updates/deletes.
Database administrators can still rewrite an entire database and its chain.
Production needs separate write-only audit privileges, external WORM anchoring,
retention controls and independent verification. PostgreSQL database-level
append-only permissions/triggers require deployment hardening beyond API controls.

Request logs contain generated request ID, route template, status and measured
duration; they exclude document bodies, tokens and query strings. Model proposal
audit records retain model/prompt versions, observed usage, latency and output in
the protected database. OpenTelemetry exporters, distributed trace correlation,
cost billing integration and load-tested SLOs remain deployment work.

Production gates: organizational identity/MFA, scoped administration, TLS,
encrypted databases/object storage, managed secrets/rotation, malware scanning,
isolated parsers, rate limiting, database migrations, backup/restore testing,
observability, approved retention/residency, model evaluations and procurement
legal review. No compliance certification is claimed.

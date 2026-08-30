# Validation report

Date: 2026-08-30
Environment: Windows x64, Python 3.12, Node.js 24, Codex in-app browser
Scope: local checkout before commit and push

## Guided workflow validation (version 0.3)

- Full suite: **65 passed** in 31.82 seconds; the same upstream TestClient
  deprecation warning remains.
- Ruff lint/format, 10/10 offline evaluations, and the 121-file repository
  schema/link/secret-pattern validator passed.
- New tests exercise partial spec creation/resumption, preservation of reviewed
  design edits, approval gates, all/next/task/skill/module selection, dependency
  expansion, transitive receipt invalidation, CLI completion/resumption and an
  eight-module tender graph with a database task.
- The installed CLI's government tender `guide` command was exercised. Five new
  or revised skills passed the Skill Creator validator.
- Plans explicitly report that no code/tests were executed. Coding-agent teaching
  and implementation is an instruction workflow, not a bundled autonomous model
  executor or an independently measured guarantee for arbitrary problems.
- Repaired literal escaped newlines in this report. Application UI/diagrams and
  provider code did not change in this follow-up, so their earlier results below
  are historical checks, not newly repeated browser/live-provider tests.

## Problems found and fixed

| Finding | Disposition |
|---|---|
| No use-case to capability/design/decomposition workflow | Added a strict generic compiler, schemas, review digest, dependency gates, receipts and reusable skills. |
| Hard-coded “50 scenario” accuracy and latency claims | Withdrawn. Removed the old result JSON/UI; the harness now computes 10 versioned golden checks and labels live quality/cost unmeasured. |
| Provider outage silently returned mock success | Removed `auto`. Models/keys are explicit; failures are bounded errors. Mock is explicit and forbidden for tender extraction. |
| Narrow hard-coded model support | Added configurable OpenAI, Azure, Gemini, Anthropic, Ollama and compatible endpoints, budgets, capability flags and same-provider fallback. Anthropic compatibility schema extraction is blocked. |
| Tools accepted missing/extra/wrong arguments and overstated MCP support | Added JSON Schema validation and operational metadata; relabeled as a local MCP-shaped catalog with no transport claim. |
| Unauthenticated APIs, wildcard CORS and GET work execution | Maintained APIs require identity/role/tender scope. Simulations are POST-only, authenticated and disabled by default. |
| Raw prompts in audit and path-traversable file IDs | Audit stores sanitized prompts; file/spec/evidence paths are bounded and resolved inside their roots. |
| Demo success flags ignored tool failures | Flags now derive from successful observations and use `OFFLINE_DEMO` mode. |
| No tender reference or human decision boundary | Added structured evidence, PDF ingestion, deterministic scoring, idempotent snapshots and independent stale-safe review. |
| Mandatory Ollama stack, public ports and no resource budget | Core app/PostgreSQL bind loopback and cap at 4 GiB; local Ollama is an 8 GiB opt-in profile. |
| Setup continued after errors and installed globally | Added fail-fast checks, venv/container paths, ignored unique identities and no silent host/model install. |
| Missing SVG and inaccurate aspirational docs | Added generated eight-module SVG plus eight Mermaid diagrams; removed stale personal/component docs and retained demos with accurate simulation labels. |

## Initial reference validation

- Ruff lint passed; Ruff formatting check passed.
- Pytest: **58 passed** in 8.05 seconds. One warning originates in FastAPI's TestClient compatibility import.
- Offline evaluation: **10/10** synthetic retrieval/scoring cases passed. No live model quality or cloud cost was measured.
- `pip-audit` found no known vulnerabilities in pinned runtime dependencies at scan time.
- JavaScript and PowerShell syntax checks passed.
- Root Compose YAML passed the official Compose Specification JSON Schema (static check).
- Mermaid 11 parsed all **8** `.mmd` diagrams in a browser without console errors.
- The generated SVG loaded with its accessible title/description and 53 text nodes; visual inspection found readable numbering, spacing and flow.
- The portal loaded with no console errors. Desktop visual inspection, unauthenticated state, evaluator login and empty portfolio states passed.
- Repository validator checks strict specs, generated schemas, JSON/YAML/SVG, tracked local links and high-confidence secret patterns.
- `git diff --check` passed before final review.

Tests also cover six provider request contracts through intercepted HTTP, missing
credentials, refusals and invalid schemas. API/security coverage includes tender
scope on every read, cross-bid evidence, exact quote/page checks, nonfinite values,
request/PDF limits, scanner fail-closed behavior, append-only SQLite triggers,
concurrent idempotency, stale evidence, role-change self-approval, unresolved
evidence, version freezing and audit-chain verification.

## Not established locally

- Docker is absent, so image build, Compose runtime, PostgreSQL, health checks and
  configured memory limits were not run locally. The prior
  [CI run](https://github.com/jpnaidu07/agentic-ai-blueprint/actions/runs/33316926101)
  passed; CI repeats the image build, startup and health check for each push.
- SQLite tests cannot prove PostgreSQL isolation, migrations, failover or recovery.
- No live model/embedding request, extraction quality, cost, billing, latency or
  provider residency policy was tested.
- No malware engine, OCR, DOCX/XLSX/image parser, parser sandbox, PDF fuzz campaign,
  load/soak test, backup/restore drill or external audit anchor was exercised.
- No full accessibility audit, external identity/MFA, TLS, encrypted storage, rate
  limiter, managed secret rotation, retention job or jurisdictional procurement review.
- Local tokens are broad development identities. PostgreSQL database-level
  append-only privileges/triggers are not implemented; an administrator can rewrite
  the database and hash chain.
- The in-process PDF parser remains exposed to decompression/parser resource attacks
  before post-extraction limits; production needs an isolated worker.
- The GitHub token pasted in chat was not written to the checkout or tool commands.
  It was exposed in chat and should be revoked regardless.

## Release decision

Suitable as a transparent **development reference and reusable spec template**
after final repository validation and CI. Blocked for real procurement/production
data until every applicable gate above has an owner, evidence and independent approval.

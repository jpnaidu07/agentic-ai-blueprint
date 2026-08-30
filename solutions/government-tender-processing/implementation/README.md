# Implementation map

The source package is shared under the repository's existing `src/` convention.
This folder holds solution-specific work packets and evidence, not copied source.

| Concern | Implemented source |
|---|---|
| Typed tender, criterion and evidence contracts; deterministic scoring | `src/tender/models.py` |
| SQL persistence, revision locks, audit hashes | `src/tender/store.py` |
| PDF parsing, page segmentation, BM25/hybrid extension | `src/tender/documents.py` |
| Identity and tender scope | `src/tender/security.py` |
| Upload, fact, evaluation, review, search, audit and extraction APIs | `src/tender/api.py` |
| Portal | `src/tender/ui/` |
| Provider abstraction | `src/agent/llm_client.py` |
| API host, body limits and request telemetry | `src/api/server.py` |
| Container entrypoint | `docker-compose.yml`, `infra/Dockerfile.backend` |
| Tests | `src/tests/test_tender.py`, `src/tests/test_provider_security.py` |

All paths above are relative to the repository root. Run commands from that root.
No local approval is bundled: users must review the three specs and their design
notes before recording their own approval. Existing reference source can be run
for synthetic-data exploration without claiming those production approvals exist.

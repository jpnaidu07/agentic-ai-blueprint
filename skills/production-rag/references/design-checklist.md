# Production RAG design checklist

Use this checklist to turn an approved retrieval capability into explicit, testable decisions. Mark irrelevant items as not applicable with a reason rather than inventing components.

## Ingestion contract

- Supported source types and maximum bytes/pages/records.
- Canonical document fields: tenant/resource/document/revision IDs, source hash, content type, page/section/offset, timestamps and ACL labels.
- Parser isolation, malware result, OCR/table handling and unsupported-format behavior.
- Chunking strategy per content class, tokenizer-aware limits and parent/child relationships.
- Idempotent add/update/delete, partial-failure recovery and document-to-index consistency.
- Embedding provider/model/version, dimensions, normalization, batch/rate limits and data residency.
- Persistent index schema, namespace, distance metric, backup, migration, re-embedding and rollback.

## Retrieval and generation contract

- Caller authorization and metadata filtering occur before candidates can cross the trust boundary.
- Query normalization/rewrite and history have bounded, versioned behavior.
- Lexical/dense candidate counts, fusion strategy, optional reranker and final context budget are explicit.
- No-evidence, low-score, conflicting-source and stale-index paths abstain visibly.
- Answer prompt distinguishes policy from untrusted evidence and requires stable source citations.
- Structured facts are quote/page checked. Transactional decisions come from authoritative services, not similarity.
- Streaming has cancellation, timeout, backpressure, terminal status and final-citation semantics.

## Evaluation and operations

- Versioned representative queries include easy, paraphrased, multi-document, negative and adversarial cases.
- Measure retrieval recall@k/precision@k and, when useful, MRR or nDCG.
- Separately measure citation correctness, groundedness/unsupported claims and abstention behavior.
- Record p50/p95 latency, index freshness, failure rates and observed provider usage/cost.
- Test cross-tenant isolation, deleted/replaced documents, embedding drift, malformed files, provider outage and prompt injection.
- Monitor ingestion lag and index/source reconciliation; support a tested rebuild without losing the source of truth.

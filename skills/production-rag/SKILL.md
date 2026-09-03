---
name: production-rag
description: Design and implement evidence-grounded RAG when a solution requires document ingestion, embeddings, persistent vector retrieval, cited LLM answers, and measured retrieval quality. Use the basic rag skill for lexical-only retrieval without an answer-generation pipeline.
---

# Production RAG engineering

Start from the approved capability and data boundary. Confirm that unstructured knowledge retrieval is required; use SQL or typed APIs for counts, workflow state, prices, rankings, and other authoritative transactions. Do not add a vector database merely because an LLM is present.

Design two independently retryable pipelines. Ingestion normalizes supported sources into versioned documents, parses unsafe formats in an isolated worker, creates structure-aware chunks with stable source/page/section offsets and ACL metadata, embeds with a versioned model, and idempotently upserts or removes a persistent index. Retrieval authorizes the resource scope before search, combines approved lexical and dense modes, optionally reranks, fits evidence into a bounded context, and generates an answer that cites the retrieved source identifiers or abstains.

Keep the embedding model, vector store, chunker, retriever, reranker and answer model behind typed interfaces. Record dimensions, distance metric, normalization, model/index versions and rebuild/migration behavior. Preserve the immutable source hash so an index entry can be traced to the exact document revision. Treat retrieved text, metadata and conversation history as untrusted data; none may change system rules, tool permissions or human approvals.

Choose `top_k`, overlap, score thresholds and context budgets from versioned evaluation cases rather than intuition. A similarity score is not calibrated answer confidence. Return retrieval scores separately from groundedness, citation verification and business confidence. Stream only when the API and UI preserve cancellation, final citations and error states. Bound and summarize history; never let prior turns bypass current authorization or source revision checks.

Read [the design checklist](references/design-checklist.md) when creating architecture or implementation evidence. When preparing an interview explanation, read [the interview story](references/interview-story.md) and keep its implementation/measurement limitations intact.

Completion requires executed ingestion, update/delete, retrieval, authorization, abstention and answer-grounding tests. Retain golden labels and observed recall/precision or ranking metrics, citation correctness, unsupported-answer rate, latency and actual model usage. Include cross-resource access, stale index, parser failure, provider failure, prompt injection and conflicting-source cases. Do not mark deployment complete when OCR, malware isolation, identity, encryption, retention, monitoring, index backup/rebuild or independent domain review is unresolved.

Run `agent-blueprint run <solution> production-rag` for matching approved work packages. Specifications retain domain decisions; this skill supplies the reusable engineering method. Source generation, passing agent-authored tests and an interview narrative are not independent production certification.

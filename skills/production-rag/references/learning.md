# Production RAG: a use-case lesson

## What it is and why it fits

Retrieval-augmented generation selects external knowledge at query time and puts that evidence into the LLM's input to produce a grounded answer. Retrieval does not update the answer model's weights. Ingestion prepares searchable knowledge; query processing retrieves and uses it.

For a tender example, "What warranty exclusions does bidder A list?" requires authorized passages from that bidder's current documents. "How many bids are approved?" requires SQL over approval records. "Approve bidder A" requires a separately authorized business action. RAG supports the first need and must not become the authority for the other two. Adapt these examples to the selected solution.

The existing tender reference returns cited excerpts for free-text fallback. That is a retrieval baseline, not evidence that a complete generative RAG pipeline already runs.

## Compare with "relearning"

Clarify whether relearning means fine-tuning, continued pretraining or full training. Fine-tuning updates weights using task examples; continued pretraining updates them on additional text; training from scratch builds a new model from a much larger training process. RAG supplies external evidence at inference time. These approaches can be combined.

| Approach | Prefer when | Limitation to explain |
|---|---|---|
| SQL or typed API | Exact counts, prices, state or rules | Does not interpret arbitrary document prose |
| Keyword/BM25 search | Exact clauses, identifiers, strong lexical overlap | May miss paraphrases; returns evidence, not necessarily an answer |
| Direct long-context prompt | A small, bounded set of documents fits | Repeated context cost and omission/distraction must be measured |
| RAG | Knowledge changes, corpora grow, provenance matters | Parsing, retrieval, index freshness and generation can each fail |
| Fine-tuning | Evaluated errors concern behavior, format or task patterns and suitable training data exists | Requires training/evaluation; weight updates do not replace current access checks and citations |
| Continued pretraining/full training | A justified model-development objective and sufficient data/compute | Substantial training, governance and evaluation scope; not a routine response to a new tender |

The tender design rationale is frequently changing evidence and traceability, not a claim that RAG is always cheaper or more accurate. Advantages include targeted context and source updates without answer-model retraining. Costs include indexing, storage, embedding calls, retrieval latency and ongoing evaluation. It still can generate unsupported claims.

## Trace both pipelines

**Ingestion:** upload → validate/isolate parser → extract text/table/OCR as supported → retain source hash/revision/page → chunk → attach ACL metadata → embed → versioned index upsert. Replaced or deleted documents must invalidate stale index entries. The original document remains the source of truth.

**Query:** authenticate → authorize tender/bidder scope → normalize query → retrieve lexical/dense candidates → optional rerank → fit context → generate → verify citations/grounding or abstain. Return stable document, revision and page identifiers. Reauthorize on every turn.

## Advanced concepts with reasons to use them

- **Structure-aware and parent-child chunking:** retrieve a short matching section, then add its parent context so exclusions and table headers are not lost. Compare against fixed chunks; extra context may dilute relevance and increase tokens.
- **Hybrid search and reciprocal-rank fusion:** merge lexical and dense candidate ranks to cover exact identifiers and paraphrases. Rank fusion avoids assuming their raw scores have the same scale; it still needs evaluation.
- **Reranking:** score query/passage pairs after initial retrieval to improve ordering. It adds latency and cannot recover evidence absent from the candidate set.
- **Index lifecycle:** record embedding model, dimensions, metric and chunking version. Changing the embedder may require re-embedding/rebuilding; test deletes and revision reconciliation.
- **Query rewriting and history:** resolving "what about its warranty?" can help retrieval, but history must remain bounded and cannot extend current access scope. Recheck stale citations.
- **Context and answer policy:** conflicting, missing or low-quality evidence should trigger an explicit response. Similarity is not calibrated factual confidence; measure unsupported answers separately.
- **Streaming:** useful for perceived response time, but requires terminal errors, cancellation and stable final citations. The current restricted preview relay lacks streaming/WebSockets; record the required extension instead of claiming it works.
- **Observability:** trace ingestion lag, retrieval candidates, index versions and model usage without logging sensitive document contents by default.

## A reproducible learning experiment

Use synthetic documents, never invented measured results:
1. Create bidder A revision 1 with "Warranty: 24 months" and a separate "Batteries excluded" clause. Create bidder B with "Warranty: 12 months, including batteries".
2. Label the passages for: "A warranty duration", "Does A cover battery replacement?", "Which bid includes batteries?", an unanswerable question about delivery, and an unauthorized bidder request.
3. First retrieve using lexical search. Then compare dense/hybrid only if an actual embedder/index is available. Keep documents, query set and scope constant.
4. Record retrieved document/revision/page IDs, expected IDs, recall@k, citation correctness, unsupported answers and observed latency. Label target thresholds as targets. Hold back additional paraphrases from configuration tuning.
5. Replace A's warranty with revision 2 and 18 months. Query again, delete it and query once more. Check current citations, removal behavior and visible abstention.
6. Introduce a provider outage and an instruction in the document to ignore permissions. Verify the defined failure path and unchanged access/approval boundaries.

Expected behavior is a hypothesis until checked. If the runner cannot access the embedder, vector store or provider, report the setup needed and mark semantic/live-generation quality unmeasured. Offline stub tests establish contracts only.

## Check understanding and explain the result

**Question:** Why did a larger answer model still miss A's battery exclusion?

**Answer rubric:** inspect extraction and chunk boundaries first; check authorization scope, candidate recall and context truncation; inspect generation only after verifying the relevant exception reached it. A reranker cannot recover a clause that was never retrieved.

**Question:** A new addendum arrives. Should we fine-tune?

**Answer rubric:** version and index the addendum, remove stale evidence, test fresh citations and access; evaluate fine-tuning separately for a demonstrated behavioral problem.

Interview practice: "The hardest challenge was ensuring each answer used the correct authorized revision. I compared a lexical baseline with [actually tested alternative], found [observed error], changed [implemented mechanism], and measured [real result]. Scoring stayed deterministic and approvals stayed with the reviewer." Preserve the brackets as questions to answer from evidence, not numbers to invent.

References: [AWS RAG versus fine-tuning](https://docs.aws.amazon.com/prescriptive-guidance/latest/retrieval-augmented-generation-options/rag-vs-fine-tuning.html), [RAG research paper](https://arxiv.org/abs/2005.11401).

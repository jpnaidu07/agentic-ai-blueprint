# Retrieval foundations and the RAG decision

**What:** Retrieval-augmented generation (RAG) retrieves external evidence at query time and supplies it to a language model to produce an answer. Retrieval alone returns matching passages; call it search if there is no answer-generation step. A chunk is a document segment, and an embedding represents text as a numeric vector for similarity search.

**Why:** Tender documents change and answers need traceable passages. Retrieval can select current, authorized evidence without changing the answer model's weights. "Relearning" could mean fine-tuning, continued pretraining or training from scratch; explain which is being considered.

**Alternatives:** SQL handles exact counts and workflow state. Keyword/BM25 search is an inexpensive baseline and can work well for exact terms. Putting a few documents directly in context can suit a small bounded corpus. Fine-tuning adjusts weights to learn behavior or task patterns; it does not itself provide current document citations or per-query access control. It may complement RAG. Training a model from scratch is generally a different data/compute undertaking.

**Benefits and costs:** RAG provides explicit evidence and index updates without answer-model retraining, but adds parsing, search, freshness and context costs. It cannot guarantee factual correctness. Lexical search can miss paraphrases; dense search can miss exact identifiers. Test both before introducing hybrid retrieval.

**Advanced:** Chunk boundaries can split a condition from its exception. Similarity scores are retrieval signals, not calibrated answer confidence. Revisions and authorization metadata must travel with every chunk.

**Practice:** Create two short synthetic bids and label passages answering exact-term and paraphrased questions. Compare keyword retrieval against a proposed or available embedding retriever. Add an unanswerable and an unauthorized question. Record retrieved IDs, expected IDs and observed results; do not invent dense-search results if no embedder is configured.

**Check:** A new addendum changes eligibility. Must the LLM be retrained? Rubric: ingest/reindex the revision, invalidate stale evidence and verify citations; change weights only for a demonstrated model-behavior need.

**Explain:** "We selected retrieval because knowledge changed and answers needed provenance; we kept exact business questions in SQL." For the full lifecycle and experiments, continue with the production-rag learning reference.

Reference: [AWS comparison of RAG and fine-tuning](https://docs.aws.amazon.com/prescriptive-guidance/latest/retrieval-augmented-generation-options/rag-vs-fine-tuning.html).

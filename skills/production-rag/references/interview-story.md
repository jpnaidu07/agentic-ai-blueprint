# Interview story: hardest LLM-agent design problem

## Short answer

The hardest problem was not calling the LLM. It was building a trustworthy evidence boundary around it. Tender documents are long, inconsistent and untrusted, while bidder counts, scores, rankings and approvals are transactional facts. A single “put everything in a vector database and ask the model” pipeline could retrieve another tender's data, mistake similarity for confidence, use stale evidence or let document instructions influence a procurement decision.

I separated ingestion, retrieval, deterministic policy and human decision-making. Documents receive hashes, revisions and page-aware chunks. Authorization is applied before retrieval. Business counts and ranking snapshots come from SQL, while document questions use evidence retrieval. Answers cite exact source metadata and abstain when evidence is missing; low-confidence or stale facts block ranking. Model output can propose facts but cannot accept evidence, change scoring rules or approve an evaluation. I added negative retrieval and prompt-injection cases, stale-revision checks, role separation and reproducible CI.

The result is a development reference where evidence and decisions are reconstructible and unsafe uncertainty is visible. The local suite and CI validate the implemented baseline. I would not claim the semantic production stack is finished: the persistent vector index, embedding-model evaluation, OCR/parser isolation and production identity controls remain explicit gates. That distinction—measured implementation versus planned architecture—was part of solving the problem.

## Follow-up structure

- **Situation:** confidential, heterogeneous bids; long PDFs; multiple roles; legally consequential decisions.
- **Task:** support useful discovery without allowing probabilistic retrieval or generation to become the authority.
- **Action:** split the two RAG pipelines; preserve provenance and revisions; enforce resource ACLs; keep SQL authoritative; add citations, abstention, deterministic scoring, independent approval and adversarial evaluations.
- **Result:** working evidence-grounded baseline with repeatable tests and visible limitations; advanced embedding/vector retrieval remains a separately testable work package.
- **Lesson:** production RAG quality comes from data contracts, authorization, retrieval evaluation and failure behavior more than from choosing a fashionable framework or model.

Do not replace “development reference” with “production platform,” invent accuracy/latency improvements, or claim that a persistent vector database is deployed until corresponding evidence exists.

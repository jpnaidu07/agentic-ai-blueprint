# Model and retrieval evaluation

**What:** An evaluation measures behavior on representative tasks against labels or a scoring rubric. It distinguishes retrieval quality, answer groundedness, business correctness and runtime performance.

**Why:** A successful model connection does not show that tender questions retrieve the correct exception or cite the current document. Measure the failure that matters to the user.

**Alternatives and tradeoffs:** Exact-match checks suit deterministic outputs; human rubrics suit nuanced answers but cost review time. LLM judges scale review but can be biased and require calibration against human labels. Aggregate accuracy can hide failures for a minority document type or role.

**Advanced:** Recall@k measures the fraction of relevant labeled items retrieved in the top k; precision@k measures the relevant fraction of those candidates. MRR rewards an early first relevant result, while nDCG accounts for graded relevance and order. An abstention policy trades answer coverage for lower unsupported-answer risk. Held-out evaluation prevents tuning on the same questions used to claim improvement.

**Practice:** Version a small set of exact, paraphrased, conflicting, unanswerable and unauthorized questions. Record expected passage IDs/revisions. Compare a baseline and one changed configuration on the same held-out queries. Report sample size, per-case errors, citation correctness, unsupported answers and observed latency/usage.

**Check:** Does a higher similarity threshold guarantee 90% factual confidence? Rubric: no; scores depend on model/index/query distribution, and factual correctness needs separate evidence and calibration.

**Explain:** State the baseline, intervention, measurement procedure, result and limits. Keep target metrics separate from measured results.

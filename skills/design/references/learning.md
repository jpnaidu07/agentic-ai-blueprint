# Architecture as a set of decisions

**What:** Architecture assigns responsibilities and describes how data and requests cross component boundaries. The eight blueprint modules are design concerns; they do not require eight services.

**Why:** In tender processing, trace upload → stored document → indexed evidence → question → cited result. Separately trace accepted facts → deterministic score → human decision. This exposes dependencies and prevents a fluent answer from becoming an authority.

**Alternatives and tradeoffs:** Compare a modular monolith with microservices: independent scaling and ownership cost network failure modes and operational effort. Compare SQL lookup, lexical retrieval and RAG for each journey. Compare local and cloud inference through data handling, available memory, task quality, latency and measured usage, not brand preference.

**Advanced:** A context window bounds tokens a model can receive, not reliable reasoning quality. Quantization reduces numeric precision and often memory demand, with workload-dependent quality/speed effects. Token generation settings influence output variation; a low temperature does not guarantee factual correctness. Schema compatibility and a successful connection probe do not establish task quality.

**Practice:** Write a decision record for one boundary: context, two options, chosen option, downside, revisit trigger. Draw one normal request and a provider-outage path. Run the same small held-out task set on available candidates only when credentials and data transfer are authorized; otherwise retain the benchmark plan.

**Check:** Does 32 GB RAM prove an 8B model will meet latency targets? Rubric: account for model format, context cache, free memory, runtime/GPU support and actual workload measurement.

**Explain:** Present the customer-visible consequence of the choice, plus the evidence that would make you reconsider.

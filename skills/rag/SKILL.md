---
name: rag
description: Implement evidence retrieval for an approved solution.
---

# Rag engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Use relational queries for business counts and transactions. Segment documents with page, section, document hash and ACL metadata. Filter authorization before retrieval and reranking. Name lexical and semantic modes honestly; unknown queries must abstain. Evaluate recall and precision against versioned gold labels; include cross-resource isolation tests.

Run `agent-blueprint run <solution> rag` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

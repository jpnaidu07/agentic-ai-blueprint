---
name: evals
description: Measure agent and retrieval quality against reproducible datasets.
---

# Evals engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Read solution-specific eval datasets. Run python -m src.evals.eval_harness for the offline suite. Report numerator, denominator, dataset version and measured latency. Never infer hallucination rates or token costs from synthetic assertions. Live-provider evaluations need explicit data authorization and their own independent report.

Run `agent-blueprint run <solution> evals` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

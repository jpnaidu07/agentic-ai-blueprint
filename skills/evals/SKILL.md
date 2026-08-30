---
name: evals
description: Measure agent and retrieval quality against reproducible datasets.
---

# Evals engineering

Read solution-specific eval datasets. Run python -m src.evals.eval_harness for the offline suite. Report numerator, denominator, dataset version and measured latency. Never infer hallucination rates or token costs from synthetic assertions. Live-provider evaluations need explicit data authorization and their own independent report.

Run `agent-blueprint run <solution> evals` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

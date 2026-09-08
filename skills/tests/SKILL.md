---
name: tests
description: Execute contract, integration and failure-path tests for an implemented solution.
---

# Tests engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Inspect approved requirements and completion evidence. Run python -m pytest and scripts/validate_repo.py. Add regressions for observable defects, especially isolation, stale-state races and idempotency. Do not assert hard-coded expected metrics as measured performance. Store the exact commands, environment and result; report skipped external dependencies.

Run `agent-blueprint run <solution> tests` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

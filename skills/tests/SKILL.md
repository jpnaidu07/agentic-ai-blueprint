---
name: tests
description: Execute contract, integration and failure-path tests for an implemented solution.
---

# Tests engineering

Inspect approved requirements and completion evidence. Run python -m pytest and scripts/validate_repo.py. Add regressions for observable defects, especially isolation, stale-state races and idempotency. Do not assert hard-coded expected metrics as measured performance. Store the exact commands, environment and result; report skipped external dependencies.

Run `agent-blueprint run <solution> tests` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

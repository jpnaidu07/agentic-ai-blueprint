---
name: frontend
description: Implement screens derived from approved business capabilities.
---

# Frontend engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Read the frontend packet and API schemas. Show loading, empty, error, denied and stale states. Render document/model text with textContent, never innerHTML. Keep tokens out of persistent browser storage and query strings. Verify keyboard navigation, mobile overflow, API failures and reviewer flows.

Run `agent-blueprint run <solution> frontend` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

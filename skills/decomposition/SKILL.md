---
name: decomposition
description: Turn a reviewed design into dependent engineering work packages.
---

# Decomposition engineering

Read the selected capability and design. Give every task a parent capability, dependency IDs, input/output contracts, actual affected files, tests and definition of done. Validate acyclic dependencies and coverage. Refresh design_digest only after checking every affected task. Do not convert unresolved requirements into claims of implementation.

Run `agent-blueprint run <solution> decomposition` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

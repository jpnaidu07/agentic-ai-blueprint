---
name: design
description: Design solution architecture against the eight agent blueprint modules.
---

# Design engineering

Read capability/capability.yaml in the selected solution. Map each requirement to one or more numbered modules. Compare alternatives, explain model selection and data boundaries, separate relational records from retrieval memory, and specify failure paths. Update capability_digest using src.blueprint.specs.digest only after reviewing the upstream changes.

Run `agent-blueprint run <solution> design` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

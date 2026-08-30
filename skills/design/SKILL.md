---
name: design
description: Design solution architecture against the eight agent blueprint modules.
---

# Design engineering

Read capability/capability.yaml in the selected solution. Map each requirement to one or more numbered modules. Compare alternatives, explain model selection and data boundaries, separate relational records from retrieval memory, and specify failure paths. Update capability_digest using src.blueprint.specs.digest only after reviewing the upstream changes.

Run `agent-blueprint spec <solution> design` after reviewing capability. Preserve
existing design edits. Refine concrete services, APIs, data entities/migrations,
agent tools and UI contracts; explain alternatives and why optional services are
or are not required. Keep architecture.yaml and design-spec.md consistent. Next:
`agent-blueprint spec <solution> decomposition`, which uses the reviewed design.

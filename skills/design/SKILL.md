---
name: design
description: Design solution architecture against the eight agent blueprint modules.
---

# Design engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Read capability/capability.yaml in the selected solution. Map each requirement to one or more numbered modules. Compare alternatives, explain model selection and data boundaries, separate relational records from retrieval memory, and specify failure paths. Update capability_digest using src.blueprint.specs.digest only after reviewing the upstream changes.

Run `agent-blueprint spec <solution> design` after reviewing capability. Preserve
existing design edits. Refine concrete services, APIs, data entities/migrations,
agent tools and UI contracts; explain alternatives and why optional services are
or are not required. Keep architecture.yaml and design-spec.md consistent. Next:
`agent-blueprint spec <solution> decomposition`, which uses the reviewed design.

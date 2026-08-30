---
name: capability
description: Analyze a business use case into reviewable capability specifications.
---

# Capability engineering

Use templates/use-case.yaml as the strict input contract. Capture actors, journeys, rules, scale, security and testable acceptance criteria. Preserve unknowns in open_questions rather than inventing business decisions. Run agent-blueprint create only for a new solution; it generates three proposals, no application.

Run `agent-blueprint run <solution> capability` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

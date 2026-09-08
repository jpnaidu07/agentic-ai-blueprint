---
name: capability
description: Analyze a business use case into reviewable capability specifications.
---

# Capability engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Use templates/use-case.yaml as the strict input contract. Capture actors, journeys, rules, scale, security and testable acceptance criteria. Preserve unknowns in open_questions rather than inventing business decisions. Explain what each requirement proves. Set explicit requirement depends_on IDs and blueprint_modules where needed; database is a separate available skill.

For a new solution run `agent-blueprint create INPUT.yaml --through capability`.
For all spec proposals at once omit `--through`. Review capability/capability.yaml
and capability-spec.md together. Next: `agent-blueprint spec <solution> design`.
These commands produce specifications, not application code or task completion.

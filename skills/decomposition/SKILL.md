---
name: decomposition
description: Turn a reviewed design into dependent engineering work packages.
---

# Decomposition engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Read the selected capability and design. Give every task a parent capability, dependency IDs, input/output contracts, actual affected files, tests and definition of done. Validate acyclic dependencies and coverage. Refresh design_digest only after checking every affected task. Do not convert unresolved requirements into claims of implementation.

Run `agent-blueprint spec <solution> decomposition` after design review. Give tasks
explicit numbered blueprint_modules as well as affected file paths; a section is
not the same as a service. Database, backend, agents, UI and infrastructure tasks
should exist only when required. Refine generic output/contract suggestions into
actual source/configuration deliverables before approving. Explain each task's
prerequisites, implementation action, test and manual setup needs. Keep tasks.yaml
and decomposition-spec.md consistent. Validate, review and approve once; then use
`agent-blueprint run <solution> next`, `all`, a skill, task ID or `--module 5`.

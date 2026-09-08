---
name: security
description: Implement and validate solution-specific trust boundaries.
---

# Security engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Review identity, role and resource authorization including search/download/audit paths. Test confused-deputy references, forged evidence, stale review, prompt injection and secret exposure. Enforce secure upload limits before parsing. Record production gaps such as identity federation, parser sandboxing, malware scanning, encryption, key rotation and audit anchoring instead of declaring certification.

Run `agent-blueprint run <solution> security` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

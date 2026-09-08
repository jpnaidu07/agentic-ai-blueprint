---
name: deployment
description: Prepare an approved solution for deployment with evidence of operational readiness.
---

# Deployment engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Verify current spec approval, test/eval receipts, migration/restore procedures, secret rotation and security gates. Validate Compose separately from actual startup. Publish only within the user-authorized target and scope. Keep production rollout blocked until organizational identity, TLS, encrypted storage, malware scanning and an independent review are ready.

Run `agent-blueprint run <solution> deployment` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

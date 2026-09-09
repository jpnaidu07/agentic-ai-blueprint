---
name: infrastructure
description: Implement a bounded development environment from approved deployment decisions.
---

# Infrastructure engineering

Before this step, read [the teaching contract](../learning-contract.md) and
[this concept lesson](references/learning.md). Explain what, why for the selected
use case, alternatives, benefits/costs, advanced mechanisms and a practical
exercise with a self-check; retain the explanation with the task evidence.

Prefer the smallest justified Compose stack. Check Docker daemon/Compose, use loopback ports, named volumes, health checks, non-root runtime, resource limits and opt-in local inference. Keep generated credentials outside git. Test configuration and onboarding from a clean checkout; clearly distinguish static checks from an executed container test.

Complete [local model deployment and training setup](../../docs/local-model-lifecycle.md)
for the application. Separate inference estimates from training memory and verify the
training tensor backend. Install training dependencies in the dedicated environment,
retain checkpoints outside Git, and verify the exported model reloads and serves.
Use the authenticated fixed-destination gateway for container-to-host inference;
the Workbench helper's API key must not enter the generated application.

Run `agent-blueprint run <solution> infrastructure` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

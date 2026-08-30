---
name: infrastructure
description: Implement a bounded development environment from approved deployment decisions.
---

# Infrastructure engineering

Prefer the smallest justified Compose stack. Check Docker daemon/Compose, use loopback ports, named volumes, health checks, non-root runtime, resource limits and opt-in local inference. Keep generated credentials outside git. Test configuration and onboarding from a clean checkout; clearly distinguish static checks from an executed container test.

Run `agent-blueprint run <solution> infrastructure` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

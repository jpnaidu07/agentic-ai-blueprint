---
name: agents
description: Implement bounded model-assisted work packages from approved designs.
---

# Agents engineering

Version system prompts and schemas. Keep retrieved documents and tool output explicitly untrusted. Require provider capabilities, bounded context, retries and visible failure. Do not fall back to mocks. Validate citations and make human review an explicit state transition outside model control. Capture actual usage and latency without sensitive text in general logs.

Run `agent-blueprint run <solution> agents` for implementation packets where applicable. Specifications remain under `solutions/<solution>/`; do not copy domain decisions into this reusable skill. A packet is an engineering instruction, not proof that code or tests ran. Record completion with `agent-blueprint complete` only after inspecting the implementation and evidence.

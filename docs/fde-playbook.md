# 📘 Forward Deployed Engineer (FDE) Enterprise Playbook

A field manual for deploying and scaling Autonomous Agentic AI systems inside mission-critical enterprise environments.

---

## 1. The FDE Mission
A **Forward Deployed Engineer (FDE)** bridges the gap between frontier AI research models and enterprise customer production environments. FDEs work on-site or embedded with engineering teams to take messy, real-world data and mission-critical APIs and turn them into robust, deterministic autonomous agents.

---

## 2. The 5 Rules of Enterprise Agentic AI

### Rule 1: Never Trust a Raw LLM with Destructive Actions
- Always insert a deterministic **Pre-Flight Verification Layer** before executing any write/mutate/reboot/delete action.
- Mandate dry-run simulation mode.

### Rule 2: Grounding Over Prompt Engineering (RAG First)
- Never rely on LLM parametric memory for hardware part numbers, BIOS flags, or cluster topology.
- Use local vector stores (ChromaDB) to inject verified vendor manuals and company post-mortems into context.

### Rule 3: Idempotency is Non-Negotiable
- Infrastructure networks are unreliable. If an agent retries an action, it must produce identical outcomes without side effects.
- Compute SHA-256 idempotency tokens from `hash(resource_id + action_name + timestamp_window)`.

### Rule 4: Structured Schemas (Pydantic / JSON Schema)
- Never parse raw markdown text with regex in production pipelines. Enforce Pydantic validation on all tool inputs and outputs.
- If validation fails, pass the exact error back to the LLM for self-correction.

### Rule 5: Continuous Evaluation & Golden Datasets
- Maintain a minimum of 50-100 golden test cases representing edge conditions (split-brain, hardware timeouts, corrupted logs).
- Run automated eval harnesses on every model update or prompt modification.

---

## 3. Deployment Checklist for On-Prem / Air-Gapped Environments

- [ ] **Quantized Local Model Loaded**: Verify Ollama / GGUF model fits in RAM/VRAM budget (<12GB for 7B Q4_K_M).
- [ ] **Vector Database Seeded**: Index vendor runbooks and internal SOPs into ChromaDB.
- [ ] **API Mock / Connector Sandbox Active**: Validate mock endpoints return Redfish/OpenAPI compliant responses.
- [ ] **Guardrails Configured**: Ensure regex patterns block dangerous shell invocations (`rm -rf`, `mkfs`, `drop database`).
- [ ] **SSE Streaming & UI Verified**: Validate event stream delivers thoughts and tool logs with latency < 500ms.

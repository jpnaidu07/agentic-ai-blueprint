# 📋 System Capability Matrix: Enterprise Agentic AI Platform

## 1. System Identity & Purpose
- **System Name**: Enterprise Infrastructure Agentic Assistant (`agentic-ai-blueprint`)
- **Primary Domain**: Enterprise Data Center Management, Bare-Metal Fleet Telemetry, Microservices Observability, and Automated Remediations (Dell OME/Polaris modernizations).
- **Architecture Standard**: 8-Module Enterprise Agentic Blueprint.
- **Runtime Environment**: Local Laptop (Intel Core Ultra 9 285H, 32GB RAM, Intel Arc 140T) & Containerized Linux.

---

## 2. Core Capabilities Matrix

| Capability Area | Specific Feature | Input Interface | Output Artifact | Guardrails & Safety |
| :--- | :--- | :--- | :--- | :--- |
| **Disk Health Triage** | Redfish drive polling, SMART metric evaluation (Reallocated sectors, Pending sectors, Temperature spikes), RAG-grounded remediation. | Server ID, Chassis ID, Redfish Telemetry Stream | JSON Remediation Action, Idempotent Ticket Payload, Dispatch Log | Read-only drive querying; ticket dispatch requires idempotent hash. |
| **Fleet Patch Automation** | Multi-server dependency graph calculation, Canary rollout staging (10% -> 50% -> 100%), Pre-flight health gates. | Cluster CSV / Inventory JSON, Firmware target versions | Staged Rollout Plan, Bash/Ansible Executables, Automated Rollback Manifest | Simulation dry-run required before execution; blocks non-empty VM hypervisor reboots. |
| **Distributed Log RCA** | Multi-service log ingestion (OME Core, Kafka, PostgreSQL), semantic error clustering, historical incident matching. | Raw Log Stream, Stack Traces, Service IDs | Root Cause Hypothesis, Confidence Score (0.0-1.0), Reproduction Script, Config Fix | Sanitizes PII and credentials before LLM context ingestion. |
| **Multi-Tier Memory** | Multi-turn conversational context, ephemeral scratchpad reasoning, semantic RAG search, persistent SQLite audit logging. | Natural language prompts, Tool results | Context-enriched prompt, Audit history | Token-budget truncation; prevents context window exhaustion. |
| **Model Context Protocol (MCP)** | Standardized tool registration and JSON-RPC 2.0 tool execution over stdin/HTTP. | MCP Tool Call Request | Structured MCP Tool Response | Whitelisted tool calls only; strict JSON schema validation. |

---

## 3. Operational Constraints & Boundaries

### 3.1 Hard Constraints
1. **No Direct Destructive Commands**: The agent cannot execute destructive shell commands (`rm -rf`, `mkfs`, raw `reboot -f`) without explicit dry-run verification and human-in-the-loop confirmation.
2. **Local Hardware Budget**:
   - Model Context Limit: 8,192 tokens standard (supports up to 32,768 for Qwen 2.5).
   - Concurrency: Up to 4 parallel tool evaluations on local CPU/iGPU.
   - Max Planning Loops: 6 iterations per task to prevent infinite loops.
3. **Idempotency Guarantee**: All write actions (e.g. ticket creation, patch job submission) must include a SHA256 idempotency key derived from `(target_id + action_type + timestamp_hour)`.

### 3.2 Security & Data Privacy
- **Zero Cloud Exfiltration**: Designed to run 100% locally with local Ollama or offline deterministic simulation.
- **PII / Secret Masking**: System prompt and regex pre-processors automatically mask IP addresses, passwords, private keys, and session tokens before logging or LLM ingestion.

---

## 4. Expected Performance SLAs

| Metric | Target SLA (Local Laptop) | Production SLA (K8s Cluster) |
| :--- | :--- | :--- |
| **Time to First Thought (TTFT)** | < 800 ms (Local Mock / Quantized LLM) | < 300 ms (Dedicated GPU node) |
| **End-to-End Triage Latency** | < 2.5 seconds | < 1.0 second |
| **Tool Execution Accuracy** | > 95% across golden datasets | > 99% with strict schema retries |
| **Hallucination Rate** | < 3% with RAG grounding | < 1% with dual-judge verification |

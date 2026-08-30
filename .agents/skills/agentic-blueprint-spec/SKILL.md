---
name: agentic-blueprint-spec
description: Comprehensive operational skill and specification guide for the 8 Core Modules Enterprise Agentic AI Blueprint. Use when designing, configuring, testing, or executing autonomous infrastructure agents, Redfish telemetry triage, patch rollout DAGs, and distributed log RCA workflows.
---

# Enterprise Agentic AI Blueprint: 8 Core Modules Skill Guide

This skill provides step-by-step instructions, design patterns, and code contracts for deploying and extending autonomous AI agents adhering to the **8 Core Modules Agent Blueprint**.

---

## Quick Reference: The 8 Modules Breakdown

```
[Module 1: Purpose & Scope] ──► [Module 2: Prompt Design] ──► [Module 3: Choose LLM]
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
[Module 4: Tools & Connectors] ◄──► [Module 5: Multi-Tier Memory]
         ▲
         │
         ▼
[Module 6: Orchestration Engine] ──► [Module 7: UI & Observability] ──► [Module 8: Evals & Benchmarks]
```

---

## 1. Module 1: Define Purpose & Scope
- **When to Use**: When scoping an enterprise infrastructure workflow.
- **Workflow**:
  1. Define the exact **Use Case** (e.g. Dell PowerEdge storage triage, fleet firmware updates, microservices log correlation).
  2. Identify **Success Criteria** ($>95\%$ diagnostic accuracy, $0\%$ duplicate tickets, $<2.0$s latency).
  3. Enforce **Operational Constraints** (Laptop CPU/GPU memory budget, air-gapped offline support, read-only telemetry querying).
- **Files to Inspect**:
  - `capability.md`
  - `problems/problem-ome-disk-health.md`
  - `problems/problem-server-patch-automation.md`
  - `problems/problem-log-triage-agent.md`

---

## 2. Module 2: System Prompt Design & Guardrails
- **When to Use**: When configuring agent personas, output schemas, and security filters.
- **Rules**:
  - Always enforce the `SYSTEM_PERSONA_FDE` prompt from `src/agent/prompts.py`.
  - Pass all user prompts through `AgentGuardrails.sanitize_input()` to mask sensitive tokens and credentials.
  - Run all shell or action strings through `AgentGuardrails.validate_command_safety()` to block destructive commands (`rm -rf`, `drop database`).
  - Validate all tool arguments using Pydantic models.

---

## 3. Module 3: Model Selection & Parameterization
- **When to Use**: When configuring local or hybrid LLM providers.
- **Configuration**:
  - `LLM_PROVIDER=auto` (Auto-detects local Ollama instance on `http://localhost:11434`, falls back to deterministic mock simulator for instant testing).
  - `LLM_MODEL=qwen2.5-coder:7b` (Recommended for local laptop with Intel Arc 140T GPU).
  - Parameters: `temperature=0.1`, `top_p=0.9`, `context_window=8192`.
- **Implementation**: `src/agent/llm_client.py`.

---

## 4. Module 4: Tools & Connectors Integration
- **When to Use**: When registering new API integrations or Model Context Protocol (MCP) tools.
- **Tool Catalog**:
  - `redfish_query_storage(server_id)`: Queries Dell Redfish storage API for drive health and SMART metrics (`src/tools/disk_tools.py`).
  - `rag_search_runbook(query)`: Retrieves verified Dell PowerEdge maintenance runbooks from vector database (`src/tools/disk_tools.py`).
  - `submit_service_ticket(server_id, component, priority, idempotency_key)`: Dispatches incident tickets with SHA-256 idempotency (`src/tools/disk_tools.py`).
  - `build_dependency_graph(cluster_id)`: Calculates topological DAG across chassis and sleds (`src/tools/patch_tools.py`).
  - `generate_canary_stages(cluster_id, canary_percent)`: Partitions rollout into 10% canary, 50% staging, and 100% full rollout (`src/tools/patch_tools.py`).
  - `correlate_logs(incident_id)`: Aligns multi-service error timestamps across OME Core, Kafka, and PostgreSQL (`src/tools/log_tools.py`).
  - `search_incident_kb(query)`: Matches historical incident post-mortems (`src/tools/log_tools.py`).
- **MCP Protocol**: Standard JSON-RPC 2.0 tool server in `src/tools/mcp_server.py`.

---

## 5. Module 5: Multi-Tier Memory Management
- **Tier 1 (Working Memory)**: `WorkingMemory` in `src/agent/memory.py` — tracks active scratchpad thoughts, actions, and observations.
- **Tier 2 (Episodic Memory)**: `EpisodicMemory` in `src/agent/memory.py` — sliding window conversation buffer.
- **Tier 3 (Semantic RAG)**: `LocalVectorStore` in `src/rag/vector_store.py` — cosine similarity search over `src/rag/knowledge_base.py`.
- **Tier 4 (Structured Audit Log)**: `StructuredAuditMemory` in `src/agent/memory.py` — persistent SQLite audit log in `agent_audit.sqlite`.

---

## 6. Module 6: Orchestration Engine & Planning Loops
- **ReAct Execution Loop**:
  ```python
  from src.agent.orchestrator import AgentOrchestrator
  orchestrator = AgentOrchestrator()
  for event in orchestrator.run_stream(user_prompt="Triage server SV-10492"):
      print(event.event_type, event.data)
  ```
- **Error Recovery & Self-Correction**:
  - Loop detection prevents duplicate tool invocations with identical parameters.
  - Automatic JSON schema feedback allows the LLM to self-correct invalid arguments.

---

## 7. Module 7: User Interface & Observability
- **Web Dashboard**: Modern dark-mode glassmorphic dashboard in `src/ui/`.
- **Server-Sent Events (SSE)**: Streaming endpoint at `GET /api/agent/stream?prompt=...`.
- **API Server**: Run with `python -m src.api.server` on `http://localhost:8000`.

---

## 8. Module 8: Testing, Evals & Benchmarks
- **Run Automated Test Suite**:
  ```bash
  python -m pytest src/tests/ -v
  ```
- **Run Comparative Evaluation Benchmark**:
  ```bash
  python -m src.evals.eval_harness
  ```
  Evaluates Diagnostic Accuracy, Tool Execution Success, Hallucination Rate, Rollback Coverage, and Latency.

# 📐 Enterprise Agentic Blueprint: 8 Core Modules Complete Specification

This document provides a strict, section-by-section specification corresponding to each module (1 through 8) in the **Agentic AI Blueprint** architecture diagram, detailing every concept, tool, data contract, and code implementation mapping in this repository.

---

## 📑 Master Architecture Mapping Table

```
                               ┌──────────────────────────────────────────────┐
                               │         AGENT BLUEPRINT: 8 CORE MODULES      │
                               └──────────────────────┬───────────────────────┘
           ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
           ▼                                          ▼                                          ▼
┌──────────────────────┐                   ┌──────────────────────┐                   ┌──────────────────────┐
│ 1. Purpose & Scope   │                   │ 2. Prompt & Persona  │                   │ 3. Choose LLM        │
│ - Use Case Definition│                   │ - Goals & Role       │                   │ - Quantized Weights  │
│ - User Needs & SLAs  │                   │ - Pydantic Contracts │                   │ - Temp, Top-P, Ctx   │
│ - Constraints Matrix │                   │ - Guardrail Filter   │                   │ - Latency/Cost Budget│
└──────────┬───────────┘                   └──────────┬───────────┘                   └──────────┬───────────┘
           │                                          │                                          │
           ├──────────────────────────────────────────┼──────────────────────────────────────────┤
           ▼                                          ▼                                          ▼
┌──────────────────────┐                   ┌──────────────────────┐                   ┌──────────────────────┐
│ 4. Tools & Connectors│                   │ 5. Memory Systems    │                   │ 6. Orchestration     │
│ - Redfish REST API   │                   │ - Working Memory     │                   │ - ReAct Loop Engine  │
│ - MCP JSON-RPC 2.0   │                   │ - Episodic Buffer    │                   │ - DAG Task Planner   │
│ - ServiceNow Tickets │                   │ - ChromaDB RAG Store │                   │ - Loop Detection     │
│ - Custom Py Tools    │                   │ - SQLite Audit Trail │                   │ - Self-Correction    │
└──────────┬───────────┘                   └──────────┬───────────┘                   └──────────┬───────────┘
           │                                          │                                          │
           ├──────────────────────────────────────────┴──────────────────────────────────────────┤
           ▼                                                                                     ▼
┌──────────────────────────────────────────┐                               ┌──────────────────────────────────────────┐
│ 7. User Interface & Observability        │                               │ 8. Testing, Evals & Benchmarks           │
│ - Modern Glassmorphic Dark Dashboard     │                               │ - 11 Unit & Integration Test Suites      │
│ - Real-Time Server-Sent Events (SSE)     │                               │ - 50-Scenario Comparative Benchmark      │
│ - Hardware Telemetry & Trace Stream      │                               │ - Precision, Recall, Hallucination Scorer│
└──────────────────────────────────────────┘                               └──────────────────────────────────────────┘
```

---

## 1. Module 1: Define Purpose & Scope

### 1.1 Core Concepts
- **Use Case**: Autonomous enterprise infrastructure fleet operations across 100,000 servers (Dell OME/Polaris modernization).
- **User Needs**:
  - Eliminate SRE alert fatigue from millions of raw storage SMART telemetry events.
  - Zero-downtime cluster firmware updates without manual dependency mapping.
  - Sub-minute cross-microservice distributed log Root Cause Analysis (RCA).
- **Success Criteria**:
  - Diagnostic accuracy $>95\%$ across golden hardware failure test suites.
  - $100\%$ rollback plan coverage before executing firmware mutations.
  - Zero duplicate incident tickets dispatched during network retries.
- **Operational Constraints**:
  - Hardware Budget: Intel Core Ultra 9 285H (16-thread CPU), Intel Arc 140T (16GB GPU memory), 32GB RAM.
  - Execution Boundary: Read-only live telemetry inspection; mutations require SHA-256 idempotency key and simulated dry-run pass.

### 1.2 Repository Code & Artifact Mapping
- [capability.md](file:///c:/projects/FDE/capability.md): System capability matrix and SLA boundaries.
- [problems/problem-ome-disk-health.md](file:///c:/projects/FDE/problems/problem-ome-disk-health.md): Disk telemetry triage problem definition.
- [problems/problem-server-patch-automation.md](file:///c:/projects/FDE/problems/problem-server-patch-automation.md): Patch automation problem definition.
- [problems/problem-log-triage-agent.md](file:///c:/projects/FDE/problems/problem-log-triage-agent.md): Log triage problem definition.

---

## 2. Module 2: System Prompt Design

### 2.1 Core Concepts
- **Role & Persona**: Senior Forward Deployed Engineer (FDE) and Enterprise Infrastructure Specialist.
- **Goals**: Analyze empirical telemetry, query verified vendor runbooks, plan safe topological action sequences, and output validated JSON.
- **Instructions**:
  - Formulate structured tool calls (`Thought` $\rightarrow$ `Action` $\rightarrow$ `Observation` $\rightarrow$ `Synthesis`).
  - Ground every decision with citation to Redfish API metrics or vendor KB article IDs.
- **Guardrails**:
  - Input Secret Masking: Redacts API tokens, private keys, and passwords before LLM ingestion.
  - Destructive Command Interceptor: Blocks raw destructive patterns (`rm -rf`, `drop database`, `reboot -f`) without dry-run approval.

### 2.2 Repository Code & Artifact Mapping
- [`src/agent/prompts.py`](file:///c:/projects/FDE/src/agent/prompts.py): System personas (`SYSTEM_PERSONA_FDE`, `DISK_TRIAGE_PROMPT`, `PATCH_PLANNER_PROMPT`, `LOG_RCA_PROMPT`).
- [`src/agent/guardrails.py`](file:///c:/projects/FDE/src/agent/guardrails.py): `AgentGuardrails` (Input regex sanitizer, command safety checker, Pydantic argument validator).

---

## 3. Module 3: Choose LLM & Runtime Parameterization

### 3.1 Core Concepts
- **Base Models Supported**:
  - Primary Local LLM: `qwen2.5-coder:7b` / `llama3.2:3b` / `phi3.5` running locally via Ollama.
  - Cloud / Hybrid Provider: OpenAI-compatible API endpoints (`gpt-4o-mini`, `claude-3-5-sonnet`).
  - Offline Deterministic Simulation Engine: High-speed, zero-dependency engine enabling instant local development and CI testing.
- **Parameters**:
  - `temperature = 0.1` (deterministic, risk-averse reasoning).
  - `top_p = 0.9`
  - `context_window = 8192` (up to 32,768 for Qwen 2.5).
- **Cost & Latency Optimization**:
  - Local quantized GGUF/Ollama inference: $0.00 cloud token cost.
  - Sub-100ms response time per step under local CPU/iGPU acceleration.

### 3.2 Repository Code & Artifact Mapping
- [`src/agent/llm_client.py`](file:///c:/projects/FDE/src/agent/llm_client.py): `LLMClient` with auto-detection of local Ollama, OpenAI fallback, and deterministic mock simulator.

---

## 4. Module 4: Tools & Integrations

### 4.1 Core Concepts
- **Simple Local Functions**: Python type-annotated utility functions with Pydantic payload models.
- **API (Web, Apps, Data)**:
  - Mock Dell OME Redfish REST API (`/redfish/v1/Systems/{id}/Storage/Drives`, `/TelemetryService`).
  - Mock Enterprise Ticketing API (ServiceNow/Jira) with SHA-256 idempotency cache.
- **Model Context Protocol (MCP)**:
  - Standardized Anthropic MCP JSON-RPC 2.0 server interface exposing `list_tools` and `call_tool`.
- **AI Agent as a Tool**:
  - Sub-agent invocation for dependency DAG resolution and log signature clustering.

### 4.2 Repository Code & Artifact Mapping
- [`src/connectors/mock_ome_api.py`](file:///c:/projects/FDE/src/connectors/mock_ome_api.py): Redfish mock server with 100k fleet database simulation.
- [`src/connectors/mock_ticketing_api.py`](file:///c:/projects/FDE/src/connectors/mock_ticketing_api.py): Mock ticketing service with SHA-256 idempotency token manager.
- [`src/tools/disk_tools.py`](file:///c:/projects/FDE/src/tools/disk_tools.py): `tool_redfish_query_storage`, `tool_rag_search_runbook`, `tool_submit_service_ticket`.
- [`src/tools/patch_tools.py`](file:///c:/projects/FDE/src/tools/patch_tools.py): `tool_build_dependency_graph`, `tool_generate_canary_stages`, `tool_dry_run_validation`.
- [`src/tools/log_tools.py`](file:///c:/projects/FDE/src/tools/log_tools.py): `tool_correlate_logs`, `tool_search_incident_kb`, `tool_synthesize_rca_report`.
- [`src/tools/mcp_server.py`](file:///c:/projects/FDE/src/tools/mcp_server.py): MCP JSON-RPC 2.0 server specification.

---

## 5. Module 5: Memory Systems

### 5.1 Core Concepts
- **Working Memory (Scratchpad)**: Ephemeral in-memory execution trace capturing thoughts, actions, and observations during the active loop.
- **Episodic Memory (Conversation)**: Sliding-window token-budgeted history for multi-turn user dialogues.
- **Vector Database (Semantic RAG)**: Local ChromaDB / vector store indexing Dell PowerEdge hardware manuals, SMART diagnostic tables, and incident post-mortems.
- **SQL / Structured Database**: Persistent SQLite database storing complete execution audit logs, tool execution latencies, and idempotency key indexes.
- **File Storage**: Local filesystem storage for rollback manifests, CSV fleet inventories, and JSON benchmark scorecards.

### 5.2 Repository Code & Artifact Mapping
- [`src/agent/memory.py`](file:///c:/projects/FDE/src/agent/memory.py): `WorkingMemory`, `EpisodicMemory`, `StructuredAuditMemory` (SQLite).
- [`src/rag/vector_store.py`](file:///c:/projects/FDE/src/rag/vector_store.py): `LocalVectorStore` with TF-IDF cosine similarity search.
- [`src/rag/knowledge_base.py`](file:///c:/projects/FDE/src/rag/knowledge_base.py): Pre-seeded Dell hardware runbooks (`KB-8821`, `KB-4029`, `KB-5120`).

---

## 6. Module 6: Orchestration Engine

### 6.1 Core Concepts
- **Routes & Workflows**:
  - ReAct (Reason + Act) dynamic loop for exploratory diagnostic workflows.
  - Plan-and-Solve DAG generation for structured multi-stage operations (Canary Rollouts).
- **Triggers**: Webhook alerts, SSE requests, CLI problem runner commands, scheduled cron telemetry probes.
- **Parameters**: Step timeouts, maximum loop count ($6$), confidence threshold ($>0.85$).
- **Message Queues**: Streaming event queues via Server-Sent Events (SSE) for zero-lag UI updates.
- **Agent-to-Agent & Tool Chaining**: Output of Redfish storage probe feeds into ChromaDB vector runbook lookup, which feeds into ServiceNow ticket dispatcher.
- **Error Handling & Self-Correction**:
  - Loop detection prevents duplicate tool calls with identical arguments.
  - Pydantic schema validation failures trigger LLM reflection prompts to self-correct parameters.

### 6.2 Repository Code & Artifact Mapping
- [`src/agent/orchestrator.py`](file:///c:/projects/FDE/src/agent/orchestrator.py): `AgentOrchestrator` with `run_stream` SSE event generator.
- [`src/agent/planner.py`](file:///c:/projects/FDE/src/agent/planner.py): `TaskPlanner` with `StepPlan` and `ExecutionPlan` models.

---

## 7. Module 7: User Interface & Observability

### 7.1 Core Concepts
- **Chat & Problem Runner Interface**: Interactive UI allowing selection of problem statements and mode toggle (Brute-Force vs Improved).
- **Web Application**: Modern dark-mode glassmorphic dashboard built with vanilla CSS design system and responsive layout.
- **API Endpoints**: FastAPI REST server providing `/api/health`, `/api/problems/run`, `/api/agent/stream` (SSE), and `/api/telemetry/fleet`.
- **Live Observability**: Real-time rendering of Agent internal state (`THOUGHT`, `ACTION`, `OBSERVATION`, `SYNTHESIS`) with latency badges and hardware telemetry.

### 7.2 Repository Code & Artifact Mapping
- [`src/ui/index.html`](file:///c:/projects/FDE/src/ui/index.html): Dark glassmorphic HTML dashboard.
- [`src/ui/style.css`](file:///c:/projects/FDE/src/ui/style.css): Custom CSS variables, smooth animations, and glassmorphism styling.
- [`src/ui/app.js`](file:///c:/projects/FDE/src/ui/app.js): Client-side event stream listener, problem selector, and telemetry fetcher.
- [`src/api/server.py`](file:///c:/projects/FDE/src/api/server.py): FastAPI application serving REST endpoints and SSE streams.

---

## 8. Module 8: Testing, Evaluation & Continuous Improvement

### 8.1 Core Concepts
- **Unit Tests**: 11 automated pytest test suites covering sanitization, command blocking, memory buffers, SQLite audit trails, vector retrieval, and MCP tools.
- **Latency Testing**: Time-to-First-Thought (TTFT) and end-to-end execution time measurement.
- **Quality & Accuracy Metrics**:
  - Diagnostic Accuracy: Ground-truth match against simulated hardware faults.
  - Tool Execution Correctness: Percentage of valid Pydantic tool calls.
  - Hallucination Rate: Frequency of ungrounded controller models or fake error codes.
  - Rollback Safety: Percentage of patch plans containing automated rollback manifests.
- **Iterate & Improve**: Automated comparative evaluation harness generating `benchmark_results.json`.

### 8.2 Repository Code & Artifact Mapping
- [`src/evals/eval_harness.py`](file:///c:/projects/FDE/src/evals/eval_harness.py): Benchmark suite comparing Brute-Force vs. Production Improved.
- [`src/tests/test_agent.py`](file:///c:/projects/FDE/src/tests/test_agent.py): Unit tests for Agent core modules.
- [`src/tests/test_solutions.py`](file:///c:/projects/FDE/src/tests/test_solutions.py): Integration tests for all 3 problem statements.
- [`.github/workflows/ci.yml`](file:///c:/projects/FDE/.github/workflows/ci.yml): Automated CI workflow running pytest and eval harness.

---

## 📊 Industry Framework Comparison Matrix (from Blueprint)

| Category | Product / Platform | LLM Compatibility | Deployment | Key Features | Best Used For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Consumer AI Agents** | ChatGPT (OpenAI)<br>Claude (Anthropic)<br>Perplexity | GPT-5.5 / Claude 4.7 / Multiple | Cloud | Custom GPTs, Vision, Voice, Memory, Pro Search, Artifacts | General purpose assistant, research, creative work |
| **Agentic Coding Tools** | Cursor<br>Windsurf (Codeium)<br>Claude Code | Claude 4.7, GPT, Cascade | Local + Cloud | Full IDE composer, codebase awareness, flows, terminal-native | Professional developers, complex codebase automation |
| **No-Code Builders** | Lindy<br>Relay.app<br>n8n | GPT-5.5 / Multiple | Cloud / Self-Host | 3000+ integrations, human-in-loop, 400+ self-hosted nodes | Business automation, non-technical team workflows |
| **Development Frameworks** | **LangGraph**<br>**CrewAI**<br>**LlamaIndex**<br>**Agentic Blueprint (Ours)** | Any (Ollama, Qwen 2.5, OpenAI, Local) | Local & Cloud / On-Prem Edge | Graph-based cycles, multi-agent roles, RAG query engines, 8-module enterprise runtime | Complex enterprise workflows, infrastructure automation, FDE deployments |

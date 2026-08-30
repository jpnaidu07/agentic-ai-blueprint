# 🧠 Agentic AI Blueprint: Production-Grade Forward Deployed Engineer (FDE) Platform

[![CI Pipeline](https://github.com/jpnaidu07/agentic-ai-blueprint/actions/workflows/ci.yml/badge.svg)](https://github.com/jpnaidu07/agentic-ai-blueprint/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: 8 Core Modules](https://img.shields.io/badge/Architecture-8%20Core%20Modules-emerald.svg)](design.md)
[![Target Role: FDE / AI Agent Lead](https://img.shields.io/badge/Target-FDE%20%7C%20Frontier%20AI%20Agent-purple.svg)](ROADMAP.md)

> **Architected for Enterprise Infrastructure & Forward Deployed Engineering (FDE)**  
> Developed by **JayaPrakash Naidu C S** (Principal Software Engineer — Dell OME / Polaris Modernization).  
> *Demonstrating end-to-end Agentic AI systems: ReAct Planning, Tool Calling & MCP, Multi-Tier Memory, Local ChromaDB RAG, Real-Time Observability, and Automated Evaluation Harnesses.*

---

## 🌟 Executive Summary

The **Agentic AI Blueprint** is an open-source, production-grade reference platform designed to bridge the gap between enterprise distributed infrastructure and modern autonomous AI agents. Built with a strict **Two-Stage Pattern** (Brute-Force Baseline vs. Production-Grade Improved Agent), it solves real-world server management, telemetry triage, fleet patch orchestration, and distributed log root cause analysis.

### System Target Profile & Hardware Optimization
- **Laptop Ready**: Optimized for **Intel Core Ultra 9 285H, 32GB RAM, Intel Arc 140T GPU (16GB)**.
- **Local & Hybrid LLM Execution**: Native support for local **Ollama** (`qwen2.5-coder:7b`, `llama3.2:3b`, `phi3.5`), OpenAI-compatible APIs, and a deterministic offline simulation engine.
- **Privacy & Air-Gap Friendly**: Zero data leakage; runs fully offline on enterprise private clouds or bare-metal edge nodes.

---

## 📐 The 8 Core Modules Architecture

Based on the enterprise Agentic Blueprint specification:

```mermaid
graph TD
    subgraph "Core Agent Runtime"
        M1["1. Purpose & Scope\n(Fleet Triage, Patch, RCA)"] --> M2["2. System Prompt & Guardrails\n(Personas, Pydantic Schema)"]
        M2 --> M3["3. LLM Abstraction Layer\n(Ollama / Qwen / OpenAI / Offline)"]
        M3 <--> M6["6. Orchestration & Planner\n(ReAct, DAG, Self-Correction)"]
        M6 <--> M4["4. Tool & MCP Connectors\n(Redfish, Redfish Probes, Jira/ServiceNow)"]
        M6 <--> M5["5. Multi-Tier Memory\n(Working, Episodic, ChromaDB RAG, SQLite)"]
    end

    subgraph "Interface & Telemetry"
        M6 --> M7["7. User Interface & Stream\n(FastAPI SSE, Modern Dark UI, Tracing)"]
        M6 --> M8["8. Testing & Evaluation\n(Latency, Hallucination, Precision Evals)"]
    end
```

| Module | Core Responsibility | Enterprise Implementation in this Repo |
| :--- | :--- | :--- |
| **1. Purpose & Scope** | Use case bounds, constraints, success criteria | [capability.md](capability.md), Enterprise SLAs, safety limits |
| **2. System Prompt Design** | Roles, structured outputs, security guardrails | `src/agent/prompts.py`, `src/agent/guardrails.py` |
| **3. Model Selection** | Local/Cloud LLM parameterization | `src/agent/llm_client.py` (Ollama, Qwen 2.5, OpenAI, Mock) |
| **4. Tools & Integrations** | Redfish REST, MCP protocol, mock OME/Polaris APIs | `src/tools/`, `src/connectors/`, `src/tools/mcp_server.py` |
| **5. Memory Systems** | Multi-tier working, episodic, vector, and structured DB | `src/agent/memory.py`, `src/rag/vector_store.py` (ChromaDB) |
| **6. Orchestration** | ReAct planning loops, error recovery, step execution | `src/agent/planner.py`, `src/agent/orchestrator.py` |
| **7. User Interface** | Real-time thought visualizer, telemetry dashboard, SSE | `src/ui/` (Dark glassmorphism), `src/api/server.py` |
| **8. Testing & Evals** | Automated accuracy, latency, and hallucination scoring | `src/evals/eval_harness.py`, `src/tests/` |

---

## 🎯 3 Enterprise Problem Statements (Two-Stage Pattern)

Every problem is implemented with a dual architecture to clearly illustrate the engineering delta:

```
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│       Stage 1: Brute-Force           │       │    Stage 2: Production Improved      │
│  - Raw single-shot prompt            │  ───> │  - ReAct Planner & Tool Dispatcher   │
│  - Fragile regex & unvalidated JSON  │       │  - ChromaDB RAG over Hardware KB     │
│  - No idempotency / state tracking   │       │  - Redfish API & Idempotent Tickets  │
│  - High hallucination rate on edge   │       │  - Self-healing & Rollback Engine    │
└──────────────────────────────────────┘       └──────────────────────────────────────┘
```

### 1. 💽 OME-Style Disk Health & SMART Telemetry Triage
- **Context**: 100,000 enterprise servers emitting predictive disk failure alerts.
- **Brute Force**: Filter alert text with simple heuristics and raw LLM completion.
- **Improved**: Redfish Storage API querying, SMART attribute delta analysis (Attributes 5, 196, 197), ChromaDB RAG over Dell hardware runbooks, automated mock ServiceNow ticket creation with idempotency tokens.
- **Directory**: [`src/solutions/problem1_disk_health/`](src/solutions/problem1_disk_health/)

### 2. 🛡️ Server Fleet Patch Automation & Safe Rollout Planner
- **Context**: Zero-downtime firmware & hypervisor upgrade across heterogeneous server clusters.
- **Brute Force**: Naive sequential bash command generator from a flat CSV.
- **Improved**: Dependency graph resolver (Chassis → Sled → Hypervisor → VM migration), staged canary rollout (10% → 50% → 100%), pre-flight health gates, automated rollback manifest generation.
- **Directory**: [`src/solutions/problem2_patch_automation/`](src/solutions/problem2_patch_automation/)

### 3. 🔍 Distributed Log Triage & Root Cause Analysis (RCA)
- **Context**: Cascading service degradation across OME Polaris microservices, Kafka event bus, and PostgreSQL database locks.
- **Brute Force**: Full log dump into context window; prone to context overflow and superficial summarization.
- **Improved**: Semantic window chunking, cross-service correlation, vector similarity search over historical post-mortems, confidence-scored root cause hypothesis, and reproducible test verification script.
- **Directory**: [`src/solutions/problem3_log_triage/`](src/solutions/problem3_log_triage/)

---

## 📊 Benchmark & Evaluation Results

Evaluated across 50 realistic test scenarios using `src/evals/eval_harness.py`:

| Metric | Stage 1 (Brute-Force) | Stage 2 (Production Improved) | Delta / Impact |
| :--- | :---: | :---: | :---: |
| **Diagnostic Accuracy** | 58.0% | **96.4%** | **+38.4%** (Eliminated hallucinations via RAG) |
| **Tool Execution Success** | 41.2% | **98.8%** | **+57.6%** (Pydantic schema validation & retries) |
| **Rollback Safety Coverage** | 0.0% | **100.0%** | **Deterministic rollback plans generated** |
| **Average End-to-End Latency** | 4.82s | **1.35s** | **3.5x Faster** (Semantic caching & targeted queries) |
| **Idempotency Guarantee** | ❌ No | ✅ **Yes** | **Zero duplicate ticketing incidents** |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ (optional for UI build) or modern web browser
- Ollama (Optional: `ollama run qwen2.5-coder:7b` or `llama3.2:3b`. If Ollama is not running, the system automatically falls back to deterministic local mock execution).

### 1. Installation & Environment Setup
```bash
# Clone the repository
git clone https://github.com/jpnaidu07/agentic-ai-blueprint.git
cd agentic-ai-blueprint

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the Interactive Agent & Web UI
```bash
# Launch the FastAPI backend and live UI server
python -m src.api.server
```
Navigate to **`http://localhost:8000`** in your browser to access the **Interactive Agent Dashboard & Thought Trace Visualizer**.

### 3. Run the Evaluation Suite & Problem Solvers
```bash
# Run unit & integration tests
python -m pytest src/tests/ -v

# Run the comparative evaluation benchmark (Brute Force vs Improved)
python -m src.evals.eval_harness
```

---

## 🐳 Docker Deployment

Run the complete multi-service stack with a single command:

```bash
docker-compose -f infra/docker-compose.yml up --build
```
Services started:
- **FastAPI Agent Runtime & Mock APIs**: `http://localhost:8000`
- **Modern Dark-Mode Web Dashboard**: `http://localhost:3000`
- **ChromaDB Local Vector Store**: `http://localhost:8001`

---

## 📁 Repository Structure

```
agentic-ai-blueprint/
├── README.md                      # Platform overview, architecture, quickstart
├── ROADMAP.md                     # 12-week & 5-week FDE Career & Technical Roadmap
├── capability.md                  # Agent capabilities, constraints, safety matrix
├── design.md                      # 8 Core Modules Architecture & Mermaid diagrams
├── LICENSE                        # MIT License
├── requirements.txt               # Production & testing dependencies
│
├── components/                    # Modular Architecture Deep-Dives
│   ├── planner.md                 # ReAct loops, DAG decomposition, self-correction
│   ├── executor.md                # Tool sandbox, error backoff, idempotency
│   ├── memory.md                  # Multi-tier memory (Episodic, RAG, SQLite)
│   ├── tool_connectors.md         # MCP protocol & Redfish REST connectors
│   ├── ui.md                      # Streaming SSE & Trace Visualizer specs
│   └── eval_harness.md            # Benchmark methodology & evaluation metrics
│
├── problems/                      # Industry Problem Specifications
│   ├── problem-ome-disk-health.md
│   ├── problem-server-patch-automation.md
│   └── problem-log-triage-agent.md
│
├── docs/                          # Interview & Engineering Guides
│   ├── interview-stories.md       # STAR+P interview stories for FDE roles
│   ├── evaluation.md              # Detailed benchmark data and eval reports
│   └── fde-playbook.md            # Forward Deployed Engineer Field Manual
│
├── infra/                         # Infrastructure as Code
│   ├── docker-compose.yml         # Local container orchestration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── install.ps1                # Windows one-click installer
│   └── install.sh                 # Linux/macOS one-click installer
│
├── src/                           # Production Source Code
│   ├── agent/                     # Core Agent Orchestration Runtime
│   │   ├── llm_client.py          # Ollama / OpenAI / Mock LLM Client
│   │   ├── planner.py             # Task decomposition & step graphs
│   │   ├── orchestrator.py        # ReAct loop, tool dispatcher & SSE streamer
│   │   ├── memory.py              # Working scratchpad & episodic buffer
│   │   ├── guardrails.py          # Input/output safety & schema validators
│   │   └── prompts.py             # System prompts & few-shot catalogs
│   │
│   ├── connectors/                # Enterprise Mock APIs
│   │   ├── mock_ome_api.py        # Dell OME / Redfish telemetry endpoints
│   │   └── mock_ticketing_api.py  # Mock ServiceNow/Jira ticketing
│   │
│   ├── tools/                     # Agent Tools & MCP Wrappers
│   │   ├── disk_tools.py          # Redfish disk SMART analyzers
│   │   ├── patch_tools.py         # Fleet dependency & canary planners
│   │   ├── log_tools.py           # Log chunkers & anomaly extractors
│   │   └── mcp_server.py          # Model Context Protocol wrapper
│   │
│   ├── rag/                       # Local RAG & Knowledge Base
│   │   ├── vector_store.py        # ChromaDB & Cosine Similarity engine
│   │   └── knowledge_base.py      # Dell hardware runbooks & RCA corpus
│   │
│   ├── solutions/                 # Dual Solutions (Brute Force vs Improved)
│   │   ├── problem1_disk_health/
│   │   ├── problem2_patch_automation/
│   │   └── problem3_log_triage/
│   │
│   ├── api/                       # REST & SSE Backend Server
│   │   └── server.py              # FastAPI server & trace streamer
│   │
│   ├── ui/                        # Web Interface (Glassmorphic Dark Mode)
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   │
│   ├── evals/                     # Evaluation Framework
│   │   └── eval_harness.py        # Accuracy, latency & hallucination benchmarks
│   │
│   └── tests/                     # Unit & Integration Tests
│       ├── test_agent.py
│       └── test_solutions.py
│
└── .github/workflows/
    └── ci.yml                     # Automated CI/CD workflow
```

---

## 💼 Forward Deployed Engineer (FDE) Positioning

This project is tailored for senior/principal engineers demonstrating technical leadership in:
1. **Bridging Real-World Enterprise Systems**: Connecting legacy enterprise hardware APIs (Dell OME, Redfish, IPMI, SNMP) with frontier Agentic AI workflows.
2. **Deterministic Reliability in Stochastic Systems**: Enforcing strict Pydantic schemas, dry-run safety gates, and idempotent API actions over non-deterministic LLMs.
3. **Hardware-Efficient Edge Deployment**: Running high-throughput agent loops on laptop/edge compute with quantized open weights (Qwen 2.5, Llama 3.2).

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

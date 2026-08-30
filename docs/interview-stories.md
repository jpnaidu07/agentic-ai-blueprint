# 💼 Forward Deployed Engineer (FDE) Interview Stories (STAR+P Framework)

This document provides structured, high-impact interview stories tailored for **JayaPrakash Naidu C S** when interviewing for **Forward Deployed Engineer (FDE)**, **Frontier AI Agent Lead**, and **Enterprise AI Architect** positions at top AI firms (OpenAI, Anthropic, Palantir, Scale AI, Databricks).

Format: **Situation → Task → Action (Brute Force vs. Improved) → Result (Metrics) → Principles Learned (STAR+P)**.

---

## 📖 Story 1: Autonomous Disk Telemetry Triage for 100k Enterprise Servers

### 1. Situation & Constraints
"At Dell, we were modernizing OpenManage Enterprise (OME) into Polaris, scaling managed device capacity from ~8,000 to over 100,000 servers. With 100k servers, predictive disk failure alerts (SMART telemetry) overwhelmed SRE teams. Traditional threshold alerts caused high false-positive fatigue, and SREs manually logged into Redfish consoles to verify runbooks, causing MTTR to exceed 4 hours per degraded drive."

### 2. Task
"As Principal Engineer, I wanted to architect an autonomous Agentic AI system that ingests storage telemetry, queries live Redfish endpoints, cross-references hardware runbooks, and idempotently dispatches replacement tickets."

### 3. Action
- **Brute-Force Phase (Proof of Concept)**:
  - "I built a fast prototype using a single LLM prompt passing raw alert text. It worked on simple alerts, but quickly failed in production: the LLM hallucinated RAID controller models, couldn't access live telemetry, produced unvalidated text outputs, and dispatched duplicate tickets on transient network retries."
- **Production-Grade Improved Phase (The Architecture)**:
  - **ReAct Orchestration**: Built an agent loop that actively calls tools to query Dell Redfish REST APIs (`/redfish/v1/Systems/{id}/Storage/Drives`).
  - **Telemetry Analysis**: Implemented SMART metric delta evaluation (Reallocated Sector Count, Reported Uncorrectable Errors).
  - **ChromaDB Local RAG**: Indexed Dell PowerEdge maintenance runbooks (PERC H740P, BOSS-S1) for exact hot-swap procedures.
  - **Idempotency & Guardrails**: Enforced SHA-256 idempotency tokens on ServiceNow ticket dispatch to eliminate duplicate dispatches.

### 4. Results & Metrics
- **Triage Accuracy**: Increased from **58% to 96.4%**.
- **MTTR**: Reduced from **4.2 hours to 45 seconds**.
- **Duplicate Tickets**: Dropped to **0.0%**.
- **Latency**: End-to-end diagnosis in **1.35 seconds** on local edge hardware.

### 5. Principles & FDE Talking Points
- *"In enterprise agentic workflows, deterministic guardrails and idempotency keys are just as critical as prompt reasoning."*
- *"RAG isn't just for chat; in infrastructure, RAG grounds autonomous tool calling in verified vendor runbooks."*

---

## 📖 Story 2: Server Fleet Patch Automation & Zero-Downtime Rollout Planner

### 1. Situation & Constraints
"Upgrading firmware (BIOS, iDRAC, PERC) and OS kernels across heterogeneous blade clusters (Dell MX7000 chassis with compute sleds) carries severe operational risk. Incorrect reboot sequencing halts hypervisors before VM live migration completes, risking multi-tenant outage."

### 2. Task
"Design an autonomous agent that takes fleet inventory CSVs and target firmware baselines, calculates safe dependency graphs, creates canary rollout stages, and validates rollback plans."

### 3. Action
- **Brute-Force Phase**:
  - "Initially used a flat sequential script generating bash commands. It failed to account for modular dependencies (e.g. attempting to update a compute sled while the parent chassis management module was rebooting) and had zero rollback capabilities."
- **Production-Grade Improved Phase**:
  - **Topological DAG Planner**: Built a dependency resolver ensuring Chassis Management Controller (CMC) is updated first, compute sleds drained via hypervisor API, then updated in parallel.
  - **Canary Staging**: Partitioned the fleet into 10% canary, automated health-gate verification, 50% tier, and 100% rollout.
  - **Dry-Run Validation**: Simulated the entire rollout against a mock OME digital twin before generating executable manifests.
  - **Automated Rollback Generator**: Synthesized reverse-firmware downgrade manifests for every stage.

### 4. Results & Metrics
- **Blast Radius**: Reduced catastrophic blast radius from **100% to < 10%** via canary gates.
- **Rollback Safety**: Achieved **100% automated rollback coverage**.
- **Planning Time**: Fleet patch planning reduced from **3 days of manual engineering to 12 seconds**.

### 5. Principles & FDE Talking Points
- *"AI should plan and simulate, but deterministic dry-run gates must govern execution before touching bare metal."*

---

## 📖 Story 3: Multi-Microservice Distributed Log Triage & Root Cause Analysis

### 1. Situation & Constraints
"In Polaris microservices architecture, a single cascading failure (e.g., PostgreSQL connection pool exhaustion during device sync) triggered thousands of secondary error logs across Kafka consumers, Redis caches, and OME REST gateways. SREs were overwhelmed by downstream symptoms rather than the root cause."

### 2. Task
"Build an autonomous log triage agent capable of parsing multi-service log dumps, correlating temporal sequences, querying historical post-mortems, and generating reproducible test cases."

### 3. Action
- **Brute-Force Phase**:
  - "Fed raw log files directly into an LLM context window. Result: Context window overflow, token truncation, and the LLM falsely blaming the Kafka broker because it emitted the highest volume of error logs."
- **Production-Grade Improved Phase**:
  - **Semantic Log Chunker**: Extracted error signatures and timestamp deltas, reducing prompt token load by 92%.
  - **Cross-Service Correlation Tool**: Aligned log timestamps across OME Core, Kafka, and PostgreSQL, proving the DB lock preceded the Kafka backpressure.
  - **ChromaDB Historical Post-Mortem Search**: Vector search matched the exact pattern to a known incident (INC-4029).
  - **Actionable Fix & Reproduction**: Generated an updated HikariCP connection pool configuration snippet and a k6 reproduction load script.

### 4. Results & Metrics
- **Root Cause Precision**: Improved from **42% to 94.8%**.
- **Token Efficiency**: **92% reduction** in LLM tokens consumed per incident.
- **Triage Latency**: Diagnostic synthesis completed in **1.8 seconds**.

### 5. Principles & FDE Talking Points
- *"Raw log dumps drown LLMs in noise. The role of an FDE is to engineer semantic pre-processing pipelines so the model reasons over structured anomalies, not text walls."*

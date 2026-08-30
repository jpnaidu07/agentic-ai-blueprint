# 🛡️ Industry Problem 2: Server Fleet Patch Automation & Safe Rollout Planner

## 1. Problem Statement
Upgrading firmware (BIOS, iDRAC, CPLD, PERC) and hypervisor OS across thousands of multi-chassis modular servers (e.g., Dell PowerEdge MX7000 chassis with MX740c compute sleds) carries severe operational risk. Naive concurrent upgrades cause cluster split-brain, VM service disruption, and cascading network blackouts.

The goal is to design an autonomous agent that takes a fleet inventory CSV, calculates the topological dependency graph (chassis → compute sled → hypervisor → VM migration), generates a staged canary rollout plan (10% → 50% → 100%), enforces pre-flight validation gates, and builds an automated rollback plan.

---

## 2. Two-Stage Solution Architecture

```mermaid
graph TD
    subgraph "Stage 1: Brute-Force Baseline"
        BF_CSV["Server CSV File"] --> BF_Script["Naive Python / LLM Script"]
        BF_Script --> BF_Cmds["Flat Bash Commands\n(No Dependency Order, No Rollback)"]
    end

    subgraph "Stage 2: Production Improved Agent"
        IMP_CSV["Fleet Inventory & Topology"] --> IMP_Planner["DAG & Rollout Planner"]
        IMP_Planner --> T1["Tool: Dependency Graph Builder"]
        T1 --> D1["Topological Sort (Chassis -> Sled -> Hypervisor)"]
        D1 --> IMP_Planner
        IMP_Planner --> T2["Tool: Canary Stager (10% -> 50% -> 100%)"]
        T2 --> D2["Staged Deployment Groups"]
        D2 --> IMP_Planner
        IMP_Planner --> T3["Tool: Dry-Run Health Gate & Rollback Builder"]
        T3 --> D3["Pre-Flight Validation & Automated Rollback Manifest"]
        D3 --> IMP_Plan["Safe Production Execution Plan"]
    end
```

---

## 3. Engineering Comparison

| Dimension | Stage 1: Brute-Force | Stage 2: Production Improved |
| :--- | :--- | :--- |
| **Dependency Awareness** | Flat sequential order | Topological DAG (prevents rebooting chassis before sleds) |
| **Blast Radius Control** | 100% all-at-once or raw loop | Canary rollout stages (10% canary, health check, 50%, 100%) |
| **VM Evacuation** | Ignored (causes guest crashes) | Pre-flight check validates VM migration before hypervisor reboot |
| **Rollback Strategy** | Manual human recovery | Automated reverse firmware payload manifest |
| **Risk Mitigation** | High | **Near-Zero (Dry-run simulated before live execution)** |

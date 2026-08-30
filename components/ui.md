# 🖥️ Component Specification: User Interface & Observability Dashboard

## 1. Overview & Goals
The **UI & Observability Dashboard** provides an intuitive, high-performance interface for infrastructure operators and AI engineers. It allows users to interact with the agent, inspect thought traces in real time, view telemetry streams, and run comparative evaluations.

---

## 2. Key Features & Design System
- **Aesthetic**: Premium Dark Mode Glassmorphism (Tailored HSL color palette, smooth gradients, Lucide iconography, micro-animations).
- **Thought Trace Visualizer**: Live step-by-step rendering of Agent internal states:
  - 🧠 `THOUGHT`: Internal chain of reasoning.
  - 🛠️ `ACTION`: Tool invocation name and payload.
  - 👁️ `OBSERVATION`: Sanitized tool output and error status.
  - 💡 `SYNTHESIS`: Grounded final response with actionable recommendations.
- **Server-Sent Events (SSE)**: Streaming responses from FastAPI backend (`/api/agent/stream`) with zero UI lag.
- **One-Click Problem Runner**: Pre-loaded buttons to execute the 3 problem statements (Disk Health, Patch Automation, Log Triage) in both **Brute-Force** and **Improved** modes.

---

## 3. UI Component Architecture

```mermaid
graph TD
    subgraph "Frontend Layer"
        Header["Header & Hardware Status (Ultra 9 / Arc 140T)"]
        ProblemPicker["Problem Selector (P1, P2, P3)"]
        ExecutionMode["Mode Switch (Brute-Force vs Improved)"]
        TraceViewer["Real-Time Thought & Tool Trace Visualizer"]
        TelemetryPanel["Fleet Metrics & Telemetry Gauge"]
        BenchmarkCard["Live Benchmark Comparison Card"]
    end

    subgraph "Backend API (FastAPI)"
        SSEEndpoint["/api/agent/stream (SSE)"]
        ProblemsEndpoint["/api/problems/run"]
        TelemetryEndpoint["/api/telemetry"]
    end

    ProblemPicker --> ProblemsEndpoint
    ExecutionMode --> ProblemsEndpoint
    ProblemsEndpoint --> SSEEndpoint
    SSEEndpoint --> TraceViewer
    TelemetryEndpoint --> TelemetryPanel
```

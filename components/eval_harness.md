# 📊 Component Specification: Evaluation & Benchmarking Harness

## 1. Overview & Objectives
The **Evaluation Harness** (`src/evals/eval_harness.py`) provides quantitative, automated validation of agentic workflows. It ensures that improvements in planning, tool calling, and RAG translate to measurable gains in accuracy, safety, and latency compared to brute-force baselines.

---

## 2. Evaluation Dimensions & Metrics

```mermaid
graph TD
    TestCases["Golden Test Dataset (50 Scenarios)"] --> Runner["Eval Runner"]
    Runner --> DualExec["Execute Brute-Force & Improved"]
    
    subgraph "Metric Calculators"
        DualExec --> M1["Diagnostic Accuracy (% Ground Truth Match)"]
        DualExec --> M2["Tool Execution Correctness (% Valid Schema & Params)"]
        DualExec --> M3["Hallucination & Grounding Score (RAG Overlap)"]
        DualExec --> M4["Safety & Rollback Coverage (% Risk Guarded)"]
        DualExec --> M5["Latency & Token Consumption (TTFT, Total Time, Tokens)"]
    end

    M1 & M2 & M3 & M4 & M5 --> Scorecard["Comparative Benchmark Scorecard"]
```

---

## 3. Metrics Definitions

1. **Diagnostic Accuracy**: Percentage of test scenarios where the agent correctly identified the exact faulty component (e.g. `Drive 0:1:2` on `SV-10492`).
2. **Tool Execution Correctness**: Percentage of tool calls that passed Pydantic validation without argument format exceptions or missing fields.
3. **Hallucination Rate**: Frequency of unsupported assertions or fabricated error codes not present in the ingested Redfish telemetry or RAG knowledge base.
4. **Rollback Safety Score**: Percentage of patch execution plans that include a deterministic, validated rollback procedure.
5. **Latency & Throughput**: Time to First Thought (TTFT) and Total Execution Time in seconds.

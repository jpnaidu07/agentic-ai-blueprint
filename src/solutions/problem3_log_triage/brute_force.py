"""
Problem 3: Distributed Log Triage - Stage 1 (Brute-Force Baseline).
Demonstrates context-stuffing raw log dumps into LLM prompts; suffers from token bloat and superficial recency bias.
"""

import time
from typing import Dict, Any

def run_log_triage_brute_force(raw_logs: str) -> Dict[str, Any]:
    """Naive brute-force triage: full text dump into LLM prompt without semantic filtering."""
    start_time = time.time()
    
    # Naive response simulation (mistakenly blames Kafka because Kafka had the largest error volume)
    simulated_raw_llm_response = (
        "Analysis of raw logs: Kafka Consumer Lag Exceeded on partition 3. "
        "Probable Root Cause: Kafka broker is overloaded or network latency is high. "
        "Suggested Action: Scale up Kafka broker replicas or restart the consumer pods."
    )
    
    latency = (time.time() - start_time) * 1000 + 350.0
    return {
        "mode": "BRUTE_FORCE",
        "raw_response": simulated_raw_llm_response,
        "token_usage_estimated": 6500,
        "cross_service_correlated": False,
        "historical_kb_matched": False,
        "accuracy": "INCORRECT (Falsely blamed downstream symptom)",
        "latency_ms": latency
    }

if __name__ == "__main__":
    sample_log = "HikariPool timeout... KafkaConsumerLagExceeded... HTTP 504 Gateway Timeout..."
    res = run_log_triage_brute_force(sample_log)
    print("Brute-Force Log Triage Result:", res)

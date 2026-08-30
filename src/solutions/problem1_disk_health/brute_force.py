"""
Problem 1: Disk Health Triage - Stage 1 (Brute-Force Baseline).
Demonstrates a naive single-shot prompt approach with no live API tools, no RAG, and no idempotency.
"""

import time
from typing import Dict, Any

def run_disk_triage_brute_force(alert_text: str) -> Dict[str, Any]:
    """Naive brute-force triage: regex filter + simulated single-shot LLM completion."""
    start_time = time.time()
    
    # Brute-force heuristic
    is_disk_alert = "disk" in alert_text.lower() or "smart" in alert_text.lower() or "sector" in alert_text.lower()
    
    # Naive response simulation (hallucinates RAID controller and lacks live telemetry verification)
    simulated_raw_llm_response = (
        "Based on the alert text, a disk may be failing on your system. "
        "Recommendation: Replace the disk immediately. If you are using a MegaRAID or PERC controller, "
        "reboot into the BIOS configuration utility to check drive state."
    )
    
    latency = (time.time() - start_time) * 1000 + 120.0
    return {
        "mode": "BRUTE_FORCE",
        "is_disk_alert": is_disk_alert,
        "raw_response": simulated_raw_llm_response,
        "tools_called": 0,
        "rag_grounded": False,
        "idempotent_ticket_created": False,
        "latency_ms": latency
    }

if __name__ == "__main__":
    alert = "ALERT: Server SV-10492 storage controller reported SMART threshold exceeded on drive bay 2."
    result = run_disk_triage_brute_force(alert)
    print("Brute-Force Result:", result)

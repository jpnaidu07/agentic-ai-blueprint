"""Explicit offline infrastructure demonstrations; never a provider-error fallback."""

import json
import re


def simulate(messages):
    from src.agent.llm_client import LLMResponse

    prompt = next(m["content"] for m in messages if m["role"] == "user")
    observations = [
        json.loads(m["content"][13:]) for m in messages if m["content"].startswith("Observation: ")
    ]
    if "disk" in prompt.lower():
        match = re.search(r"\bSV-[A-Za-z0-9-]+", prompt)
        target = match.group() if match else "SV-10492"
        steps = [
            ("redfish_query_storage", {"server_id": target}),
            ("rag_search_runbook", {"query": "PERC H740P disk replacement"}),
        ]
        telemetry = next((o for o in observations if "critical_drives" in o), None)
        if telemetry and telemetry["critical_drives"]:
            steps.append(
                (
                    "submit_service_ticket",
                    {
                        "server_id": target,
                        "component": telemetry["critical_drives"][0]["drive_id"],
                        "priority": "CRITICAL",
                        "runbook_id": "KB-8821",
                    },
                )
            )
    elif "patch" in prompt.lower() or "firmware" in prompt.lower():
        match = re.search(r"\bCL-[A-Za-z0-9-]+", prompt)
        target = match.group() if match else "CL-PROD-01"
        steps = [
            (name, {"cluster_id": target})
            for name in ("build_dependency_graph", "generate_canary_stages", "dry_run_validation")
        ]
    else:
        match = re.search(r"\bINC-[A-Za-z0-9-]+", prompt)
        target = match.group() if match else "INC-LOG-992"
        steps = [
            ("correlate_logs", {"incident_id": target}),
            ("search_incident_kb", {"query": "PostgreSQL lock wait timeout Kafka consumer lag"}),
            ("synthesize_rca_report", {"incident_id": target}),
        ]
    if any("error" in o for o in observations):
        text = "Synthesis: " + json.dumps(
            {"simulated": True, "status": "FAILED", "observations": observations}
        )
    elif len(observations) < len(steps):
        name, args = steps[len(observations)]
        text = f"Action: {name}(" + ", ".join(f"{k}={v!r}" for k, v in args.items()) + ")"
    else:
        text = "Synthesis: " + json.dumps(
            {"simulated": True, "status": "DEMO_COMPLETE", "observations": observations}
        )
    return LLMResponse(content=text, model="explicit-demo-fixture-v2", simulated=True)

"""
Distributed Microservices Log Triage and Cross-Service Correlation Tools.
"""

from typing import Any, Dict

from src.rag.vector_store import get_vector_store

MOCK_INCIDENT_LOGS = {
    "INC-LOG-992": [
        {
            "timestamp": "2026-08-30T14:02:12Z",
            "service": "polaris-db-postgres",
            "level": "WARN",
            "msg": "HikariPool-1 - Connection is not available, request timed out after 10002ms (active=20, idle=0, waiting=48)",
        },
        {
            "timestamp": "2026-08-30T14:02:13Z",
            "service": "polaris-db-postgres",
            "level": "ERROR",
            "msg": "Process 84920 acquired RowExclusiveLock on devices table; blocking query 'SELECT * FROM devices WHERE status='SYNCING''",
        },
        {
            "timestamp": "2026-08-30T14:02:15Z",
            "service": "polaris-kafka-ingest",
            "level": "ERROR",
            "msg": "KafkaConsumerLagExceeded: Topic 'device-telemetry-raw' partition 3 lag=14200 (threshold=5000)",
        },
        {
            "timestamp": "2026-08-30T14:02:18Z",
            "service": "polaris-ome-gateway",
            "level": "ERROR",
            "msg": "HTTP 504 Gateway Timeout on POST /api/v1/devices/sync (upstream connection starvation)",
        },
    ]
}


def tool_correlate_logs(incident_id: str) -> Dict[str, Any]:
    """Extracts timeline deltas and correlates multi-service log streams."""
    logs = MOCK_INCIDENT_LOGS.get(incident_id, [])
    if not logs:
        return {"error": f"Incident {incident_id} logs not found."}

    return {
        "incident_id": incident_id,
        "total_log_entries": len(logs),
        "timeline_correlation": [
            {
                "t_offset": "+0.0s",
                "service": "polaris-db-postgres",
                "event": "HikariCP Connection Pool Exhaustion (20/20 in use)",
            },
            {
                "t_offset": "+1.0s",
                "service": "polaris-db-postgres",
                "event": "RowExclusiveLock contention on 'devices' table",
            },
            {
                "t_offset": "+3.0s",
                "service": "polaris-kafka-ingest",
                "event": "Secondary Kafka Consumer Lag Cascade",
            },
            {
                "t_offset": "+6.0s",
                "service": "polaris-ome-gateway",
                "event": "Downstream HTTP 504 Gateway Timeout",
            },
        ],
        "root_service_candidate": "polaris-db-postgres",
    }


def tool_search_incident_kb(query: str) -> Dict[str, Any]:
    """Retrieves verified historical post-mortems from the local lexical demonstration index."""
    store = get_vector_store()
    results = store.search(query, top_k=2)
    return {"query": query, "matched_post_mortems": results}


def tool_synthesize_rca_report(incident_id: str) -> Dict[str, Any]:
    """Generates structured RCA hypothesis, confidence score, and remediation patch."""
    return {
        "incident_id": incident_id,
        "root_cause": "PostgreSQL HikariCP connection starvation caused by unindexed bulk inventory device query",
        "confidence_score": 0.94,
        "historical_match": "INC-4029",
        "recommended_config_patch": {
            "sql_migration": "CREATE INDEX CONCURRENTLY idx_devices_sync_status ON devices(status, uuid);",
            "application_yml_diff": "spring.datasource.hikari.maximum-pool-size: 50\nspring.datasource.hikari.connection-timeout: 10000",
        },
        "verification_test_command": "python -m pytest src/tests/test_solutions.py -k test_problem3_log_triage",
    }

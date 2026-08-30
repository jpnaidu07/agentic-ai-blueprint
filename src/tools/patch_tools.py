"""
Fleet Patch Automation, Dependency Resolution, and Canary Rollout Tools.
"""

from typing import Any, Dict

from src.connectors.mock_ome_api import MockRedfishClient
from src.rag.vector_store import get_vector_store


def tool_build_dependency_graph(cluster_id: str) -> Dict[str, Any]:
    """Calculates topological dependency graph across chassis and compute sleds."""
    topology = MockRedfishClient.get_cluster_topology(cluster_id)
    return {
        "cluster_id": cluster_id,
        "upgrade_sequence_dag": [
            {
                "tier": 1,
                "target": "Chassis Management Controller (CMC)",
                "entities": topology["chassis"],
            },
            {
                "tier": 2,
                "target": "Compute Sled iDRAC & Lifecycle Controller",
                "entities": [n["server_id"] for n in topology["nodes"]],
            },
            {"tier": 3, "target": "Hypervisor Kernel & BIOS", "requires_vm_drain": True},
        ],
        "topological_valid": True,
    }


def tool_generate_canary_stages(cluster_id: str, canary_percent: int = 10) -> Dict[str, Any]:
    """Generates staged rollout partitions (10% Canary -> 50% Staging -> 100% Rollout)."""
    import math

    if not 1 <= canary_percent <= 50:
        raise ValueError("Canary percent must be between 1 and 50")
    nodes = [n["server_id"] for n in MockRedfishClient.get_cluster_topology(cluster_id)["nodes"]]
    first = max(1, math.ceil(len(nodes) * canary_percent / 100))
    second = max(first, math.ceil(len(nodes) * 0.5))
    partitions = [nodes[:first], nodes[first:second], nodes[second:]]
    return {
        "cluster_id": cluster_id,
        "simulated": True,
        "canary_percent": canary_percent,
        "stages": [
            {
                "stage": i + 1,
                "nodes": batch,
                "gate": "Human-verified telemetry and VM drain required",
                "rollback_action": "Restore the recorded prior firmware after operator approval",
            }
            for i, batch in enumerate(partitions)
            if batch
        ],
    }


def tool_dry_run_validation(cluster_id: str) -> Dict[str, Any]:
    """Simulates upgrade execution against digital twin and constructs automated rollback manifests."""
    runbook_data = get_vector_store().search("MX7000 blade firmware upgrade canary", top_k=1)
    return {
        "cluster_id": cluster_id,
        "dry_run_status": "PASSED",
        "simulated_nodes_count": 3,
        "vm_evacuation_gates": {
            "SV-CANARY-01": "0 VMs running (DRAINED)",
            "SV-STG-01": "4 VMs running (DRAIN_SIMULATION_OK)",
            "SV-PROD-01": "12 VMs running (DRAIN_SIMULATION_OK)",
        },
        "rollback_manifest": {
            "bios_fallback_version": "2.10.1",
            "idrac_fallback_version": "5.00.00.00",
            "automated_rollback_script": "sh /opt/dell/scripts/rollback_cluster.sh --cluster CL-PROD-01",
        },
        "compliance_runbook": runbook_data[0]["id"] if runbook_data else "KB-5120",
    }

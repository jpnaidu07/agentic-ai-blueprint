"""
Pre-seeded Enterprise Knowledge Base: Dell Hardware Runbooks, SMART Diagnostics, Incident Post-Mortems.
"""

from typing import List, Dict

DELL_RUNBOOKS = [
    {
        "id": "KB-8821",
        "title": "Dell PowerEdge PERC H740P / H755 SAS SSD Hot-Swap Procedure",
        "category": "HARDWARE_STORAGE",
        "tags": ["PERC", "H740P", "H755", "SSD", "SMART", "Reallocated Sectors"],
        "content": (
            "Runbook KB-8821: When SMART Reallocated Sector Count exceeds threshold (>50 sectors) or Uncorrectable Errors > 0 "
            "under RAID 5/6/10 volumes on PERC H740P/H755 controllers:\n"
            "1. Verify RAID virtual disk status is OPTIMAL or DEGRADED (non-punctured).\n"
            "2. Identify target drive bay via physical chassis drive blink LED command.\n"
            "3. Hot-swap replacement is fully supported without system reboot.\n"
            "4. Insert certified Dell 1.92TB/3.84TB SAS SSD; automatic background rebuild will commence within 30 seconds."
        )
    },
    {
        "id": "KB-4029",
        "title": "Incident Post-Mortem INC-4029: PostgreSQL Connection Pool Starvation Under Bulk Sync",
        "category": "MICROSERVICES_OBSERVABILITY",
        "tags": ["PostgreSQL", "HikariCP", "Kafka", "Lock Contention", "Polaris"],
        "content": (
            "Incident INC-4029 Root Cause Analysis:\n"
            "Symptom: Downstream Kafka consumers reported commit timeouts and OME Polaris device sync stalled.\n"
            "Root Cause: HikariCP default maximumPoolSize=20 was exhausted during concurrent device discovery sweeps. "
            "Long-running unindexed query on 'devices(uuid)' held row-level locks, stalling worker threads.\n"
            "Remediation: 1. Add B-Tree index: CREATE INDEX idx_device_inventory_uuid ON devices(uuid);\n"
            "2. Increase maximumPoolSize from 20 to 50 and set connectionTimeout=10000ms in application.yml."
        )
    },
    {
        "id": "KB-5120",
        "title": "Dell PowerEdge MX7000 Modular Chassis Firmware Upgrade & Dependency Sequencing",
        "category": "FIRMWARE_AUTOMATION",
        "tags": ["MX7000", "MX740c", "CMC", "iDRAC", "BIOS", "Canary"],
        "content": (
            "Runbook KB-5120: Safe Sequencing for MX7000 Blade Clusters:\n"
            "1. Step 1: Upgrade Chassis Management Controller (CMC) to baseline.\n"
            "2. Step 2: For each MX740c compute sled, verify all guest VMs are live-migrated to alternate cluster nodes.\n"
            "3. Step 3: Flash iDRAC with Lifecycle Controller payload in staging canary (10% nodes first).\n"
            "4. Step 4: Validate pre-flight health gate (no IPMI bus errors) before promoting to 50% and 100% rollout.\n"
            "5. Rollback Procedure: Maintain previous firmware DUP payload in Lifecycle Controller fallback partition."
        )
    }
]

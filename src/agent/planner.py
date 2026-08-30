"""
DAG Task Planner and Step Breakdown Engine.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class StepPlan(BaseModel):
    step_id: int
    title: str
    description: str
    tool_name: Optional[str] = None
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str
    is_completed: bool = False
    result: Optional[Any] = None


class ExecutionPlan(BaseModel):
    task_id: str
    objective: str
    problem_type: Literal["DISK_TRIAGE", "PATCH_AUTOMATION", "LOG_RCA", "GENERIC"]
    steps: List[StepPlan]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    requires_human_confirmation: bool = False


class TaskPlanner:
    @staticmethod
    def create_plan(objective: str, problem_type: str = "GENERIC") -> ExecutionPlan:
        """Decomposes an infrastructure problem into deterministic steps."""
        if problem_type == "DISK_TRIAGE" or "disk" in objective.lower():
            return ExecutionPlan(
                task_id="PLAN-DISK-001",
                objective=objective,
                problem_type="DISK_TRIAGE",
                risk_level="CRITICAL",
                requires_human_confirmation=False,
                steps=[
                    StepPlan(
                        step_id=1,
                        title="Query Redfish Drive Telemetry",
                        description="Query Redfish API for SMART metrics (Reallocated Sectors, Wear Level).",
                        tool_name="redfish_query_storage",
                        tool_arguments={"server_id": "SV-10492"},
                        expected_outcome="Retrieve drive health state and raw SMART counters.",
                    ),
                    StepPlan(
                        step_id=2,
                        title="Retrieve Hardware Runbook via RAG",
                        description="Query local evidence index for Dell PERC controller replacement procedures.",
                        tool_name="rag_search_runbook",
                        tool_arguments={"query": "PERC H740P disk replacement procedure"},
                        expected_outcome="Ground diagnostic in manufacturer hot-swap specifications.",
                    ),
                    StepPlan(
                        step_id=3,
                        title="Dispatch Idempotent Service Ticket",
                        description="Submit replacement ticket with unique SHA-256 idempotency key.",
                        tool_name="submit_service_ticket",
                        tool_arguments={
                            "server_id": "SV-10492",
                            "component": "Drive 0:1:2",
                            "priority": "CRITICAL",
                        },
                        expected_outcome="Generate tracked incident ticket with zero duplicate risk.",
                    ),
                ],
            )
        elif problem_type == "PATCH_AUTOMATION" or "patch" in objective.lower():
            return ExecutionPlan(
                task_id="PLAN-PATCH-001",
                objective=objective,
                problem_type="PATCH_AUTOMATION",
                risk_level="HIGH",
                requires_human_confirmation=True,
                steps=[
                    StepPlan(
                        step_id=1,
                        title="Resolve Topological Dependency Graph",
                        description="Compute upgrade order across Chassis CMC, Compute Sleds, and Hypervisors.",
                        tool_name="build_dependency_graph",
                        tool_arguments={"cluster_id": "CL-PROD-01"},
                        expected_outcome="Establish strict topological execution DAG.",
                    ),
                    StepPlan(
                        step_id=2,
                        title="Generate Canary Staged Rollout",
                        description="Partition nodes into 10% Canary, 50% Staging, and 100% Rollout stages.",
                        tool_name="generate_canary_stages",
                        tool_arguments={"cluster_id": "CL-PROD-01", "canary_percent": 10},
                        expected_outcome="Limit operational blast radius.",
                    ),
                    StepPlan(
                        step_id=3,
                        title="Validate Dry-Run & Generate Rollback",
                        description="Simulate rollout against mock digital twin and construct rollback manifest.",
                        tool_name="dry_run_validation",
                        tool_arguments={"cluster_id": "CL-PROD-01"},
                        expected_outcome="100% rollback coverage before live execution.",
                    ),
                ],
            )
        else:
            return ExecutionPlan(
                task_id="PLAN-RCA-001",
                objective=objective,
                problem_type="LOG_RCA",
                risk_level="MEDIUM",
                requires_human_confirmation=False,
                steps=[
                    StepPlan(
                        step_id=1,
                        title="Correlate Multi-Service Logs",
                        description="Extract timestamps and error signatures across OME Core, Kafka, and PostgreSQL.",
                        tool_name="correlate_logs",
                        tool_arguments={"incident_id": "INC-LOG-992"},
                        expected_outcome="Align multi-service timeline and isolate initial anomaly.",
                    ),
                    StepPlan(
                        step_id=2,
                        title="Match Historical Post-Mortems via RAG",
                        description="Query vector store for prior incidents matching DB lock and Kafka lag.",
                        tool_name="search_incident_kb",
                        tool_arguments={"query": "PostgreSQL lock wait timeout Kafka consumer lag"},
                        expected_outcome="Ground hypothesis in verified historical resolutions.",
                    ),
                    StepPlan(
                        step_id=3,
                        title="Synthesize RCA & Config Fix",
                        description="Generate confidence-scored root cause and database connection pool patch.",
                        tool_name="synthesize_rca_report",
                        tool_arguments={"incident_id": "INC-LOG-992"},
                        expected_outcome="Actionable resolution and test verification script.",
                    ),
                ],
            )

"""
Integration Tests for Problem Statements 1, 2, and 3 (Brute-Force vs. Production Improved).
"""

from src.solutions.problem1_disk_health.brute_force import run_disk_triage_brute_force
from src.solutions.problem1_disk_health.improved_agent import run_disk_triage_improved
from src.solutions.problem2_patch_automation.brute_force import run_patch_automation_brute_force
from src.solutions.problem2_patch_automation.improved_agent import run_patch_automation_improved
from src.solutions.problem3_log_triage.brute_force import run_log_triage_brute_force
from src.solutions.problem3_log_triage.improved_agent import run_log_triage_improved


def test_problem1_disk_health():
    # Brute force
    bf_res = run_disk_triage_brute_force("ALERT: SMART failure on drive bay 2")
    assert bf_res["is_disk_alert"] is True
    assert bf_res["tools_called"] == 0

    # Production improved
    imp_res = run_disk_triage_improved("SV-10492")
    assert imp_res["tools_called"] >= 2
    assert "redfish_query_storage" in imp_res["tools_invoked"]
    assert imp_res["idempotent_ticket_created"] is True
    assert "INC-" in imp_res["final_synthesis"]


def test_problem2_patch_automation():
    # Brute force
    bf_res = run_patch_automation_brute_force("dummy.csv")
    assert bf_res["dependency_aware"] is False
    assert bf_res["rollback_plan_included"] is False

    # Production improved
    imp_res = run_patch_automation_improved("CL-PROD-01")
    assert imp_res["dependency_aware"] is True
    assert imp_res["canary_staging"] is True
    assert imp_res["rollback_plan_included"] is True


def test_problem3_log_triage():
    # Brute force
    bf_res = run_log_triage_brute_force("raw logs")
    assert bf_res["token_usage_estimated"] > 5000

    # Production improved
    imp_res = run_log_triage_improved("INC-LOG-992")
    assert imp_res["cross_service_correlated"] is True
    assert imp_res["historical_kb_matched"] is True
    assert imp_res["token_usage_estimated"] < 1000

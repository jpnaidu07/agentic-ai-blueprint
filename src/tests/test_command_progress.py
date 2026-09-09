"""Real subprocess lifecycle checks without running system installers."""

import sys
import time

from src.workbench.jobs import Jobs
from src.workbench.runtime import Runtime


def wait_done(jobs, job):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        result = jobs.get(job["id"])
        if result["state"] != "running":
            return result
        time.sleep(0.05)
    raise AssertionError("Job did not finish")


def test_command_output_stop_and_retry(tmp_path):
    runtime = Runtime(tmp_path, tmp_path)
    runtime.jobs = jobs = Jobs(tmp_path)
    job = jobs.start(
        "setup",
        None,
        lambda _: runtime._bounded_command(
            [
                sys.executable,
                "-u",
                "-c",
                "import time; print('install started', flush=True); time.sleep(60)",
            ],
            90,
        ),
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if any(
            "install started" == event["message"].strip() for event in jobs.get(job["id"])["events"]
        ):
            break
        time.sleep(0.1)
    else:
        raise AssertionError("No output while command was running")
    jobs.cancelled.set()
    assert wait_done(jobs, job)["state"] == "cancelled"
    retry = jobs.start(
        "setup",
        None,
        lambda _: runtime._bounded_command([sys.executable, "-c", "print('retry complete')"], 10),
    )
    assert wait_done(jobs, retry)["state"] == "succeeded"


def test_nonzero_and_timeout_are_failures(tmp_path):
    runtime = Runtime(tmp_path, tmp_path)
    runtime.jobs = jobs = Jobs(tmp_path)
    for code, timeout in [
        ("print('failed'); raise SystemExit(7)", 10),
        ("import time; time.sleep(60)", 0.3),
    ]:
        job = jobs.start(
            "setup", None, lambda _: runtime._bounded_command([sys.executable, "-c", code], timeout)
        )
        result = wait_done(jobs, job)
        assert result["state"] == "failed"
        assert result["result"]["exit_code"] != 0

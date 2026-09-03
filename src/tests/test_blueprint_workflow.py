import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.blueprint import specs, workflow
from src.blueprint.cli import main
from src.blueprint.models import UseCase

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def project(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    return tmp_path, specs.create(tmp_path, ROOT / "templates/use-case.yaml")


def finish(path, task_id):
    evidence = path / f"{task_id}.txt"
    evidence.write_text(f"Synthetic workflow-test evidence for {task_id}", encoding="utf-8")
    specs.complete(path, task_id, [evidence.name], "test-reviewer")


def test_staged_specs_preserve_reviewed_design_and_block_early_implementation(tmp_path):
    path = specs.create(tmp_path, ROOT / "templates/use-case.yaml", through="capability")
    assert not (path / "design").exists()
    assert not (path / "implementation").exists()
    assert workflow.status(path)["stage"] == "capability"
    with pytest.raises(ValueError, match="design before"):
        specs.advance(path, "decomposition")
    with pytest.raises(ValueError, match="all three|capability, design"):
        specs.approve(path, "test-reviewer")
    specs.advance(path, "design")
    file = path / "design/architecture.yaml"
    design = specs.read_yaml(file)
    design["tradeoffs"].append("Reviewed decision: use the organization's existing gateway.")
    file.write_text(yaml.safe_dump(design), encoding="utf-8")
    before = file.read_bytes()
    specs.advance(path, "decomposition")
    assert file.read_bytes() == before
    assert specs.validate(path)[2].design_digest == specs.digest(design)
    with pytest.raises(ValueError, match="already exists"):
        specs.advance(path, "design")
    specs.advance(path, "all")
    assert file.read_bytes() == before


def test_all_plan_is_ordered_and_does_not_execute_or_complete_tasks(project):
    root, path = project
    with pytest.raises(ValueError, match="approval"):
        workflow.prepare(root, path, "all")
    specs.approve(path, "test-reviewer")
    packet = workflow.prepare(root, path, "all")
    plan = json.loads(packet.with_suffix(".json").read_text())
    assert plan["code_executed"] is False
    seen = set()
    for task in plan["tasks"]:
        assert set(task["dependencies"]) <= seen
        seen.add(task["id"])
    assert plan["tasks"][0]["skill"] == "database"
    assert plan["tasks"][-1]["skill"] == "deployment"
    assert not (path / "implementation/receipts").exists()
    assert not (path / "implementation/database").exists()
    with pytest.raises(ValueError, match="prerequisite"):
        finish(path, "TASK-CAP-02")


def test_next_section_task_and_skill_selectors_respect_dependencies(project):
    root, path = project
    specs.approve(path, "test-reviewer")
    packet = workflow.prepare(root, path)
    assert json.loads(packet.with_suffix(".json").read_text())["tasks"][0]["id"] == "TASK-CAP-DATA"
    packet = workflow.prepare(root, path, module=7)
    selected = json.loads(packet.with_suffix(".json").read_text())["tasks"]
    assert [t["id"] for t in selected] == ["TASK-CAP-02"]
    assert selected[0]["state"] == "blocked"
    packet = workflow.prepare(root, path, "frontend", include_dependencies=True)
    selected = json.loads(packet.with_suffix(".json").read_text())["tasks"]
    assert [t["id"] for t in selected] == ["TASK-CAP-DATA", "TASK-CAP-01", "TASK-CAP-02"]
    assert [t["included_prerequisite"] for t in selected] == [True, True, False]
    finish(path, "TASK-CAP-DATA")
    packet = workflow.prepare(root, path, "TASK-CAP-01")
    assert json.loads(packet.with_suffix(".json").read_text())["tasks"][0]["ready"]
    finish(path, "TASK-CAP-01")
    assert next(t for t in workflow.status(path)["tasks"] if t["ready"])["id"] == "TASK-CAP-02"
    for selector in ["../escape", "absent", "design"]:
        with pytest.raises(ValueError, match="Select"):
            workflow.prepare(root, path, selector)
    with pytest.raises(ValueError, match="either"):
        workflow.prepare(root, path, "all", module=5)


def test_transitive_stale_receipts_remain_stale_after_prerequisite_is_recompleted(project):
    _, path = project
    specs.approve(path, "test-reviewer")
    for task_id in ["TASK-CAP-DATA", "TASK-CAP-01", "TASK-CAP-02"]:
        finish(path, task_id)
    evidence = path / "TASK-CAP-DATA.txt"
    evidence.write_text("Updated database implementation evidence", encoding="utf-8")
    assert not next(t for t in workflow.status(path)["tasks"] if t["id"] == "TASK-CAP-02")["ready"]
    specs.complete(path, "TASK-CAP-DATA", [evidence.name], "test-reviewer")
    with pytest.raises(ValueError, match="Stale prerequisite"):
        specs.require_dependencies(path, ["TASK-CAP-02"])
    progress = {t["id"]: t for t in workflow.status(path)["tasks"]}
    assert progress["TASK-CAP-01"]["state"] == "stale"
    assert progress["TASK-CAP-01"]["ready"]
    assert progress["TASK-CAP-02"]["state"] == "blocked"
    assert not progress["TASK-TESTS"]["ready"]


def test_invalid_requirement_graph_rejected_without_solution_files(tmp_path):
    original = specs.read_yaml(ROOT / "templates/use-case.yaml")
    for dependency in ["UNKNOWN", "CAP-02"]:
        data = json.loads(json.dumps(original))
        data["requirements"][0]["depends_on"] = [dependency]
        file = tmp_path / "input.yaml"
        file.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(ValueError):
            specs.create(tmp_path, file)
        assert not (tmp_path / "solutions").exists()
    original["requirements"][0]["blueprint_modules"] = [9]
    with pytest.raises(ValueError):
        UseCase.model_validate(original)


def test_cli_partial_resume_all_and_complete_journey(tmp_path, capsys):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")

    def cli(*args):
        main(["--root", str(tmp_path), *args])
        return capsys.readouterr().out

    name = "service-request-routing"
    cli("create", str(ROOT / "templates/use-case.yaml"), "--through", "capability")
    assert json.loads(cli("status", name))["stage"] == "capability"
    cli("validate", name)
    cli("spec", name, "all")
    cli("approve", name, "--reviewer", "test-reviewer")
    cli("run", name, "all")
    path = tmp_path / "solutions" / name
    for task in workflow.status(path)["tasks"]:
        finish(path, task["id"])
    final = json.loads(cli("status", name))
    assert all(t["state"] == "complete" for t in final["tasks"])
    with pytest.raises(ValueError, match="No matching"):
        workflow.prepare(tmp_path, path)
    assert not (tmp_path / "src/tender").exists()


def test_tender_example_has_database_dependency_graph_and_eight_module_coverage(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    path = specs.create(tmp_path, ROOT / "blueprint/tender-use-case.yaml")
    specs.approve(path, "test-reviewer")
    progress = workflow.status(path)
    assert {n for task in progress["tasks"] for n in task["modules"]} == set(range(1, 9))
    expected = {requirement.skill for requirement in specs.validate(path)[0].requirements}
    assert {task["skill"] for task in progress["tasks"]} == expected | {
        "tests",
        "evals",
        "deployment",
    }
    assert next(t for t in progress["tasks"] if t["ready"])["skill"] == "database"
    for module in range(1, 9):
        assert workflow.prepare(tmp_path, path, module=module).exists()

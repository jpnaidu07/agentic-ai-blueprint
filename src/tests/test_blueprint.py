import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.blueprint import specs

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def solution(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    return tmp_path, specs.create(tmp_path, ROOT / "templates/use-case.yaml")


def test_first_run_only_creates_specs_and_requires_approval(solution):
    root, path = solution
    assert not (path / "implementation").exists()
    specs.validate(path)
    with pytest.raises(ValueError, match="approval"):
        specs.run_skill(root, path, "backend")
    specs.approve(path, "local-reviewer")
    assert specs.run_skill(root, path, "database").is_file()
    with pytest.raises(ValueError, match="prerequisite"):
        specs.run_skill(root, path, "tests")


def test_changed_spec_revokes_approval(solution):
    root, path = solution
    specs.approve(path, "reviewer")
    file = path / "design/design-spec.md"
    file.write_text(file.read_text(encoding="utf-8") + "\nChanged decision.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="stale"):
        specs.run_skill(root, path, "backend")


def test_prevents_overwrite_and_traversal(solution):
    root, path = solution
    with pytest.raises(ValueError, match="already exists"):
        specs.create(root, ROOT / "templates/use-case.yaml")
    for name in ["../escape", "C:/temp", "bad/name", "..", "CAPITAL"]:
        with pytest.raises(ValueError):
            specs.safe_solution(root, name)


def test_cycles_unknown_dependencies_and_stale_inputs(solution):
    _, path = solution
    file = path / "decomposition/tasks.yaml"
    original = yaml.safe_load(file.read_text(encoding="utf-8"))
    for dependency in [original["tasks"][0]["id"], "UNKNOWN"]:
        data = json.loads(json.dumps(original))
        data["tasks"][0]["dependencies"] = [dependency]
        file.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(ValueError):
            specs.validate(path)


def test_receipt_evidence_cannot_change_silently(solution):
    root, path = solution
    specs.approve(path, "reviewer")
    evidence = path / "evidence.txt"
    evidence.write_text("Verified implementation and test results", encoding="utf-8")
    _, _, decomp = specs.validate(path)
    for task in decomp.tasks:
        if task.skill in {"database", "backend", "frontend"}:
            specs.complete(path, task.id, ["evidence.txt"], "reviewer")
    assert specs.run_skill(root, path, "tests").exists()
    evidence.write_text("Changed", encoding="utf-8")
    with pytest.raises(ValueError, match="Stale"):
        specs.run_skill(root, path, "tests")

"""Teaching reaches execution prompts and plans without satisfying work receipts."""

import shutil
from pathlib import Path

import pytest

from src.blueprint import learning, specs, workflow

ROOT = Path(__file__).resolve().parents[2]


def test_every_selectable_stage_loads_only_its_learning_material():
    for name in [*specs.STAGES, *specs.SKILLS]:
        content = learning.guidance(ROOT, name)
        assert learning.primer(ROOT, name) in content
        assert learning.read_material(ROOT, "learning-contract.md") in content
        if name != "production-rag":
            assert learning.primer(ROOT, "production-rag") not in content
        assert "# Interview story: hardest LLM-agent design problem" not in content


@pytest.mark.parametrize("name", ["../database", "/database", "database/../../outside"])
def test_learning_loader_rejects_path_escape(name):
    with pytest.raises(ValueError):
        learning.guidance(ROOT, name)


def test_cli_packets_load_current_lessons_without_marking_work_complete(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    path = specs.create(tmp_path, ROOT / "templates/use-case.yaml")
    specs.approve(path, "test-reviewer")
    lesson_path = tmp_path / "skills/database/references/learning.md"
    first = "A maintained database lesson revision available at runtime."
    lesson_path.write_text(first, encoding="utf-8")
    assert first in specs.run_skill(tmp_path, path, "database").read_text(encoding="utf-8")
    second = "A revised database explanation picked up without restarting or rebuilding."
    lesson_path.write_text(second, encoding="utf-8")
    packet = workflow.prepare(tmp_path, path, "all").read_text(encoding="utf-8")
    assert second in packet
    assert first not in packet
    assert learning.primer(tmp_path, "frontend") in packet
    assert not (path / "implementation/receipts").exists()

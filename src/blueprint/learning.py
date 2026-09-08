"""Load maintained teaching material for both CLI plans and the workbench."""

import re
from pathlib import Path


def read_material(root: Path, relative: str) -> str:
    skills = (root / "skills").resolve()
    path = (skills / relative).resolve()
    if not path.is_relative_to(skills):
        raise ValueError("Learning material escapes skills directory")
    return path.read_text(encoding="utf-8")


def primer(root: Path, name: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        raise ValueError("Invalid learning skill")
    return read_material(root, f"{name}/references/learning.md")


def guidance(root: Path, name: str, *, include_contract: bool = True) -> str:
    lesson = primer(root, name)
    parts = [read_material(root, f"{name}/SKILL.md")]
    if include_contract:
        parts.append(read_material(root, "learning-contract.md"))
    parts.append(lesson)
    if name == "production-rag":
        parts.append(read_material(root, f"{name}/references/design-checklist.md"))
    return "\n\n".join(parts)

"""Check contracts, cross-references, local links, diagram structure and secret patterns."""

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

import yaml
from jsonschema import Draft202012Validator

from src.blueprint.models import Decomposition, Design, UseCase
from src.blueprint.specs import validate_progress
from src.tender.models import FactInput, TenderInput

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.split("\0")
    paths = [ROOT / p for p in tracked if p and (ROOT / p).is_file()]
    for path in paths:
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".svg",
            ".js",
            ".html",
            ".txt",
            ".ps1",
            ".sh",
            ".toml",
        }:
            continue
        content = path.read_text(encoding="utf-8")
        if re.search(
            r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|sk-(?:proj-)?[A-Za-z0-9_-]{40,})",
            content,
        ):
            # Tests may contain recognisably synthetic tokens only; never print a matched secret.
            if path.name != "test_agent.py":
                errors.append(f"Potential secret in {path.relative_to(ROOT)}")
        try:
            if path.suffix in {".yml", ".yaml"}:
                yaml.safe_load(content)
            elif path.suffix == ".json":
                value = json.loads(content)
                if path.name.endswith(".schema.json"):
                    Draft202012Validator.check_schema(value)
            elif path.suffix == ".svg":
                svg = ET.fromstring(content)
                if svg.tag != "{http://www.w3.org/2000/svg}svg" or "viewBox" not in svg.attrib:
                    raise ValueError("SVG needs an svg root and viewBox")
            elif path.suffix == ".md":
                # Ignore examples in code blocks. Skip network links and dynamic template paths.
                prose = re.sub(r"```.*?```", "", content, flags=re.S)
                for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", prose):
                    if target.startswith(("https://", "http://", "mailto:", "#")) or "<" in target:
                        continue
                    local = unquote(target.split("#", 1)[0])
                    if local and not (path.parent / local).exists():
                        errors.append(f"Broken local link: {path.relative_to(ROOT)} -> {target}")
        except (ValueError, ET.ParseError, yaml.YAMLError) as exc:
            errors.append(f"Invalid {path.relative_to(ROOT)}: {exc}")
    for path in (ROOT / "solutions").iterdir():
        if path.is_dir() and not path.name.startswith("."):
            try:
                validate_progress(path)
            except (ValueError, OSError) as exc:
                errors.append(f"Spec {path.name}: {exc}")
    for name, model in [
        ("use-case", UseCase),
        ("design", Design),
        ("decomposition", Decomposition),
        ("tender", TenderInput),
        ("evidence", FactInput),
    ]:
        schema = json.loads(
            (ROOT / "blueprint/schemas" / f"{name}.schema.json").read_text(encoding="utf-8")
        )
        if schema != model.model_json_schema():
            errors.append(f"Stale {name} schema; run python -m scripts.generate_schemas")
    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"Validated {len(paths)} repository files: contracts, local links, JSON/YAML, SVG and secret patterns."
    )
    print("Mermaid rendering, Compose runtime and live-provider checks are separate validations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

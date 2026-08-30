"""Explicit two-stage CLI: specification generation, then engineering packets."""

import argparse
import json
import shutil
from pathlib import Path

from src.blueprint import specs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Blueprint checkout root")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Compile three specs only; never application code")
    create.add_argument(
        "input", type=Path, help="Business use-case YAML; see templates/use-case.yaml"
    )
    for name in ("validate", "approve", "run", "complete"):
        cmd = commands.add_parser(name)
        cmd.add_argument("solution")
        if name in ("approve", "complete"):
            cmd.add_argument("--reviewer", required=True)
        if name == "run":
            cmd.add_argument("skill", choices=specs.SKILLS)
        if name == "complete":
            cmd.add_argument("task")
            cmd.add_argument("--evidence", action="append", required=True)
    commands.add_parser("doctor")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(
                json.dumps(
                    {
                        tool: shutil.which(tool) or "MISSING"
                        for tool in ("git", "docker", "python", "ollama")
                    },
                    indent=2,
                )
            )
            print(
                "Docker needs a running daemon + Compose v2. Windows: enable WSL2 and install Docker Desktop."
            )
            print(
                "Cloud LLM calls need LLM_MODEL and LLM_API_KEY. Local AI is optional. See docs/setup.md."
            )
        elif args.command == "create":
            print(
                f"Three specifications generated: {specs.create(args.root, args.input)}\nReview them before approve/run."
            )
        else:
            path = specs.safe_solution(args.root, args.solution)
            if args.command == "validate":
                specs.validate(path)
                print("Specifications valid; approval and implementation are separate checks.")
            elif args.command == "approve":
                specs.approve(path, args.reviewer)
                print("Recorded local approval of current specification contents.")
            elif args.command == "run":
                packet = specs.run_skill(args.root, path, args.skill)
                print(
                    f"Engineering packet: {packet}\nExecute it with your coding agent or developer; no code was silently generated."
                )
            elif args.command == "complete":
                specs.complete(path, args.task, args.evidence, args.reviewer)
                print("Recorded developer attestation and evidence hashes.")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

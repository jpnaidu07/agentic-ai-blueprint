"""Guided specifications and resumable engineering plans for any structured use case."""

import argparse
import json
import shutil
from pathlib import Path

from src.blueprint import specs, workflow


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Blueprint checkout root")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Compile three specs only; never application code")
    create.add_argument(
        "input", type=Path, help="Business use-case YAML; see templates/use-case.yaml"
    )
    create.add_argument(
        "--through",
        choices=specs.STAGES,
        default="decomposition",
        help="Stop after this spec stage (default: all three)",
    )
    spec = commands.add_parser(
        "spec", help="Generate the next spec stage without overwriting reviewed work"
    )
    spec.add_argument("solution")
    spec.add_argument("stage", choices=["design", "decomposition", "all"])
    for name in ("validate", "approve", "run", "complete", "status", "guide"):
        cmd = commands.add_parser(name)
        cmd.add_argument("solution")
        if name in ("approve", "complete"):
            cmd.add_argument("--reviewer", required=True)
        if name == "run":
            cmd.add_argument(
                "selector", nargs="?", default="next", help="next, all, skill, or TASK-ID"
            )
            cmd.add_argument("--module", type=int, choices=range(1, 9))
            cmd.add_argument("--include-dependencies", action="store_true")
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
            path = specs.create(args.root, args.input, args.through)
            print(
                f"Specifications generated through {args.through}: {path}\nReview before continuing."
            )
            print(workflow.guide(path))
        else:
            path = specs.safe_solution(args.root, args.solution)
            if args.command == "validate":
                specs.validate_progress(path)
                print(
                    "Current spec stages valid; implementation still requires all three stages and approval."
                )
            elif args.command == "spec":
                specs.advance(path, args.stage)
                print(workflow.guide(path))
            elif args.command == "guide":
                print(workflow.guide(path))
            elif args.command == "status":
                print(json.dumps(workflow.status(path), indent=2))
            elif args.command == "approve":
                specs.approve(path, args.reviewer)
                print("Recorded local approval of current specification contents.")
            elif args.command == "run":
                packet = workflow.prepare(
                    args.root, path, args.selector, args.module, args.include_dependencies
                )
                print(
                    f"Teaching/execution plan: {packet}\nAsk your coding agent to execute it using blueprint-workflow, or implement it yourself. No code or tests ran.\nBlocked tasks stay blocked until prerequisites have current evidence."
                )
            elif args.command == "complete":
                specs.complete(path, args.task, args.evidence, args.reviewer)
                print("Recorded developer attestation and evidence hashes.")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

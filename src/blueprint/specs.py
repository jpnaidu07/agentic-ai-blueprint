"""Deterministic specification compiler. Inputs remain data, never executable code."""

import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from graphlib import TopologicalSorter
from pathlib import Path

import yaml

from src.blueprint.models import Decomposition, Design, Module, Task, UseCase

MODULES = [
    "Purpose & Scope",
    "System Prompt Design",
    "Choose LLM",
    "Tools & Integrations",
    "Memory Systems",
    "Orchestration",
    "User Interface",
    "Testing & Evaluation",
]
SPEC_FILES = [
    "capability/capability.yaml",
    "capability/capability-spec.md",
    "design/architecture.yaml",
    "design/design-spec.md",
    "decomposition/tasks.yaml",
    "decomposition/decomposition-spec.md",
    "use-case.yaml",
]
SKILLS = [
    "backend",
    "database",
    "agents",
    "rag",
    "frontend",
    "infrastructure",
    "security",
    "tests",
    "evals",
    "deployment",
]
STAGES = ["capability", "design", "decomposition"]
STAGE_FILES = ["capability.yaml", "architecture.yaml", "tasks.yaml"]
SKILL_MODULES = {
    "backend": [1, 4, 5],
    "database": [5],
    "agents": [2, 3, 4, 6],
    "rag": [3, 4, 5],
    "frontend": [7],
    "infrastructure": [4, 5, 6],
    "security": [2, 4, 5, 6, 7],
    "tests": [8],
    "evals": [8],
    "deployment": [4, 6, 8],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def safe_solution(root: Path, name: str) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", name):
        raise ValueError("Solution name must be a lowercase slug of 3–64 characters")
    base = (root / "solutions").resolve()
    path = (base / name).resolve()
    if path.parent != base:
        raise ValueError("Solution path escapes the solutions directory")
    return path


def read_yaml(path):
    if path.stat().st_size > 1_000_000:
        raise ValueError("Specification exceeds 1 MB")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def render(title, data):
    """Keep prose and machine artifacts in agreement; structured sections are reviewable."""
    parts = [f"# {title}\n", "Generated proposal. Review before approving implementation.\n"]
    for key, value in data.items():
        parts += [f"## {key.replace('_', ' ').title()}\n"]
        if isinstance(value, str):
            parts += [value + "\n"]
        else:
            parts += [
                "```yaml\n"
                + yaml.safe_dump(value, sort_keys=False, allow_unicode=True).rstrip()
                + "\n```\n"
            ]
    return "\n".join(parts)


def compile_specs(case: UseCase, design_override=None):
    capability = case.model_dump()
    decisions = [
        [
            case.problem,
            *case.objectives,
            f"Sensitivity: {case.data_sensitivity}",
            f"Scale: {case.scale}",
        ],
        [
            "Version prompts; separate system policy from untrusted documents and tool output.",
            "Require schema-valid outputs and source citations; abstain on missing evidence.",
            "Model output cannot authorize tools, change business rules, or approve decisions.",
        ],
        [
            case.model_selection,
            "Select provider and exact model through environment configuration.",
            "Validate capabilities per model. Fail visibly; fallback must be explicitly configured within the approved data boundary.",
        ],
        [
            "Register input/output schemas, roles, resource scope, authentication, timeout, retry policy and errors.",
            "Only allowlisted tools; no generated shell commands. Mutations need idempotency and authorization.",
        ],
        [
            "Relational records for business entities; page-aware chunks for retrieval; bytes in file/object storage.",
            "Working state is per request. Persist workflow/audit state separately from optional conversation memory.",
            "Embeddings are optional and never the authority for transactional facts.",
        ],
        [
            "Validate input -> process -> verify evidence -> deterministic policy -> human review.",
            "Persist state transitions transactionally, reject stale versions, bound retries and runtime.",
            "Use durable queues and a graph engine only for justified asynchronous/parallel work.",
        ],
        [
            "Derive screens and APIs from requirement IDs, personas and journeys.",
            "Expose evidence and unresolved questions alongside outcomes; never present model text as an approved decision.",
        ],
        [
            "Unit, API, isolation, invalid-input, concurrency, injection and workflow regression tests.",
            "Version golden datasets; measure retrieval recall/precision, abstention, latency and observed model usage.",
            "Separate offline deterministic checks from live model evaluations and human review.",
        ],
    ]
    design = Design(
        solution=case.name,
        capability_digest=digest(capability),
        modules=[
            Module(number=i + 1, name=name, decisions=decisions[i])
            for i, name in enumerate(MODULES)
        ],
        tradeoffs=[
            "Proposed baseline: Python/FastAPI + relational SQL + same-origin browser UI; reuse one language for API and document pipelines.",
            "PostgreSQL for concurrent development; SQLite for isolated tests. SQLAlchemy shares query semantics.",
            "A dedicated SPA, vector service, broker and object store add operational cost; select them only when a capability requires them.",
            f"Deployment constraint: {case.deployment}",
        ],
        production_gates=[
            "Identity provider and secret rotation",
            "TLS, encryption at rest and restore drill",
            "Malware scanner and isolated parser workers",
            "Load tests, data retention review and human sign-off",
        ],
    ).model_dump()
    if design_override is not None:
        design = design_override
    tasks = []
    for req in case.requirements:
        tasks.append(
            Task(
                id=f"TASK-{req.id}",
                parent_capability=req.id,
                objective=req.objective,
                skill=req.skill,
                dependencies=[f"TASK-{dependency}" for dependency in req.depends_on],
                inputs=["capability/capability.yaml", "design/architecture.yaml"],
                outputs=[
                    f"implementation/{req.skill}",
                    f"implementation/{req.skill}/{req.id.lower()}-evidence.md",
                ],
                affected_modules=[f"implementation/{req.skill}"],
                blueprint_modules=req.blueprint_modules or SKILL_MODULES[req.skill],
                api_contract="Derive request/response and error schemas from this capability; review before coding.",
                data_contract="Define typed records, relationships, validation and migration from this capability.",
                agent_tools=["Use only design-approved tools with caller resource scope"],
                instructions=[
                    req.objective,
                    "Explain the goal, design choice and success check before implementation; then build and test real code.",
                    "Use solution-local source unless an existing reference is explicitly mapped. Identify database, service, agent and UI files as applicable.",
                    "For unavailable credentials or host services, record the exact prerequisite, user action and verification command; do not mark the task complete.",
                    "Record implementation files and validation evidence in the completion receipt.",
                ],
                tests=req.acceptance,
                definition_of_done=[*req.acceptance, "No secrets; tests pass; evidence reviewed"],
            )
        )
    # Tests and evaluations depend on all implementation capabilities.
    impl_ids = [t.id for t in tasks]
    for skill, dependencies in [
        ("tests", impl_ids),
        ("evals", ["TASK-TESTS"]),
        ("deployment", ["TASK-EVALS"]),
    ]:
        tasks.append(
            Task(
                id=f"TASK-{skill.upper()}",
                parent_capability=case.requirements[0].id,
                objective=f"Validate {skill} against approved capabilities",
                skill=skill,
                dependencies=dependencies,
                inputs=["decomposition/tasks.yaml"],
                outputs=[f"implementation/{skill}/evidence.md"],
                affected_modules=[f"implementation/{skill}"],
                blueprint_modules=SKILL_MODULES[skill],
                api_contract="Exercise approved API contracts",
                data_contract="Use synthetic fixtures only",
                agent_tools=[],
                instructions=[
                    "Execute the corresponding reusable skill and retain reproducible evidence."
                ],
                tests=["All prerequisite work packages complete against current specs"],
                definition_of_done=["Evidence exists and reviewer accepts the results"],
            )
        )
    decomposition = Decomposition(
        solution=case.name, design_digest=digest(design), tasks=tasks
    ).model_dump()
    return capability, design, decomposition


def create(root: Path, input_file: Path, through="decomposition"):
    if through not in STAGES:
        raise ValueError("Unknown specification stage")
    case = UseCase.model_validate(read_yaml(input_file))
    target = safe_solution(root, case.name)
    if target.exists():
        raise ValueError(
            f"Solution already exists: {case.name}; edit and revalidate its specs, never overwrite them"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    artifacts = compile_specs(case)
    # Publish only after all writes succeed; temporary data stays beside the target.
    with tempfile.TemporaryDirectory(prefix=".spec-", dir=target.parent) as temp:
        staging = Path(temp) / case.name
        staging.mkdir()
        (staging / "use-case.yaml").write_text(
            yaml.safe_dump(case.model_dump(), sort_keys=False), encoding="utf-8"
        )
        for index, (folder, filename, title) in enumerate(
            [
                ("capability", "capability.yaml", "Capability"),
                ("design", "architecture.yaml", "Design"),
                ("decomposition", "tasks.yaml", "Decomposition"),
            ]
        ):
            if index > STAGES.index(through):
                break
            directory = staging / folder
            directory.mkdir()
            (directory / filename).write_text(
                yaml.safe_dump(artifacts[index], sort_keys=False), encoding="utf-8"
            )
            (directory / f"{folder}-spec.md").write_text(
                render(f"{case.title}: {title}", artifacts[index]), encoding="utf-8"
            )
        validate_progress(staging)
        staging.rename(target)
    return target


def validate_progress(path: Path):
    """Validate an intentional prefix of the three-stage specification workflow."""
    for relative in SPEC_FILES:
        if (path / relative).exists() and not (path / relative).resolve().is_relative_to(
            path.resolve()
        ):
            raise ValueError("Specification path escapes solution")
    case = UseCase.model_validate(read_yaml(path / "capability/capability.yaml"))
    if (
        not (path / "use-case.yaml").is_file()
        or not (path / "capability/capability-spec.md").is_file()
    ):
        raise ValueError("Missing use-case or capability artifact")
    # use-case.yaml retains the original brief; capability.yaml is the reviewed authority.
    UseCase.model_validate(read_yaml(path / "use-case.yaml"))
    if case.name != path.name:
        raise ValueError("Solution IDs disagree")
    if not (path / "design").exists():
        if (path / "decomposition").exists():
            raise ValueError("Decomposition requires design first")
        return case, None, None
    design = Design.model_validate(read_yaml(path / "design/architecture.yaml"))
    if design.solution != case.name:
        raise ValueError("Solution IDs disagree")
    if not (path / "design/design-spec.md").is_file():
        raise ValueError("Missing design-spec.md")
    if [(m.number, m.name) for m in design.modules] != list(enumerate(MODULES, 1)):
        raise ValueError("Design must contain exactly the eight ordered blueprint modules")
    if design.capability_digest != digest(case.model_dump()):
        raise ValueError(
            "Design is stale relative to capability; revise it and refresh its capability_digest"
        )
    if not (path / "decomposition").exists():
        return case, design, None
    decomposition = Decomposition.model_validate(read_yaml(path / "decomposition/tasks.yaml"))
    if decomposition.solution != case.name:
        raise ValueError("Solution IDs disagree")
    if decomposition.design_digest != digest(design.model_dump()):
        raise ValueError(
            "Decomposition is stale relative to design; revise it and refresh its design_digest"
        )
    graph = {t.id: t.dependencies for t in decomposition.tasks}
    if len(graph) != len(decomposition.tasks):
        raise ValueError("Duplicate task ID")
    for task in decomposition.tasks:
        if task.skill not in SKILLS or task.parent_capability not in {
            r.id for r in case.requirements
        }:
            raise ValueError(f"Invalid capability or skill in {task.id}")
        if set(task.dependencies) - graph.keys():
            raise ValueError(f"Unknown dependencies in {task.id}")
        for file in task.inputs + task.outputs + task.affected_modules:
            if not (path / file).resolve().is_relative_to(path.resolve()):
                raise ValueError(f"Task path escapes solution: {task.id}")
    if {r.id for r in case.requirements} - {t.parent_capability for t in decomposition.tasks}:
        raise ValueError("Capabilities lack implementation tasks")
    list(TopologicalSorter(graph).static_order())
    for relative in SPEC_FILES:
        if not (path / relative).is_file():
            raise ValueError(f"Missing artifact: {relative}")
    return case, design, decomposition


def validate(path: Path):
    result = validate_progress(path)
    if result[2] is None:
        raise ValueError("Complete capability, design and decomposition before implementation")
    return result


def advance(path: Path, stage: str):
    """Add the next stage without overwriting reviewed specifications or implementation."""
    if stage not in {"design", "decomposition", "all"}:
        raise ValueError("Use create for capability; spec accepts design, decomposition or all")
    case, design, decomposition = validate_progress(path)
    if stage == "all":
        if design is None:
            advance(path, "design")
        if decomposition is None:
            advance(path, "decomposition")
        return path
    if (path / stage).exists():
        raise ValueError(f"{stage} already exists; review/edit it, never overwrite it")
    if stage == "decomposition" and design is None:
        raise ValueError("Generate and review design before decomposition")
    index = STAGES.index(stage)
    data = compile_specs(case, design.model_dump() if design else None)[index]
    with tempfile.TemporaryDirectory(prefix=".spec-", dir=path) as temp:
        directory = Path(temp) / stage
        directory.mkdir()
        (directory / STAGE_FILES[index]).write_text(
            yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )
        (directory / f"{stage}-spec.md").write_text(
            render(f"{case.title}: {stage.title()}", data), encoding="utf-8"
        )
        directory.rename(path / stage)
    validate_progress(path)
    return path / stage


def spec_digest(path):
    files = sorted(
        set(SPEC_FILES)
        | {
            str(p.relative_to(path))
            for section in ("capability", "design", "decomposition")
            for p in (path / section).rglob("*")
            if p.is_file()
        }
    )
    if any(not (path / f).resolve().is_relative_to(path.resolve()) for f in files):
        raise ValueError("Specification symlink escapes solution")
    return digest({f: hashlib.sha256((path / f).read_bytes()).hexdigest() for f in files})


def approve(path, reviewer):
    case, _, _ = validate(path)
    if case.open_questions:
        raise ValueError("Resolve capability open_questions before approval")
    if not reviewer.strip():
        raise ValueError("Reviewer identity is required")
    receipt = {
        "reviewer": reviewer,
        "spec_digest": spec_digest(path),
        "at": datetime.now(timezone.utc).isoformat(),
        "scope": "Local engineering approval; not a production procurement decision",
    }
    (path / "approval.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")


def require_approval(path):
    validate(path)
    receipt = path / "approval.json"
    if not receipt.exists() or json.loads(receipt.read_text(encoding="utf-8"))[
        "spec_digest"
    ] != spec_digest(path):
        raise ValueError(
            "Missing or stale spec approval: review all three specifications and run approve"
        )


def require_dependencies(path, dependencies, checked=None, context=None):
    checked = set() if checked is None else checked
    # A context lives only for one read/check, never across edits or CLI invocations.
    if context is None:
        context = ({t.id: t for t in validate(path)[2].tasks}, spec_digest(path))
    tasks, current_digest = context
    for dependency in dependencies:
        if dependency in checked:
            continue
        if dependency not in tasks:
            raise ValueError(f"Unknown prerequisite: {dependency}")
        checked.add(dependency)
        receipt = path / "implementation" / "receipts" / f"{dependency}.json"
        if not receipt.resolve().is_relative_to(path.resolve()):
            raise ValueError("Completion receipt escapes solution")
        if not receipt.exists():
            raise ValueError(f"Incomplete prerequisite: {dependency}")
        data = json.loads(receipt.read_text(encoding="utf-8"))
        if (
            not data["evidence"]
            or data.get("task") != dependency
            or data["spec_digest"] != current_digest
            or any(
                not (path / file).resolve().is_relative_to(path.resolve())
                or not (path / file).is_file()
                or hashlib.sha256((path / file).read_bytes()).hexdigest() != sha
                for file, sha in data["evidence"].items()
            )
        ):
            raise ValueError(f"Stale completion evidence: {dependency}")
        require_dependencies(path, tasks[dependency].dependencies, checked, context)
        current_dependencies = {
            prerequisite: hashlib.sha256(
                (path / "implementation/receipts" / f"{prerequisite}.json").read_bytes()
            ).hexdigest()
            for prerequisite in tasks[dependency].dependencies
        }
        if data.get("dependencies", {}) != current_dependencies:
            raise ValueError(f"Stale prerequisite receipts: {dependency}")


def run_skill(root, path, skill):
    require_approval(path)
    _, _, decomposition = validate(path)
    tasks = [t for t in decomposition.tasks if t.skill == skill]
    if not tasks:
        raise ValueError(f"No {skill} work packages in this solution")
    require_dependencies(path, set(d for t in tasks for d in t.dependencies))
    guidance = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    destination = path / "implementation" / "work-packages"
    if not destination.resolve().is_relative_to(path.resolve()):
        raise ValueError("Work-package path escapes solution")
    destination.mkdir(parents=True, exist_ok=True)
    packet = destination / f"{skill}.md"
    packet.write_text(
        guidance
        + "\n\n"
        + render("Approved work packages", {"tasks": [t.model_dump() for t in tasks]}),
        encoding="utf-8",
    )
    return packet


def complete(path, task_id, evidence, reviewer):
    require_approval(path)
    _, _, decomposition = validate(path)
    if task_id not in {t.id for t in decomposition.tasks}:
        raise ValueError("Unknown work package")
    if not evidence or not reviewer.strip():
        raise ValueError("Completion needs a reviewer and nonempty evidence")
    task = next(t for t in decomposition.tasks if t.id == task_id)
    require_dependencies(path, task.dependencies)
    hashes = {}
    for relative in evidence:
        file = (path / relative).resolve()
        if not file.is_relative_to(path.resolve()) or not file.is_file():
            raise ValueError("Evidence must be an existing file inside the solution")
        hashes[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    receipt = path / "implementation" / "receipts" / f"{task_id}.json"
    if not receipt.resolve().is_relative_to(path.resolve()):
        raise ValueError("Completion receipt escapes solution")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "task": task_id,
                "reviewer": reviewer,
                "spec_digest": spec_digest(path),
                "evidence": hashes,
                "dependencies": {
                    prerequisite: hashlib.sha256(
                        (path / "implementation/receipts" / f"{prerequisite}.json").read_bytes()
                    ).hexdigest()
                    for prerequisite in task.dependencies
                },
                "at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

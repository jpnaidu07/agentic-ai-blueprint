"""Runtime-loaded specifications/skills, model-assisted stages and bounded task execution."""

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import yaml

from src.blueprint import specs, workflow
from src.blueprint.models import Decomposition, Design, UseCase
from src.workbench.contracts import Advice, Implementation
from src.workbench.runtime import SUFFIXES, source_digest, source_snapshot
from src.workbench.security import WorkbenchError, local_path, no_secrets
from src.workbench.system import inspect_system


class Engine:
    def __init__(self, root, state, providers, jobs, runtime):
        self.root, self.state = root, state
        self.providers, self.jobs, self.runtime = providers, jobs, runtime

    def skill(self, name):
        if name not in {*specs.SKILLS, *specs.STAGES}:
            raise WorkbenchError("Unknown skill")
        content = local_path(self.root, f"skills/{name}/SKILL.md").read_text(encoding="utf-8")
        if name == "production-rag":
            checklist = local_path(
                self.root, "skills/production-rag/references/design-checklist.md"
            ).read_text(encoding="utf-8")
            content += "\n\n## Implementation checklist\n\n" + checklist
        return content

    def artifacts(self, path):
        result = {}
        for section in specs.STAGES:
            for file in sorted((path / section).rglob("*")):
                if file.is_file():
                    relative = file.relative_to(path).as_posix()
                    local_path(path, relative)
                    if file.stat().st_size > 200000:
                        raise WorkbenchError("Specification file is too large for this workbench.")
                    if file.suffix in {".md", ".yaml", ".mmd"}:
                        result[relative] = file.read_text(encoding="utf-8")
        if sum(len(v) for v in result.values()) > 400000:
            raise WorkbenchError("Specification set is too large; narrow the solution scope.")
        return result

    def overview(self, name):
        path = specs.safe_solution(self.root, name)
        if not path.is_dir():
            raise WorkbenchError("Solution not found")
        files = self.artifacts(path)
        try:
            progress = workflow.status(path)
            progress["spec_digest"] = (
                specs.spec_digest(path) if progress["stage"] == "decomposition" else None
            )
        except (ValueError, OSError, KeyError):
            progress = {
                "solution": name,
                "approved": False,
                "tasks": [],
                "stage": "needs-repair",
                "issue": "Specs are incomplete or stale. Review the artifact editor and validate the dependent stages before approval.",
            }
        return {
            **progress,
            "files": [
                {
                    "path": key,
                    "content": value,
                    "sha256": hashlib.sha256((path / key).read_bytes()).hexdigest(),
                }
                for key, value in files.items()
            ],
            "reference": name == "government-tender-processing",
            "runtime_files": list(source_snapshot(path / "implementation/runtime")),
        }

    def capability(self, brief, connection, job_id):
        if specs.safe_solution(self.root, brief.name).exists():
            raise WorkbenchError(
                "This solution already exists. Select it to continue; no existing files were overwritten."
            )
        self.jobs.event(
            job_id,
            "Capability lesson: identify actors, journeys, business rules, acceptance checks and unknowns before choosing technology.",
        )
        case, usage = self.providers.generate(
            connection,
            UseCase,
            self.skill("capability")
            + "\nGenerate a concrete capability proposal. Preserve the requested slug. Put unresolved domain decisions in open_questions. Requirements must have real, observable acceptance checks. Use depends_on for a valid acyclic graph and blueprint_modules 1..8. Do not copy the example domain.",
            {
                "brief": brief.model_dump(),
                "input_template": (self.root / "templates/use-case.yaml").read_text(
                    encoding="utf-8"
                ),
            },
        )
        case = UseCase.model_validate({**case.model_dump(), "name": brief.name})
        self.jobs.check_cancelled()
        with tempfile.TemporaryDirectory(dir=self.state) as temporary:
            file = Path(temporary) / "input.yaml"
            file.write_text(yaml.safe_dump(case.model_dump(), sort_keys=False), encoding="utf-8")
            specs.create(self.root, file, through="capability")
        self.jobs.event(
            job_id,
            "Capability files created. Review the proposal and resolve questions before design/implementation.",
        )
        return {
            "solution": case.name,
            "stage": "capability",
            "open_questions": case.open_questions,
            "usage": usage,
        }

    def stage(self, name, stage, connection, job_id):
        path = specs.safe_solution(self.root, name)
        if stage == "remaining":
            for current in ("design", "decomposition"):
                if not (path / current).exists():
                    self.stage(name, current, connection, job_id)
            return {
                "solution": name,
                "message": "All three proposals are present. Review and approve their current contents before implementation.",
            }
        case, design, _ = specs.validate_progress(path)
        if (path / stage).exists():
            raise WorkbenchError(
                "That stage already exists. Use the artifact editor to revise it; it was not overwritten."
            )
        if stage == "decomposition" and design is None:
            raise WorkbenchError("Generate and review design before decomposition.")
        before = specs.digest(self.artifacts(path))
        self.jobs.event(
            job_id,
            f"{stage.title()} lesson: {'compare architecture choices and map each requirement to the eight modules' if stage == 'design' else 'define concrete source files, contracts, dependencies, tests and completion criteria'}.",
        )
        model = Design if stage == "design" else Decomposition
        instructions = (
            self.skill(stage)
            + "\nPropose a concrete solution for the supplied capabilities. The built-in isolated runtime supports Python, FastAPI, SQLAlchemy, SQLite and same-origin HTML/CSS/JS. Use implementation/runtime/app.py exporting app, GET /api/health and tests/test_*.py. Use /data for writable app state; preview storage is temporary. Other stacks/external services must be explicit manual prerequisites. Never include credentials or host shell commands. Preserve the exact eight ordered module names when producing Design."
        )
        proposal, usage = self.providers.generate(
            connection,
            model,
            instructions,
            {
                "specifications": self.artifacts(path),
                "modules": specs.MODULES,
                "skills": specs.SKILLS,
            },
        )
        data = proposal.model_dump()
        data["solution"] = name
        if stage == "design":
            data["capability_digest"] = specs.digest(case.model_dump())
        else:
            data["design_digest"] = specs.digest(design.model_dump())
            if len(data["tasks"]) > 40:
                raise WorkbenchError("Decomposition exceeds 40 tasks. Narrow the capability scope.")
            # Mandatory gates come from the maintained compiler; the model may refine implementation tasks.
            implementation = [
                t for t in data["tasks"] if t["skill"] not in {"tests", "evals", "deployment"}
            ]
            gates = specs.compile_specs(case, design.model_dump())[2]["tasks"][-3:]
            gates[0]["dependencies"] = [t["id"] for t in implementation]
            data["tasks"] = implementation + gates
        self.jobs.check_cancelled()
        if before != specs.digest(self.artifacts(path)):
            raise WorkbenchError(
                "Specifications changed while the model was working. Review and retry."
            )
        index = specs.STAGES.index(stage)
        with tempfile.TemporaryDirectory(dir=self.state) as temporary:
            check = Path(temporary) / name
            check.mkdir()
            shutil.copyfile(path / "use-case.yaml", check / "use-case.yaml")
            for existing in specs.STAGES[:index]:
                shutil.copytree(path / existing, check / existing)
            output = check / stage
            output.mkdir()
            (output / specs.STAGE_FILES[index]).write_text(
                yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
            )
            (output / f"{stage}-spec.md").write_text(
                specs.render(f"{case.title}: {stage}", data), encoding="utf-8"
            )
            specs.validate_progress(check)
            output.rename(path / stage)
        self.jobs.event(
            job_id,
            f"{stage.title()} generated and schema/dependency validation passed. This is a proposal, not proof of implementation.",
        )
        return {"solution": name, "stage": stage, "usage": usage}

    def edit(self, name, section, content, expected_sha):
        path = specs.safe_solution(self.root, name)
        index = specs.STAGES.index(section)
        target = local_path(path, f"{section}/{specs.STAGE_FILES[index]}")
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected_sha:
            raise WorkbenchError("Artifact changed since it was opened. Refresh before saving.")
        no_secrets(content)
        parsed = yaml.safe_load(content)
        model = {"capability": UseCase, "design": Design, "decomposition": Decomposition}[section]
        data = model.model_validate(parsed).model_dump()
        if data.get("name", data.get("solution")) != name:
            raise WorkbenchError("The editor cannot rename a solution.")
        if section == "design":
            if [(m["number"], m["name"]) for m in data["modules"]] != list(
                enumerate(specs.MODULES, 1)
            ):
                raise WorkbenchError("Preserve the eight ordered blueprint module names.")
            case = UseCase.model_validate(specs.read_yaml(path / "capability/capability.yaml"))
            data["capability_digest"] = specs.digest(case.model_dump())
        if section == "decomposition":
            design = Design.model_validate(specs.read_yaml(path / "design/architecture.yaml"))
            data["design_digest"] = specs.digest(design.model_dump())
        backup = self.state / "revisions" / name / expected_sha
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, backup / target.name)
        target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        (target.parent / f"{section}-spec.md").write_text(
            specs.render(f"{name}: {section}", data), encoding="utf-8"
        )
        return {
            "message": "Saved with a local backup. Dependent stages/approval may now be stale; review them in order before approving again."
        }

    def ask(self, question, connection, job_id):
        self.jobs.event(
            job_id,
            "This is advice only: no files, commands, tools or approvals will be changed by the answer.",
        )
        data = {
            "question": question.text,
            "selected_model": {"provider": connection.provider, "model": connection.model},
            "hardware_and_local_tools": inspect_system(self.root),
            "project": (self.root / "docs/workbench.md").read_text(encoding="utf-8"),
        }
        if question.solution:
            data["specifications"] = self.artifacts(
                specs.safe_solution(self.root, question.solution)
            )
        advice, usage = self.providers.generate(
            connection,
            Advice,
            "You teach spec-driven agent engineering. Explain tradeoffs, exact next UI steps and manual prerequisites. For model recommendations distinguish account availability, schema compatibility, hardware estimates and task benchmarks. Never invent measured quality, pricing or claim a model is best without task evidence. Do not claim to execute actions; this channel is read-only advice.",
            data,
        )
        return {**advice.model_dump(), "usage": usage}

    def run(self, name, body, connection, job_id):
        if not body.confirmed:
            raise WorkbenchError(
                "Confirm the selected task scope and data transfer before running."
            )
        path = specs.safe_solution(self.root, name)
        packet = workflow.prepare(
            self.root, path, body.selector, body.module, body.include_dependencies
        )
        plan = json.loads(packet.with_suffix(".json").read_text())
        if name == "government-tender-processing":
            self.jobs.event(
                job_id,
                "This reference already has backend, database, agent, evidence, UI and tests mapped in its implementation README. It is not safe to replace shared repository source from generated files.",
            )
            return {
                "message": "Teaching plan prepared for the existing reference. Launch the Tender reference from Apps to explore it. Use the displayed plan with a coding agent to modify shared source; this UI's code writer is restricted to new solution-local runtime files.",
                "plan": packet.relative_to(path).as_posix(),
                "lesson": packet.read_text(encoding="utf-8")[:30000],
                "outcome": "reference-ready-to-explore",
            }
        if body.execute:
            self.runtime.runner_ready()
        tasks = {t.id: t for t in specs.validate(path)[2].tasks}
        outcomes = []
        for row in plan["tasks"][: body.max_tasks]:
            self.jobs.check_cancelled()
            specs.require_approval(path)
            if specs.spec_digest(path) != plan["spec_digest"]:
                raise WorkbenchError(
                    "Specs changed during the run. Re-approve and start a fresh plan."
                )
            current = {t["id"]: t for t in workflow.status(path)["tasks"]}[row["id"]]
            if current["state"] == "complete":
                continue
            if not current["ready"]:
                outcomes.append(
                    {"task": row["id"], "state": "blocked", "manual_steps": current["issues"]}
                )
                continue
            task = tasks[row["id"]]
            self.jobs.event(job_id, f"{task.id}: {task.objective}")
            runtime = path / "implementation/runtime"
            before = source_snapshot(runtime)
            feedback = self.state / "task-feedback" / name / f"{task.id}.json"
            previous = (
                json.loads(feedback.read_text(encoding="utf-8")) if feedback.exists() else None
            )
            bundle, usage = self.providers.generate(
                connection,
                Implementation,
                self.skill(task.skill)
                + "\nTeach then implement this exact approved task. All file paths are relative to implementation/runtime, never the repository. Build real source and meaningful tests/test_*.py. Runtime: Python/FastAPI/SQLAlchemy, installed pinned dependencies; no package installation or shell commands. For a web app create app.py exporting app, serve same-origin UI, include GET /api/health. Use /data for app SQLite state; tests use temporary paths. Container tests are offline and unprivileged; never require live credentials. Preserve existing source unless the task requires editing it. Report any unmet external acceptance in manual_steps. Deployment tasks must not claim production readiness; report organizational gates. No placeholders, fake success or arbitrary scoring. Return full content of changed files only, not deletions.",
                {
                    "task": task.model_dump(),
                    "specifications": self.artifacts(path),
                    "existing_source": before,
                    "previous_attempt": previous,
                    "available_dependencies": (self.root / "requirements-dev.txt").read_text()
                    + (self.root / "requirements.txt").read_text(),
                },
            )
            self.jobs.event(job_id, bundle.lesson)
            self.jobs.check_cancelled()
            if specs.spec_digest(path) != plan["spec_digest"] or before != source_snapshot(runtime):
                raise WorkbenchError(
                    "Source/specs changed during generation. Nothing from this response was applied; review and retry."
                )
            prepared = {}
            for file in bundle.files:
                target = local_path(runtime, file.path)
                if target.suffix not in SUFFIXES or target.name.lower() in {
                    "requirements.txt",
                    "requirements-dev.txt",
                    "dockerfile",
                    "pyproject.toml",
                    "setup.py",
                    "setup.cfg",
                }:
                    raise WorkbenchError(
                        "Generated file requests an unsupported runtime/package configuration. Use the reviewed manual setup path."
                    )
                if file.path in prepared:
                    raise WorkbenchError("Duplicate generated file path")
                no_secrets(file.content)
                prepared[file.path] = file.content
            if not prepared and task.skill not in {"tests", "evals", "deployment"}:
                raise WorkbenchError(
                    "Model produced no implementation files. Review the task or select a more capable model."
                )
            combined = {**before, **prepared}
            if len(combined) > 100 or sum(len(v) for v in combined.values()) > 1500000:
                raise WorkbenchError("Generated source exceeds the bounded runtime size.")
            archive = self.state / "revisions" / name / job_id / task.id
            archive.mkdir(parents=True, exist_ok=True)
            (archive / "before.json").write_text(json.dumps(before), encoding="utf-8")
            for relative, content in prepared.items():
                target = local_path(runtime, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            outcome = {
                "task": task.id,
                "lesson": bundle.lesson,
                "summary": bundle.summary,
                "files": list(prepared),
                "manual_steps": bundle.manual_steps,
                "usage": usage,
                "state": "generated-not-verified",
            }
            self.jobs.event(
                job_id, f"Wrote {len(prepared)} scoped source files. {bundle.verification}"
            )
            if body.execute:
                verification = self.runtime.verify(name)
                outcome["verification"] = verification
                if (
                    verification["exit_code"] == 0
                    and not bundle.manual_steps
                    and task.skill != "deployment"
                ):
                    self.jobs.check_cancelled()
                    if (
                        specs.spec_digest(path) != plan["spec_digest"]
                        or source_digest(runtime) != verification["source_digest"]
                    ):
                        raise WorkbenchError(
                            "Source/specs changed during tests. The results cannot authorize current files."
                        )
                    evidence = local_path(
                        path, f"implementation/{task.skill}/{task.id.lower()}-evidence.md"
                    )
                    evidence.parent.mkdir(parents=True, exist_ok=True)
                    evidence.write_text(specs.render(task.id, outcome), encoding="utf-8")
                    # Task attestations refer to immutable tested snapshots. Later tasks can
                    # legitimately edit shared source; the launch ledger separately checks
                    # the current integrated runtime against its latest test run.
                    snapshot_files = []
                    for relative, content in source_snapshot(runtime).items():
                        snapshot_file = local_path(
                            path, f"implementation/evidence/{task.id}/{job_id}/{relative}"
                        )
                        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
                        snapshot_file.write_text(content, encoding="utf-8")
                        snapshot_files.append(snapshot_file.relative_to(path).as_posix())
                    specs.complete(
                        path,
                        task.id,
                        [evidence.relative_to(path).as_posix(), *snapshot_files],
                        "workbench-agent",
                    )
                    ledger = self.state / "verified" / f"{name}.json"
                    ledger.parent.mkdir(exist_ok=True)
                    ledger.write_text(
                        json.dumps(
                            {
                                "source_digest": verification["source_digest"],
                                "spec_digest": plan["spec_digest"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    outcome["state"] = "complete-with-agent-attestation"
                else:
                    outcome["state"] = "needs-attention"
                    if task.skill == "deployment":
                        outcome["manual_steps"].append(
                            "An independent human must review deployment acceptance; no automatic production-completion receipt is issued."
                        )
            outcomes.append(outcome)
            feedback.parent.mkdir(parents=True, exist_ok=True)
            feedback.write_text(json.dumps(outcome), encoding="utf-8")
            self.jobs.event(job_id, f"{task.id}: {outcome['state']}")
        return {
            "solution": name,
            "tasks": outcomes,
            "outcome": "needs-attention"
            if any(row["state"] in {"blocked", "needs-attention"} for row in outcomes)
            else "finished",
            "message": "Selected work finished or reported blockers. Review actual evidence and remaining tasks. Agent-written tests are not independent production certification.",
            "bounded_at": body.max_tasks,
        }

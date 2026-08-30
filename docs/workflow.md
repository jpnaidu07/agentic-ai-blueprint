# Learn, build and resume any solution

The intended sequence is **problem → capability → design → decomposition →
implementation tasks → tests/evals → release preparation**. All solutions use the
same engine and skills; their domain decisions remain in their own directories.

There are two cooperating parts:

- **CLI:** generates specification proposals and teaching plans, tracks dependency
  readiness, and checks approval/evidence hashes. It never invokes a model, builds
  an application or executes commands embedded in a specification.
- **Coding agent or developer:** reviews the proposals, teaches each step, writes
  the actual source/configuration, executes tests and records evidence. Use the
  repository's [blueprint-workflow skill](../.agents/skills/blueprint-workflow/SKILL.md)
  for this execution loop. A CLI `run all` by itself only prepares that loop.

## Ask the coding agent

Open this checkout in your coding agent and use one of these requests. If the skill
is not discovered automatically, ask the agent to read its file explicitly.

```text
Use .agents/skills/blueprint-workflow/SKILL.md for government-tender-processing.
Teach me and complete all authorized engineering steps in dependency order.
Reuse the existing reference implementation, explain and verify each component,
fix gaps, and report exact manual actions for anything you cannot complete.
Do not deploy externally or use real procurement data.
```

```text
Use blueprint-workflow for my customer returns problem. Start with capability
only. Explain its requirements and acceptance checks, then stop for my review.
```

```text
Continue government-tender-processing using blueprint-workflow: complete the
next ready task, explain what I learned and show the validation, then stop.
```

```text
Use blueprint-workflow for government-tender-processing, blueprint module 5
(Memory Systems). Include its unfinished prerequisites, teach and implement
the selected tasks, and stop after that section.
```

All mode still respects unresolved business decisions, prerequisite failures and
authorization for external actions. It is not a claim that any arbitrary problem
can be implemented without domain input, credentials or infrastructure.

## Generate specs all at once or one stage at a time

Install the package using the [setup instructions](setup.md). Run from the checkout
root with the virtual environment active. Copy `templates/use-case.yaml`, edit
**name** as well as the problem, and replace the example requirements/decisions.
The solution argument in later commands is that YAML `name`, not its filename.

```powershell
# All three proposals, in sequence. No application code is created.
agent-blueprint create my-problem.yaml

# Alternatively, begin a NEW solution with capability only:
agent-blueprint create my-problem.yaml --through capability
agent-blueprint guide my-problem
# Review/edit capability/capability.yaml and capability-spec.md together.
agent-blueprint spec my-problem design
# Review architecture.yaml and design-spec.md; replace generic proposals.
agent-blueprint spec my-problem decomposition
# Or generate all remaining spec stages: agent-blueprint spec my-problem all
agent-blueprint validate my-problem
agent-blueprint approve my-problem --reviewer YOUR-NAME
```

Choose one creation route, not both on the same solution. Existing specs and code
are never silently overwritten. `spec all` fills only missing stages. Decomposition
uses the reviewed design, including edits. Changes to capability/design require
reviewing downstream decisions and refreshing their digests; approval becomes
stale. See `src/blueprint/specs.py`'s `digest` helper. Refreshing a digest alone is
not a substitute for reviewing the affected content.

```text
solutions/my-problem/
  use-case.yaml                    original structured brief
  capability/capability.yaml       reviewed capability authority
  capability/capability-spec.md    readable capability specification
  design/architecture.yaml
  design/design-spec.md
  decomposition/tasks.yaml
  decomposition/decomposition-spec.md
  implementation/                 created when engineering work begins
    work-packages/                 ignored local plans, not code completion
    database/ backend/ agents/ ...  actual new domain source and evidence as needed
    receipts/                      ignored local completion attestations
```

## Select implementation scope

These commands require all three specs and current approval. They prepare a
Markdown teaching plan plus a JSON snapshot in `implementation/work-packages/`.

| Scope | Command after `agent-blueprint` |
|---|---|
| All tasks, in dependency order | `run my-problem all` |
| Next ready unfinished task | `run my-problem next` |
| One exact task | `run my-problem TASK-CAP-DATA` |
| Database work | `run my-problem database` |
| Backend/services | `run my-problem backend` |
| Agents / UI | `run my-problem agents` / `run my-problem frontend` |
| Memory Systems section | `run my-problem --module 5` |
| UI section plus prerequisite tasks | `run my-problem --module 7 --include-dependencies` |
| Current progress and next command | `status my-problem` / `guide my-problem` |

Other skills: `rag`, `security`, `infrastructure`, `tests`, `evals`, `deployment`.
Not every problem needs every skill. For example, a deterministic service may not
need an LLM, vector database or agent task. Design still considers all eight
modules and explains which capabilities apply.

`depends_on` in each input requirement lists other requirement IDs. The compiler
turns them into task dependencies. A cycle or unknown ID is rejected. Optional
`blueprint_modules: [4, 5]` explicitly maps a requirement to numbered sections;
otherwise a documented skill-based default is proposed. Review these mappings.
The distinction matters: one backend service can implement tools, memory and
orchestration. Selecting sections does not create eight duplicate services.

A section/skill plan can show **blocked** tasks so you see the complete selected
scope. Its generation does not satisfy their prerequisites. Add
`--include-dependencies` to include unfinished prerequisite tasks outside that
scope, or complete them separately. Independent selected tasks can proceed. All
mode includes the complete ordered task graph.

Ready means the local specification/dependency gates pass; it does not probe a
database, credential or external service. The implementing agent verifies those
prerequisites and records actionable blockers without creating completion receipts.

When upgrading older generated solutions, the added requirement/module metadata
can change normalized digests. Review the affected capability/design/decomposition
and refresh the digests before re-approval. Existing local receipts must be
revalidated; no old receipt is silently treated as fresh evidence.

## What every task teaches and completes

1. **Explain:** the goal, relevant blueprint sections, inputs, design choice,
   expected files/contracts and success check.
2. **Build:** real service, API, database/migration, agent/tool, screen or
   configuration selected by the reviewed decomposition. Do not stop at folders
   or Markdown when code is the task's deliverable.
3. **Verify:** run acceptance checks, inspect results and fix failures; distinguish
   executed checks from checks requiring a missing external service.
4. **Record:** write task-specific evidence with actual paths, commands/results,
   useful lessons and limitations. For code within the solution, include the
   actual source/test files as additional `--evidence` arguments.
5. **Continue or pause:** all mode advances to the next ready task; step mode stops
   at its selected boundary. If blocked, leave it incomplete and give the exact
   missing item, user action, verification and resume command.

Example completion after actual implementation and tests:

```powershell
agent-blueprint complete my-problem TASK-CAP-DATA --reviewer YOUR-NAME --evidence implementation/database/task-cap-data-evidence.md --evidence implementation/database/models.py
agent-blueprint status my-problem
agent-blueprint run my-problem next
```

The example paths must exist. Completion is a developer/agent attestation backed
by file hashes, not automatic proof that tests ran. Receipts capture spec digests,
evidence hashes and prerequisite receipt hashes. Editing evidence, specs or an
upstream completion invalidates downstream receipts transitively. A prepared plan
is a snapshot: recheck status before work. The CLI never claims an unsigned
human review or an independent production certification.

## Government tender walkthrough

The tender solution already exists, so start with `guide` rather than `create`:

```powershell
agent-blueprint guide government-tender-processing
agent-blueprint status government-tender-processing
# Review its three specs and design notes before recording your approval.
agent-blueprint approve government-tender-processing --reviewer YOUR-NAME
agent-blueprint run government-tender-processing all
# Or begin with its next ready database task:
agent-blueprint run government-tender-processing next
```

Its graph covers database integrity → identity → ingestion → reviewed AI fact
proposals → deterministic scoring → independent review → portal/infrastructure.
Retrieval depends on ingestion and joins the portal path. Tests, evals and release
preparation follow implementation. Numbered module selection covers all eight
blueprint sections.

The [implementation map](../solutions/government-tender-processing/implementation/README.md)
points to the existing `src/tender/`, shared provider adapter and root Compose
files. The coding agent explains, tests and extends those files rather than
recreating them. New unrelated solutions keep their code isolated. No completion
receipts are pre-approved merely because reference code exists.

Starting the existing reference app is separate from engineering it: use
`./setup.ps1` then `./run.ps1` (or the documented Python-only route). Missing Docker,
live provider credentials, production identity or procurement approval remains an
explicit prerequisite. The workflow cannot silently supply these.

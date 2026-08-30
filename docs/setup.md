# Development setup

Use synthetic data. This is a reference implementation, not an approved procurement service.

## Windows: container workflow

Install [Git for Windows](https://git-scm.com/downloads/win) and
[Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/).
Enable its WSL2 backend and start Docker Desktop. Setup checks both the daemon
and Compose v2; it does not silently install WSL, change host settings, download
large models, or continue after a failed command.

```powershell
git clone https://github.com/jpnaidu07/agentic-ai-blueprint.git
cd agentic-ai-blueprint
./setup.ps1
./run.ps1
```

Setup uses a temporary Python container to create unique local admin, evaluator,
reviewer and viewer credentials. It creates `.env` and `.local-credentials.txt`
only when neither exists. Both files are ignored by git. Restrict their Windows
ACLs to your account and keep them off shared or unencrypted drives. All generated
identities initially see all tenders; replace `tender_ids: ["*"]` with explicit
IDs before any multi-user test. Never reuse these tokens outside local development.

Open `http://127.0.0.1:8000`, then enter the appropriate token from the credentials
file. Create a tender as admin; add bids, PDFs and reviewed facts as evaluator;
disconnect and use the independent reviewer token for decisions. API documentation
is at `/docs`. Switching identity clears the password field; no token is kept in
browser storage or query strings.

The core stack is app + PostgreSQL, capped at 4 GiB total. No vector service,
message broker, Redis or observability cluster is installed without a demonstrated
need. The UI and API share port 8000; no frontend build service is required.

```powershell
docker compose config --quiet
docker compose up --build --wait
docker compose logs --tail 100 app
docker compose down
```

`down` retains the named database volume. Do not use `down -v` unless you intend
to permanently delete the development data. Database passwords are generated
as URL-safe hex; custom passwords with reserved URL characters require an
appropriately encoded database URL and Compose customization.

## Python-only workflow

Install Python 3.11+ (3.12 is the container baseline). A real interpreter must be
on PATH, not only the Windows Store alias.

```powershell
./setup.ps1 -LocalPython
./run.ps1 -LocalPython
.\.venv\Scripts\agent-blueprint.exe doctor
```

Linux/macOS equivalents: `bash setup.sh --local-python` and
`bash run.sh --local-python`. Container equivalents are `bash setup.sh` and
`bash run.sh`. Python mode uses SQLite in ignored `data/`, suitable for isolated
tests and a single local process. It is not a production database recommendation.

## Generic spec workflow

Run the CLI from the checkout root after installing the package in the virtual
environment. Activate it or invoke its full path as above.

```powershell
Copy-Item templates/use-case.yaml my-use-case.yaml
# Edit the name, problem, requirements, personas, constraints and acceptance criteria.
agent-blueprint create my-use-case.yaml
agent-blueprint validate service-request-routing
agent-blueprint approve service-request-routing --reviewer your-name
agent-blueprint run service-request-routing next
# Or prepare all tasks: agent-blueprint run service-request-routing all
```

The first command compiles three proposals, not source code. The input is a
structured problem statement; free-form prose is not automatically interpreted
as complete requirements. Review technology choices and fill gaps before approval.
The `run` command produces a selected teaching/execution plan for a developer/coding agent.
It does not launch a hidden agent, run arbitrary YAML commands, or claim work was
completed. After implementing, record evidence inside the solution:

```powershell
agent-blueprint complete service-request-routing TASK-CAP-DATA --reviewer your-name --evidence implementation/database/task-cap-data-evidence.md
agent-blueprint status service-request-routing
```

Completion is a local developer attestation, not cryptographic identity or a CI
result. Evidence hashes and the complete spec digest invalidate receipts when
inputs change. Define task dependency IDs in `decomposition/tasks.yaml`; missing
prerequisites mark planned work blocked and prevent downstream completion. Re-run validation after
editing specs and update upstream digests deliberately using the helper in
`src.blueprint.specs` only after reviewing the dependent content.

For capability-only creation, staged design/decomposition, database/backend/agent/UI
tasks, numbered module selection, all-mode execution and lessons at each step,
follow [the guided workflow](workflow.md). The coding agent executes the selected
plan; the CLI never claims a generated plan is implemented software.

## Models and optional local inference

No LLM is required for document parsing, manual fact review, scoring or the offline
test suite. To enable model-assisted proposals, configure `.env` following
[provider guidance](providers.md), set the exact model, verify structured-output
support and explicitly set `ALLOW_DOCUMENT_LLM=true`. Do this only after approving
the transfer of the selected document text to that provider. No API key is bundled.

The optional `local-ai` Compose profile caps Ollama at 8 GiB. Choose and pull a
model yourself; the profile does not promise a particular model will fit.

```powershell
docker compose --profile local-ai up -d
# After choosing an appropriately sized model:
docker compose exec ollama ollama pull <your-model>
```

For app-container calls use `LLM_PROVIDER=ollama` and
`LLM_BASE_URL=http://ollama:11434/v1`; Python mode uses localhost. Set the exact
model and its capability flags. Restart the app after changing environment values.
Cloud is the default provider configuration, with no model or credentials guessed.

## Verification

```powershell
python -m ruff check src scripts
python -m ruff format --check src scripts
python -m pytest -q
python -m src.evals.eval_harness
python -m scripts.validate_repo
python -m pip_audit -r requirements.txt
docker compose config --quiet
```

Do not print full `docker compose config`: it expands secrets. `--quiet` validates
without rendering credentials. Review [validation findings](validation-report.md)
for what was actually executed and what remains unverified.

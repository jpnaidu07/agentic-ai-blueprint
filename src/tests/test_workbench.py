"""Workbench security and orchestration contracts; model traffic uses intercepted HTTP."""

import json
import shutil
import threading
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from src.blueprint import specs
from src.blueprint.models import UseCase
from src.workbench.jobs import Jobs
from src.workbench.providers import Providers, strict_schema
from src.workbench.runtime import Runtime, source_digest
from src.workbench.security import WorkbenchError, local_path
from src.workbench.server import create_app

ROOT = Path(__file__).resolve().parents[2]
PAIR_TOKEN = "local-test-pairing-token-1234567890"
FAKE_KEY = "not-a-real-provider-key-987654321"


class FakeRuntime(Runtime):
    verifications = 0
    test_exit_code = 0

    def application_model(self, solution):
        # Lifecycle has its own tests; orchestration consumes a measured-config fixture.
        return {
            "provider": "ollama",
            "model": "synthetic-local",
            "base_url": "http://127.0.0.1:11434/v1",
            "embedding_model": "synthetic-embedding",
        }

    def runner_ready(self):
        return "intercepted-docker"

    def verify(self, solution):
        self.verifications += 1
        return {
            "exit_code": self.test_exit_code,
            "output": "Intercepted test result for orchestration testing only",
            "source_digest": source_digest(
                specs.safe_solution(self.root, solution) / "implementation/runtime"
            ),
            "isolation": "mocked boundary; not a real container test",
        }

    def close(self):
        pass


class ModelFixture:
    def __init__(self):
        self.case = UseCase.model_validate(specs.read_yaml(ROOT / "templates/use-case.yaml"))
        self.calls = []
        self.unsafe_path = None
        self.incomplete_lesson = False
        self.invalid_recommendations = 0

    def handle(self, request):
        self.calls.append(request)
        if request.method == "GET":
            if request.url.path == "/v1beta/models":
                return httpx.Response(
                    200,
                    json={
                        "models": [
                            {
                                "name": "models/test-model",
                                "supportedGenerationMethods": ["generateContent"],
                            },
                            {
                                "name": "models/test-embedding",
                                "supportedGenerationMethods": ["embedContent"],
                            },
                        ]
                    },
                )
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        payload = json.loads(request.content)
        properties = payload["response_format"]["json_schema"]["schema"]["properties"]
        if "ok" in properties:
            output = {"ok": True}
        elif "problem" in properties:
            brief = json.loads(payload["messages"][1]["content"])["brief"]
            self.case = self.case.model_copy(update={"name": brief["name"]})
            output = self.case.model_dump()
        elif "modules" in properties:
            output = specs.compile_specs(self.case)[1]
        elif "tasks" in properties:
            output = specs.compile_specs(self.case)[2]
        elif "files" in properties:
            output = {
                "lesson": {
                    "concept": "A relational record stores a request under a stable identity.",
                    "use_case": "Support operators need durable ownership and request history.",
                    "alternatives": "Files simplify a tiny prototype; a queue transports events but does not replace request storage.",
                    "benefits_and_costs": "Constraints improve integrity while migrations and indexes add maintenance.",
                    "advanced": "Transactions prevent partial writes; revision checks reject conflicting updates.",
                    "experiment": "Proposed: insert a request, retry it, and reject an unknown team; inspect stored rows.",
                    "check_understanding": "Can a queue count current requests? Rubric: use the authoritative request records.",
                    "interview": "This fixture tests orchestration only and does not claim a real customer deployment.",
                },
                "files": [
                    {
                        "path": self.unsafe_path or "records.py",
                        "content": "def valid_request(value):\n    return isinstance(value, str) and bool(value.strip())\n",
                    },
                    {
                        "path": "tests/test_records.py",
                        "content": "from records import valid_request\ndef test_nonempty_request():\n    assert valid_request('help')\n    assert not valid_request('')\n",
                    },
                ],
                "verification": "Run the scoped acceptance tests in the isolated runner.",
                "manual_steps": [],
                "summary": "A small synthetic implementation used solely to verify orchestration mechanics.",
            }
        elif "candidates" in properties:
            if self.invalid_recommendations:
                self.invalid_recommendations -= 1
                return httpx.Response(
                    200,
                    json={
                        "model": "test-model",
                        "choices": [{"finish_reason": "stop", "message": {"content": "not JSON"}}],
                    },
                )
            output = {
                "summary": "Use the connected helper for demanding work and validate the smaller local candidate on representative tasks.",
                "candidates": [
                    {
                        "model": "qwen3:8b",
                        "deployment": "local",
                        "recommendation": "recommended",
                        "best_for": "Specification and implementation work for this solution.",
                        "rationale": "The connected model passed schema compatibility, while solution quality remains unmeasured.",
                        "validation": "Run capability extraction and grounded-answer acceptance cases before selecting it.",
                    },
                    {
                        "model": "qwen3:4b",
                        "deployment": "local",
                        "recommendation": "conditional",
                        "best_for": "Private drafts and small local experiments.",
                        "rationale": "The deterministic screen estimates sufficient memory but does not establish output quality.",
                        "validation": "Run the same acceptance set and measure latency, abstention, and structured-output success.",
                    },
                ],
                "limitations": ["No use-case benchmark has been executed."],
            }
        else:
            output = {
                "answer": "Compare task acceptance before choosing a model.",
                "next_steps": ["Run representative cases"],
                "limitations": ["No quality benchmark was measured"],
            }
        if self.incomplete_lesson and "files" in output:
            del output["lesson"]["alternatives"]
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(output)}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
        )


@pytest.fixture
def workbench(tmp_path):
    for folder in ("skills", "templates", "blueprint", "docs"):
        shutil.copytree(ROOT / folder, tmp_path / folder)
    (tmp_path / "solutions").mkdir()
    for name in ("README.md", "requirements.txt", "requirements-dev.txt"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    model = ModelFixture()
    providers = Providers(transport=httpx.MockTransport(model.handle))
    app = create_app(tmp_path, PAIR_TOKEN, 8080, providers, FakeRuntime)
    with TestClient(app, base_url="http://127.0.0.1:8080", client=("127.0.0.1", 12345)) as client:
        yield client, tmp_path, model


def pair(client):
    response = client.post("/api/session", headers={"Authorization": f"Bearer {PAIR_TOKEN}"})
    assert response.status_code == 200, response.text
    assert "set-cookie" not in response.headers
    result = response.json()
    client.headers.update(
        {"Authorization": f"Bearer {result['session_token']}", "X-Workbench-CSRF": result["csrf"]}
    )
    return result


def connect(client):
    response = client.post(
        "/api/connection",
        json={"provider": "openai", "model": "test-model", "api_key": FAKE_KEY, "consent": True},
    )
    assert response.status_code == 200, response.text
    assert FAKE_KEY not in response.text


def finish_job(client, response):
    assert response.status_code == 200, response.text
    job_id = response.json()["id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["state"] != "running":
            return job
        time.sleep(0.02)
    pytest.fail("Workbench test job did not finish")


def create_solution(client):
    job = finish_job(
        client,
        client.post(
            "/api/solutions",
            json={
                "name": "generated-service",
                "problem": "Employees need a safe service to track and route internal support requests.",
            },
        ),
    )
    assert job["state"] == "succeeded", job
    job = finish_job(
        client, client.post("/api/solutions/generated-service/stages", json={"stage": "remaining"})
    )
    assert job["state"] == "succeeded", job
    detail = client.get("/api/solutions/generated-service").json()
    response = client.post(
        "/api/solutions/generated-service/approve",
        json={"reviewer": "test-reviewer", "confirmed": True, "spec_digest": detail["spec_digest"]},
    )
    assert response.status_code == 200, response.text


def test_pairing_origin_host_csrf_and_remote_boundaries(workbench):
    client, _, _ = workbench
    assert client.get("/").status_code == 200
    assert client.get("/api/solutions").status_code == 401
    assert client.get("/api/health", headers={"Host": "attacker.example:8080"}).status_code == 403
    assert (
        client.post(
            "/api/session",
            headers={"Authorization": f"Bearer {PAIR_TOKEN}", "Origin": "https://attacker.example"},
        ).status_code
        == 403
    )
    pair(client)
    assert client.get("/api/catalog").status_code == 200
    assert (
        client.post(
            "/api/actions",
            headers={"X-Workbench-CSRF": ""},
            json={"action": "build-runner", "confirmed": True},
        ).status_code
        == 403
    )
    with TestClient(
        client.app, base_url="http://127.0.0.1:8080", client=("192.168.1.2", 12345)
    ) as remote:
        assert remote.get("/").status_code == 403
    assert client.get("/").headers["content-security-policy"].find("script-src 'self'") >= 0


def test_catalog_exposes_production_rag_guidance(workbench):
    client, _, _ = workbench
    pair(client)
    items = client.get("/api/catalog").json()["items"]
    ids = {item["id"] for item in items}
    skill = "skills/production-rag/SKILL.md"
    interview = "skills/production-rag/references/interview-story.md"
    assert {skill, interview} <= ids
    assert (
        "trustworthy evidence boundary"
        in client.get("/api/catalog/content", params={"item": interview}).json()["content"]
    )


def test_environment_uses_offline_baseline_without_connected_helper(workbench):
    client, _, model = workbench
    pair(client)
    response = client.get("/api/system")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["local_models"]} == {
        "qwen3:4b",
        "qwen3:8b",
    }
    assert model.calls == []


def test_local_lifecycle_profile_does_not_require_helper(workbench):
    client, root, model = workbench
    pair(client)
    (root / "solutions/local-exercise").mkdir()
    profile = json.loads((ROOT / "templates/local-model-profile.json").read_text())
    assert client.put("/api/solutions/local-exercise/models", json=profile).status_code == 200
    result = client.get("/api/solutions/local-exercise/models").json()
    assert result["profile"]["inference_model"] == "qwen3:4b"
    assert result["approval"] is None
    assert not model.calls
    assert (
        client.post(
            "/api/solutions/local-exercise/models/train", json={"confirmed": False}
        ).status_code
        == 409
    )


def test_connected_helper_ranks_hardware_candidates_for_selected_solution(workbench):
    client, _, model = workbench
    pair(client)
    connect(client)
    calls_before = len(model.calls)
    response = client.post(
        "/api/system/recommendations",
        json={"solution": "government-tender-processing"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["source"] == "connected-helper"
    assert result["solution"] == "government-tender-processing"
    assert [item["model"] for item in result["candidates"]] == ["qwen3:8b", "qwen3:4b"]
    assert len(model.calls) == calls_before + 1
    request = json.loads(model.calls[-1].content)
    supplied = json.loads(request["messages"][1]["content"])
    assert "specifications" in supplied
    assert supplied["hardware_and_local_tools"]["local_models"]
    assert FAKE_KEY not in model.calls[-1].content.decode()


def test_helper_recommendation_retries_one_invalid_structured_response(workbench):
    client, _, model = workbench
    pair(client)
    connect(client)
    model.invalid_recommendations = 1
    calls_before = len(model.calls)
    response = client.post("/api/system/recommendations", json={"solution": None})
    assert response.status_code == 200, response.text
    assert response.json()["candidates"][0]["model"] == "qwen3:8b"
    assert len(model.calls) == calls_before + 2


def test_keys_are_not_echoed_stored_or_reused_without_consent(workbench):
    client, root, model = workbench
    pair(client)
    bad = client.post("/api/connection", json={"provider": "arbitrary-host", "api_key": FAKE_KEY})
    assert bad.status_code == 422 and FAKE_KEY not in bad.text
    denied = client.post(
        "/api/connection",
        json={"provider": "openai", "model": "test-model", "api_key": FAKE_KEY, "consent": False},
    )
    assert denied.status_code == 409 and not model.calls
    connect(client)
    job = finish_job(
        client, client.post("/api/ask", json={"text": "Which model should I evaluate?"})
    )
    assert job["state"] == "succeeded"
    assert FAKE_KEY not in json.dumps(job)
    assert FAKE_KEY.encode() not in (root / ".workbench/jobs.sqlite").read_bytes()
    assert client.delete("/api/connection").status_code == 200
    assert client.post("/api/ask", json={"text": "Explain the next step"}).status_code == 409
    assert all(request.url.host == "api.openai.com" for request in model.calls)


def test_session_resume_keeps_connection_without_new_probe_and_logout_revokes_it(workbench):
    client, _, model = workbench
    credentials = pair(client)
    connect(client)
    calls_before = len(model.calls)
    resumed = client.get("/api/session")
    assert resumed.status_code == 200
    assert resumed.json()["connected"] is True
    assert resumed.json()["model"] == "test-model"
    assert resumed.json()["csrf"] == credentials["csrf"]
    assert FAKE_KEY not in resumed.text
    assert "set-cookie" not in resumed.headers
    assert len(model.calls) == calls_before
    assert client.delete("/api/session").status_code == 200
    assert client.get("/api/session").status_code == 401


def test_model_backed_stages_generation_and_verification_are_distinct(workbench):
    client, root, _ = workbench
    pair(client)
    connect(client)
    create_solution(client)
    path = root / "solutions/generated-service"
    assert not (path / "implementation/runtime").exists()
    generated = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run", json={"selector": "next", "confirmed": True}
        ),
    )
    assert generated["state"] == "succeeded", generated
    assert (path / "implementation/runtime/records.py").is_file()
    assert not (path / "implementation/receipts").exists()
    assert client.app.state.runtime.verifications == 0
    tested = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run",
            json={"selector": "next", "confirmed": True, "execute": True},
        ),
    )
    assert tested["state"] == "succeeded", tested
    specs.require_dependencies(path, ["TASK-CAP-DATA"])
    assert client.app.state.runtime.verifications == 1
    assert (root / ".workbench/verified/generated-service.json").is_file()
    # A later task may edit integrated source without mutating the immutable tested snapshot.
    later = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run",
            json={"selector": "next", "confirmed": True, "execute": True},
        ),
    )
    assert later["state"] == "succeeded", later
    specs.require_dependencies(path, ["TASK-CAP-01"])


@pytest.mark.parametrize(
    "provider,host", [("gemini", "generativelanguage.googleapis.com"), ("ollama", "127.0.0.1")]
)
def test_alternate_workbench_provider_probe_and_model_listing(workbench, provider, host):
    client, _, model = workbench
    pair(client)
    response = client.post(
        "/api/providers/models", json={"provider": provider, "api_key": FAKE_KEY}
    )
    assert response.status_code == 200, response.text
    assert response.json()["models"] == ["test-model"]
    if provider == "gemini":
        listing = model.calls[-1]
        assert listing.url.path == "/v1beta/models"
        assert listing.headers["x-goog-api-key"] == FAKE_KEY
        assert "authorization" not in listing.headers
    response = client.post(
        "/api/connection",
        json={
            "provider": provider,
            "model": "test-model",
            "api_key": FAKE_KEY if provider != "ollama" else "",
            "consent": True,
        },
    )
    assert response.status_code == 200, response.text
    assert all(request.url.host == host for request in model.calls)

    # The browser clears key inputs after connection. A later list/refresh reuses
    # only the matching provider credential retained in this server-side session.
    response = client.post("/api/providers/models", json={"provider": provider, "api_key": ""})
    assert response.status_code == 200, response.text
    assert response.json()["models"] == ["test-model"]


def test_model_cannot_write_host_paths_or_skip_confirmation(workbench):
    client, root, model = workbench
    pair(client)
    connect(client)
    create_solution(client)
    denied = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run", json={"selector": "next", "confirmed": False}
        ),
    )
    assert denied["state"] == "blocked"
    model.unsafe_path = "../../../outside.py"
    blocked = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run", json={"selector": "next", "confirmed": True}
        ),
    )
    assert blocked["state"] == "blocked"
    assert not (root / "outside.py").exists()
    assert not (root / "solutions/generated-service/implementation/runtime").exists()
    assert client.get("/api/catalog/content", params={"item": "../.env"}).status_code == 404
    denied = finish_job(
        client, client.post("/api/actions", json={"action": "install-ollama", "confirmed": False})
    )
    assert denied["state"] == "blocked"


def test_setup_actions_are_workspace_scoped_and_rerunnable(workbench):
    client, _, _ = workbench
    pair(client)
    runtime = client.app.state.runtime
    runtime.action = lambda body, event: {"message": "setup complete"}
    first = finish_job(
        client,
        client.post("/api/actions", json={"action": "start-ollama", "confirmed": True}),
    )
    assert first["state"] == "succeeded"
    assert first["solution"] is None
    assert first["request"]["action"] == "start-ollama"
    second = finish_job(
        client,
        client.post("/api/actions", json={"action": "start-ollama", "confirmed": True}),
    )
    assert second["state"] == "succeeded"


def test_editor_optimistic_concurrency_and_stale_approval(workbench):
    client, root, _ = workbench
    pair(client)
    connect(client)
    create_solution(client)
    detail = client.get("/api/solutions/generated-service").json()
    file = next(f for f in detail["files"] if f["path"] == "capability/capability.yaml")
    text = file["content"].replace(
        "Internal service request routing", "Revised internal service request routing"
    )
    body = {"section": "capability", "content": text, "sha256": file["sha256"], "confirmed": True}
    assert client.put("/api/solutions/generated-service/specs", json=body).status_code == 200
    assert client.put("/api/solutions/generated-service/specs", json=body).status_code == 409
    with pytest.raises(ValueError, match="stale"):
        specs.require_approval(root / "solutions/generated-service")


def test_teaching_is_loaded_for_stages_and_tasks_and_retained(workbench):
    client, root, model = workbench
    pair(client)
    connect(client)
    create_solution(client)
    stage_calls = [json.loads(call.content) for call in model.calls if call.method == "POST"][1:]
    for stage, call in zip(specs.STAGES, stage_calls, strict=True):
        primer = (root / f"skills/{stage}/references/learning.md").read_text(encoding="utf-8")
        assert primer in call["messages"][0]["content"]
    lesson_path = root / "skills/database/references/learning.md"
    revised = "Current database teaching revision, with a local experiment for this learner."
    lesson_path.write_text(revised, encoding="utf-8")
    job = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run",
            json={"selector": "next", "confirmed": True, "execute": True},
        ),
    )
    assert job["state"] == "succeeded", job
    assert revised in json.loads(model.calls[-1].content)["messages"][0]["content"]
    assert any(revised in event["message"] for event in job["events"])
    lesson = job["result"]["tasks"][0]["lesson"]
    assert "Support operators" in lesson
    evidence = (
        root / "solutions/generated-service/implementation/database/task-cap-data-evidence.md"
    )
    assert lesson.splitlines()[1] in evidence.read_text(encoding="utf-8")
    refs = {row["id"] for row in client.get("/api/catalog").json()["items"]}
    assert "docs/fde-learning.md" in refs
    assert all(
        f"skills/{name}/references/learning.md" in refs for name in [*specs.STAGES, *specs.SKILLS]
    )


def test_incomplete_teaching_cannot_write_code_or_issue_receipts(workbench):
    client, root, model = workbench
    pair(client)
    connect(client)
    create_solution(client)
    model.incomplete_lesson = True
    job = finish_job(
        client,
        client.post(
            "/api/solutions/generated-service/run",
            json={"selector": "next", "confirmed": True, "execute": True},
        ),
    )
    assert job["state"] in {"blocked", "failed"}, job
    path = root / "solutions/generated-service/implementation"
    assert not (path / "runtime").exists()
    assert not (path / "receipts").exists()
    assert client.app.state.runtime.verifications == 0


def test_schema_requires_all_properties_recursively():
    schema = strict_schema(UseCase)
    assert set(schema["required"]) == set(schema["properties"])
    assert set(schema["$defs"]["Requirement"]["required"]) == set(
        schema["$defs"]["Requirement"]["properties"]
    )
    assert schema["additionalProperties"] is False


def test_failed_tests_block_receipts_and_inform_next_attempt(workbench):
    client, root, model = workbench
    pair(client)
    connect(client)
    create_solution(client)
    runtime = client.app.state.runtime
    runtime.test_exit_code = 1
    body = {"selector": "next", "confirmed": True, "execute": True}
    failed = finish_job(client, client.post("/api/solutions/generated-service/run", json=body))
    assert failed["state"] == "needs-attention", failed
    assert failed["result"]["tasks"][0]["verification"]["exit_code"] == 1
    assert not (root / ".workbench/verified/generated-service.json").exists()
    assert not (root / "solutions/generated-service/implementation/receipts").exists()
    runtime.test_exit_code = 0
    retried = finish_job(client, client.post("/api/solutions/generated-service/run", json=body))
    assert retried["state"] == "succeeded", retried
    prompt = json.loads(model.calls[-1].content)["messages"][1]["content"]
    assert json.loads(prompt)["previous_attempt"]["verification"]["exit_code"] == 1


def test_malformed_model_output_cannot_publish_specifications(workbench):
    client, root, _ = workbench
    pair(client)
    connect(client)
    client.app.state.engine.providers.transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": '{"not_a_spec": true}'}}
                ]
            },
        )
    )
    result = finish_job(
        client,
        client.post(
            "/api/solutions",
            json={
                "name": "invalid-proposal",
                "problem": "A synthetic business problem that needs a reviewed capability specification.",
            },
        ),
    )
    assert result["state"] in {"blocked", "failed"}
    assert not (root / "solutions/invalid-proposal").exists()


def test_request_body_limit_and_no_cookie_authentication(workbench):
    client, _, _ = workbench
    session = pair(client)
    assert client.post("/api/ask", content=b"x" * 2_000_001).status_code == 413
    assert (
        client.get(
            "/api/catalog",
            headers={"Authorization": "", "Cookie": f"session={session['session_token']}"},
        ).status_code
        == 401
    )


def test_jobs_single_writer_cancellation_and_restart(tmp_path):
    jobs = Jobs(tmp_path)
    started, release = threading.Event(), threading.Event()

    def work(job):
        started.set()
        release.wait(3)
        jobs.check_cancelled()

    job = jobs.start("test", "example", work)
    assert started.wait(2)
    with pytest.raises(WorkbenchError, match="Another"):
        jobs.start("second", None, lambda _: None)
    jobs.cancelled.set()
    release.set()
    deadline = time.monotonic() + 3
    while jobs.active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert jobs.get(job["id"])["state"] == "cancelled"
    with jobs.db() as conn:
        conn.execute("UPDATE jobs SET state='running'")
    assert Jobs(tmp_path).get(job["id"])["state"] == "interrupted"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.py",
        "/etc/passwd",
        "C:/Windows/file",
        "file:stream",
        ".env",
        "a/../../file",
        "a\\file.py",
        "CON.py",
        "sub/NUL.txt",
        "file.py.",
        "trailing /test.py",
        "file?.py",
    ],
)
def test_generated_path_boundaries(tmp_path, path):
    with pytest.raises(WorkbenchError):
        local_path(tmp_path, path)


def test_real_tender_launch_health_roles_and_no_model_transfer(tmp_path):
    runtime = Runtime(ROOT, tmp_path)
    runtime.local_models = type(
        "ApprovedModels",
        (),
        {
            "approved": lambda _self, _name: {
                "provider": "ollama",
                "model": "qwen3:4b",
                "base_url": "http://127.0.0.1:11434/v1",
                "context_window": 4096,
                "max_tokens": 256,
                "embedding_model": "embeddinggemma",
            }
        },
    )()
    try:
        result = runtime.launch_tender()
        url = result["url"]
        with httpx.Client(base_url=url, timeout=10, trust_env=False) as client:
            assert client.get("/api/me").status_code == 401
            for role, token in runtime.apps["government-tender-processing"]["tokens"].items():
                assert (
                    client.get("/api/me", headers={"Authorization": f"Bearer {token}"}).json()[
                        "role"
                    ]
                    == role
                )
        assert (tmp_path / "tender.sqlite").exists()
        assert "tokens" not in result
    finally:
        runtime.close()

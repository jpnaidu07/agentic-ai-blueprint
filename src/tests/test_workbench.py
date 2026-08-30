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

    def handle(self, request):
        self.calls.append(request)
        if request.method == "GET":
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
                "lesson": "Create durable request records and verify the contract.",
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
        else:
            output = {
                "answer": "Compare task acceptance before choosing a model.",
                "next_steps": ["Run representative cases"],
                "limitations": ["No quality benchmark was measured"],
            }
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

"""Lifecycle evidence, stale approvals and local-only provider boundaries."""

import json
from types import SimpleNamespace

import httpx
import pytest

from src.workbench import local_models
from src.workbench.local_models import LocalModels, LocalProfile, save_profile
from src.workbench.security import WorkbenchError


@pytest.fixture
def lifecycle(tmp_path, monkeypatch):
    (tmp_path / "solutions/example-service").mkdir(parents=True)
    profile = LocalProfile(
        evaluation=[{"prompt": f"What is item number {n}?", "answer": str(n)} for n in range(3)]
    )
    save_profile(tmp_path, "example-service", profile)
    calls = []

    def handle(request):
        calls.append(request)
        assert request.url.host == "127.0.0.1"
        data = json.loads(request.content)
        if request.url.path == "/api/embed":
            return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})
        answer = data["messages"][-1]["content"].split()[-1].strip("?")
        return httpx.Response(200, json={"message": {"content": answer}})

    client = httpx.Client
    monkeypatch.setattr(
        local_models.httpx,
        "Client",
        lambda **kwargs: client(**kwargs, transport=httpx.MockTransport(handle)),
    )
    jobs = SimpleNamespace(event=lambda *args: None, check_cancelled=lambda: None)
    instance = LocalModels(tmp_path, tmp_path / ".workbench", SimpleNamespace(), jobs)
    return instance, profile, calls


def test_real_scoring_and_profile_change_invalidates_approval(lifecycle):
    instance, profile, calls = lifecycle
    report = instance.evaluate("example-service", "test-job")
    assert report["accuracy"] == 1 and report["passed"]
    assert report["embedding_dimensions"] == 3
    assert len(calls) == 4
    result = instance.approve("example-service", report["id"])
    assert result["configuration"]["provider"] == "ollama"
    assert "api_key" not in json.dumps(result)
    save_profile(
        instance.root, "example-service", profile.model_copy(update={"inference_model": "qwen3:8b"})
    )
    assert instance.approved("example-service", required=False) is None
    with pytest.raises(WorkbenchError, match="changed"):
        instance.approved("example-service")


def test_training_evaluation_overlap_is_rejected(lifecycle):
    instance, profile, _ = lifecycle
    profile.training = [profile.evaluation[0]]
    with pytest.raises(WorkbenchError, match="separate"):
        save_profile(instance.root, "example-service", profile)


def test_failed_quality_cannot_be_approved(lifecycle):
    instance, profile, _ = lifecycle
    profile.evaluation[0].answer = "a different expected answer"
    save_profile(instance.root, "example-service", profile)
    report = instance.evaluate("example-service", "test-job")
    assert not report["passed"]
    with pytest.raises(WorkbenchError, match="passing"):
        instance.approve("example-service", report["id"])


def test_profile_paths_cannot_escape_solution(lifecycle):
    instance, profile, _ = lifecycle
    with pytest.raises((ValueError, WorkbenchError)):
        save_profile(instance.root, "../../other", profile)


def test_new_application_requires_a_passing_local_model(lifecycle):
    from src.workbench.runtime import Runtime

    instance, _, _ = lifecycle
    runtime = Runtime(instance.root, instance.state)
    runtime.local_models = instance
    with pytest.raises(WorkbenchError, match="Evaluate and approve"):
        runtime.application_model("example-service")


def test_approved_baseline_must_still_be_installed_and_running(lifecycle, monkeypatch):
    instance, profile, _ = lifecycle
    report = instance.evaluate("example-service", "test-job")
    instance.approve("example-service", report["id"])
    monkeypatch.setattr(
        "src.workbench.system.inspect_system",
        lambda root: {"tools": {"ollama_ready": False}, "installed_models": []},
    )
    with pytest.raises(WorkbenchError, match="Start Ollama"):
        instance.approved("example-service")
    monkeypatch.setattr(
        "src.workbench.system.inspect_system",
        lambda root: {
            "tools": {"ollama_ready": True},
            "installed_models": [profile.inference_model, profile.embedding_model],
        },
    )
    assert instance.approved("example-service")["model"] == profile.inference_model


def test_gateway_uses_only_selected_local_model_and_bounded_config(monkeypatch):
    from fastapi.testclient import TestClient

    from src.workbench import model_gateway

    monkeypatch.setenv("MODEL_GATEWAY_TOKEN", "synthetic-token")
    monkeypatch.setenv(
        "MODEL_GATEWAY_CONFIG",
        json.dumps(
            {
                "provider": "ollama",
                "model": "qwen3:4b",
                "base_url": "http://127.0.0.1:11434/v1",
                "embedding_model": "embeddinggemma",
                "context_window": 4096,
                "max_tokens": 128,
            }
        ),
    )
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "12 May"}})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        model_gateway.httpx,
        "AsyncClient",
        lambda **kw: real_client(**kw, transport=httpx.MockTransport(handle)),
    )
    with TestClient(model_gateway.app) as client:
        response = client.post(
            "/v1/chat",
            headers={"authorization": "Bearer synthetic-token"},
            json={
                "model": "qwen3:4b",
                "messages": [{"role": "user", "content": "Give a date"}],
                "max_tokens": 999999,
                "base_url": "https://untrusted.invalid",
            },
        )
        assert response.status_code == 200
        assert response.json()["choices"][0]["message"]["content"] == "12 May"
        assert str(calls[0].url) == "http://127.0.0.1:11434/api/chat"
        assert json.loads(calls[0].content)["options"]["num_predict"] == 128
        assert "authorization" not in calls[0].headers
        assert (
            client.post(
                "/v1/chat",
                headers={"authorization": "Bearer synthetic-token"},
                json={"model": "another-model"},
            ).status_code
            == 422
        )


def test_gateway_rejects_browser_and_unknown_operations(monkeypatch):
    from fastapi.testclient import TestClient

    from src.workbench.model_gateway import app

    monkeypatch.setenv("MODEL_GATEWAY_TOKEN", "synthetic-token")
    with TestClient(app) as client:
        assert client.post("/v1/chat", json={}).status_code == 403
        assert (
            client.post(
                "/v1/chat",
                headers={
                    "authorization": "Bearer synthetic-token",
                    "origin": "http://example.invalid",
                },
                json={},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/v1/pull", headers={"authorization": "Bearer synthetic-token"}, json={}
            ).status_code
            == 404
        )

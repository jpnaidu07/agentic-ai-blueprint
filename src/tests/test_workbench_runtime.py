"""Real Docker boundary tests. CI builds the image; local runs opt in explicitly."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from src.blueprint import specs
from src.workbench.runtime import Runtime
from src.workbench.security import WorkbenchError
from src.workbench.system import command

pytestmark = pytest.mark.skipif(
    os.getenv("BLUEPRINT_DOCKER_TESTS") != "1", reason="Requires explicitly enabled Docker runner"
)
ROOT = Path(__file__).resolve().parents[2]


def test_real_isolated_tests_preview_health_and_stale_source(tmp_path):
    path = specs.create(tmp_path, ROOT / "templates/use-case.yaml")
    specs.approve(path, "container-test-reviewer")
    source = path / "implementation/runtime"
    (source / "tests").mkdir(parents=True)
    (source / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('/api/health')\ndef health(): return {'status': 'ok'}\n"
    )
    (source / "tests/test_contract.py").write_text(
        "import os, socket\nfrom pathlib import Path\nimport pytest\n"
        "from fastapi.testclient import TestClient\nfrom app import app\n"
        "def test_health():\n    assert TestClient(app).get('/api/health').json() == {'status': 'ok'}\n"
        "def test_process_boundary():\n"
        "    assert os.getuid() == 65534\n"
        "    assert 'OPENAI_API_KEY' not in os.environ\n"
        "    assert 'GEMINI_API_KEY' not in os.environ\n"
        "    assert 'WORKBENCH_TOKEN' not in os.environ\n"
        "    assert not Path('/var/run/docker.sock').exists()\n"
        "    assert not Path('/app/requirements.txt').exists()\n"
        "    with pytest.raises(OSError): Path('/app/escape.txt').write_text('denied')\n"
        "    with pytest.raises(OSError): Path('/escape.txt').write_text('denied')\n"
        "    with pytest.raises(OSError): socket.create_connection(('1.1.1.1', 443), timeout=1)\n"
    )
    state = tmp_path / ".workbench"
    state.mkdir()
    runtime = Runtime(tmp_path, state)
    try:
        tested = runtime.verify(path.name)
        assert tested["exit_code"] == 0, tested["output"]
        assert "2 passed" in tested["output"]
        assert not runtime.active_tests
        ledger = state / "verified" / f"{path.name}.json"
        ledger.parent.mkdir()
        ledger.write_text(
            json.dumps(
                {"source_digest": tested["source_digest"], "spec_digest": specs.spec_digest(path)}
            )
        )
        result = runtime.launch_generated(path.name)
        assert httpx.get(result["url"] + "/api/health", timeout=10, trust_env=False).json() == {
            "status": "ok"
        }
        managed = runtime.apps[path.name]
        assert runtime.running(managed)
        inspection = command([runtime.docker(), "inspect", managed["name"]])
        config = json.loads(inspection.stdout)[0]
        assert config["HostConfig"]["ReadonlyRootfs"]
        assert config["HostConfig"]["Memory"] == 1024**3
        assert config["HostConfig"]["PidsLimit"] == 128
        assert not any(config["NetworkSettings"]["Ports"].values())
        assert len(config["NetworkSettings"]["Networks"]) == 1
        relay = command([runtime.docker(), "inspect", managed["proxy_name"]])
        relay_config = json.loads(relay.stdout)[0]
        assert relay_config["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostIp"] == "127.0.0.1"
        assert len(relay_config["NetworkSettings"]["Networks"]) == 2
        assert all(mount["Type"] == "tmpfs" for mount in relay_config["Mounts"])
        assert relay_config["HostConfig"]["Memory"] == 256 * 1024**2
        network = command([runtime.docker(), "network", "inspect", f"blueprint-{runtime.owner}"])
        assert json.loads(network.stdout)[0]["Internal"]
        egress = command(
            [
                runtime.docker(),
                "exec",
                managed["name"],
                "python",
                "-c",
                "import socket,sys\ntry: socket.create_connection(('1.1.1.1',443),timeout=1)\nexcept OSError: sys.exit(0)\nelse: sys.exit(1)",
            ]
        )
        assert egress.returncode == 0, "Generated preview unexpectedly has external network access"
        (source / "app.py").write_text("raise RuntimeError('unverified source')\n")
        with pytest.raises(WorkbenchError, match="changed after verification"):
            runtime.launch_generated(path.name)
        runtime.stop(path.name)
        assert not runtime.running(managed)
    finally:
        runtime.close()


def test_isolated_preview_reaches_only_approved_local_model(tmp_path):
    """Exercise real Docker networking through the authenticated inference gateway."""

    class LocalModel(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            assert self.path == "/v1/chat/completions"
            assert body["model"] == "local-test-model"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"choices": [{"message": {"content": "local-model-response"}}]}).encode()
            )

        def log_message(self, *args):
            pass

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), LocalModel)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    path = specs.create(tmp_path, ROOT / "templates/use-case.yaml")
    specs.approve(path, "gateway-test-reviewer")
    source = path / "implementation/runtime"
    (source / "tests").mkdir(parents=True)
    (source / "app.py").write_text(
        "import os,httpx\nfrom fastapi import FastAPI\napp=FastAPI()\n"
        "@app.get('/api/health')\ndef health(): return {'status':'ok'}\n"
        "@app.get('/api/model')\ndef model():\n"
        "    r=httpx.post(os.environ['LLM_BASE_URL']+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['LLM_API_KEY']},json={'model':os.environ['LLM_MODEL'],'messages':[{'role':'user','content':'local test'}]},timeout=15,trust_env=False)\n"
        "    r.raise_for_status()\n    return r.json()\n"
    )
    (source / "tests/test_health.py").write_text(
        "from fastapi.testclient import TestClient\nfrom app import app\ndef test_health(): assert TestClient(app).get('/api/health').status_code==200\n"
    )
    state = tmp_path / ".workbench"
    state.mkdir()
    runtime = Runtime(tmp_path, state)
    runtime.local_models = SimpleNamespace(
        approved=lambda name: {
            "provider": "openai-compatible",
            "model": "local-test-model",
            "base_url": f"http://127.0.0.1:{upstream.server_port}/v1",
            "embedding_model": "embedding-test",
            "context_window": 4096,
            "max_tokens": 128,
        }
    )
    (path / "models").mkdir()
    (path / "models/profile.json").write_text("{}")
    try:
        tested = runtime.verify(path.name)
        assert tested["exit_code"] == 0, tested["output"]
        ledger = state / "verified" / f"{path.name}.json"
        ledger.parent.mkdir()
        ledger.write_text(
            json.dumps(
                {"source_digest": tested["source_digest"], "spec_digest": specs.spec_digest(path)}
            )
        )
        result = runtime.launch_generated(path.name)
        response = httpx.get(result["url"] + "/api/model", timeout=30, trust_env=False)
        assert response.status_code == 200, response.text
        assert response.json()["choices"][0]["message"]["content"] == "local-model-response"
        assert (
            httpx.post(
                result["url"] + "/model/v1/chat/completions", json={}, trust_env=False
            ).status_code
            == 403
        )
        process = runtime.apps[path.name]["gateway_process"]
        runtime.stop(path.name)
        assert process.poll() is not None
    finally:
        runtime.close()
        upstream.shutdown()
        upstream.server_close()

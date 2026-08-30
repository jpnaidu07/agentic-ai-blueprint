"""Real Docker boundary tests. CI builds the image; local runs opt in explicitly."""

import json
import os
from pathlib import Path

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
        assert config["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostIp"] == "127.0.0.1"
        network = command([runtime.docker(), "network", "inspect", f"blueprint-{runtime.owner}"])
        assert json.loads(network.stdout)[0]["Internal"]
        (source / "app.py").write_text("raise RuntimeError('unverified source')\n")
        with pytest.raises(WorkbenchError, match="changed after verification"):
            runtime.launch_generated(path.name)
        runtime.stop(path.name)
        assert not runtime.running(managed)
    finally:
        runtime.close()

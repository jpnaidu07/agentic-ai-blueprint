"""The trusted relay must never turn user request URLs into arbitrary destinations."""

import httpx
from fastapi.testclient import TestClient

from src.workbench import preview_proxy


def test_proxy_fixed_destination_methods_headers_and_limits(monkeypatch):
    host = "blueprint-app-0123456789-test-service"
    monkeypatch.setenv("UPSTREAM_HOST", host)
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(
            200,
            stream=httpx.ByteStream(b'{"status":"ok"}'),
            headers={"content-type": "application/json", "connection": "x-hop", "x-hop": "discard"},
        )

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        preview_proxy.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(handle)),
    )
    with TestClient(preview_proxy.app) as client:
        result = client.get(
            "/api/health?next=http://untrusted.invalid",
            headers={"connection": "x-secret-hop", "x-secret-hop": "discard"},
        )
        assert result.status_code == 200 and result.json() == {"status": "ok"}
        assert "x-hop" not in result.headers
        assert requests[0].url.host == host and requests[0].url.port == 8000
        assert "x-secret-hop" not in requests[0].headers
        assert client.request("CONNECT", "/untrusted.invalid:443").status_code == 405
        monkeypatch.setattr(preview_proxy, "LIMIT", 8)
        assert client.post("/upload", content=b"too much data").status_code == 413
        assert client.get("/api/health").status_code == 502
        monkeypatch.setenv("UPSTREAM_HOST", "arbitrary.invalid")
        assert client.get("/api/health").status_code == 503

"""Trusted, fixed-upstream HTTP relay for otherwise network-isolated previews.

Runs only in a separate container with no generated source mount or credentials.
No CONNECT, arbitrary destinations, redirects, WebSockets or shell access.
"""

import os
import re
import secrets

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
LIMIT = 16 * 1024 * 1024
HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def clean_headers(headers):
    excluded = HOP_HEADERS | {
        part.strip().lower() for part in headers.get("connection", "").split(",")
    }
    return [(key, value) for key, value in headers.multi_items() if key.lower() not in excluded]


@app.api_route("/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def relay(path: str, request: Request):
    if path in {"model/v1/chat/completions", "model/v1/embeddings"}:
        token = os.getenv("MODEL_GATEWAY_TOKEN", "")
        if (
            not token
            or request.method != "POST"
            or not secrets.compare_digest(
                request.headers.get("authorization", ""), "Bearer " + token
            )
        ):
            return Response(status_code=403)
        port = os.getenv("MODEL_GATEWAY_PORT", "")
        if not port.isdigit() or not 1024 <= int(port) <= 65535:
            return Response(status_code=503)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 64000:
                return Response(status_code=413)
        target = "chat" if path.endswith("completions") else "embeddings"
        try:
            async with httpx.AsyncClient(
                timeout=120, trust_env=False, follow_redirects=False
            ) as client:
                result = await client.post(
                    f"http://host.docker.internal:{port}/v1/{target}",
                    content=bytes(body),
                    headers={
                        "authorization": "Bearer " + token,
                        "content-type": "application/json",
                    },
                )
            return Response(
                result.content, status_code=result.status_code, media_type="application/json"
            )
        except httpx.HTTPError:
            return Response("Local inference gateway is unavailable", status_code=502)
    host = os.getenv("UPSTREAM_HOST", "")
    if not re.fullmatch(r"blueprint-app-[a-f0-9]{10}-[a-z][a-z0-9-]{2,63}", host):
        return Response("Preview relay configuration is invalid.", status_code=503)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > LIMIT:
            return Response("Preview request exceeds 16 MiB.", status_code=413)
    # URL authority is built exclusively from the server-owned container name.
    url = httpx.URL(f"http://{host}:8000").copy_with(
        path="/" + path, query=request.url.query.encode()
    )
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False, follow_redirects=False) as client:
            headers = httpx.Headers(request.headers.items())
            async with client.stream(
                request.method, url, content=bytes(body), headers=clean_headers(headers)
            ) as upstream:
                content = bytearray()
                async for chunk in upstream.aiter_raw():
                    content.extend(chunk)
                    if len(content) > LIMIT:
                        return Response("Preview response exceeds 16 MiB.", status_code=502)
                response = Response(bytes(content), status_code=upstream.status_code)
                response.raw_headers.extend(
                    (key.encode("latin-1"), value.encode("latin-1"))
                    for key, value in clean_headers(upstream.headers)
                )
                return response
    except (httpx.HTTPError, ValueError):
        return Response(
            "The isolated preview is unavailable. Check its implementation and startup.",
            status_code=502,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8080, access_log=False, proxy_headers=False, limit_concurrency=16
    )

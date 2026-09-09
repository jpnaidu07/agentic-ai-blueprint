"""Authenticated fixed-destination local inference gateway for isolated previews."""

import json
import os
import secrets

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.post("/v1/{operation}")
async def inference(operation: str, request: Request):
    token = os.environ["MODEL_GATEWAY_TOKEN"]
    if request.headers.get("origin") or not secrets.compare_digest(
        request.headers.get("authorization", ""), "Bearer " + token
    ):
        return Response(status_code=403)
    if operation not in {"chat", "embeddings"}:
        return Response(status_code=404)
    data = bytearray()
    async for part in request.stream():
        data.extend(part)
        if len(data) > 64000:
            return Response(status_code=413)
    try:
        body = json.loads(data)
        config = json.loads(os.environ["MODEL_GATEWAY_CONFIG"])
        if operation == "chat":
            if body.get("model") != config["model"] or body.get("stream"):
                return Response(status_code=422)
            destination = config["base_url"] + "/chat/completions"
            payload = {
                "model": config["model"],
                "messages": body["messages"],
                "max_tokens": config["max_tokens"],
                "stream": False,
            }
            if "response_format" in body:
                payload["response_format"] = body["response_format"]
            if config["provider"] == "ollama":
                destination = "http://127.0.0.1:11434/api/chat"
                payload = {
                    "model": config["model"],
                    "messages": body["messages"],
                    "stream": False,
                    "think": False,
                    "options": {
                        "num_ctx": config["context_window"],
                        "num_predict": config["max_tokens"],
                        "temperature": 0,
                    },
                }
                if body.get("response_format", {}).get("type") == "json_schema":
                    payload["format"] = body["response_format"]["json_schema"]["schema"]
        else:
            destination = "http://127.0.0.1:11434/api/embed"
            payload = {"model": config["embedding_model"], "input": body["input"]}
        async with httpx.AsyncClient(
            timeout=120, trust_env=False, follow_redirects=False
        ) as client:
            result = await client.post(destination, json=payload)
        if operation == "chat" and config["provider"] == "ollama" and result.status_code == 200:
            output = result.json()
            return JSONResponse(
                {
                    "model": config["model"],
                    "choices": [{"finish_reason": "stop", "message": output["message"]}],
                    "usage": {
                        "prompt_tokens": output.get("prompt_eval_count", 0),
                        "completion_tokens": output.get("eval_count", 0),
                    },
                }
            )
        if operation == "embeddings" and result.status_code == 200:
            return JSONResponse(
                {
                    "model": config["embedding_model"],
                    "data": [
                        {"object": "embedding", "index": i, "embedding": vector}
                        for i, vector in enumerate(result.json()["embeddings"])
                    ],
                }
            )
        return Response(
            result.content, status_code=result.status_code, media_type="application/json"
        )
    except (ValueError, KeyError, httpx.HTTPError):
        return JSONResponse({"error": "Local model request failed"}, 502)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ["MODEL_GATEWAY_PORT"]),
        access_log=False,
        limit_concurrency=4,
    )

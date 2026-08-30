"""Configurable provider adapter. Provider failures never become simulated success."""

import json
import os
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from jsonschema import validate
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMError(RuntimeError):
    """Safe error message, excluding provider bodies and credentials."""


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = "openai"
    model: str = ""
    base_url: str = ""
    api_key: str = Field(default="", repr=False)
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, gt=0, le=1)
    max_tokens: int = Field(default=2048, ge=1, le=65536)
    context_window: int = Field(default=32768, ge=1024)
    timeout: float = Field(default=30, gt=0, le=120)
    retries: int = Field(default=1, ge=0, le=3)
    structured_output: bool = False
    tool_calling: bool = False
    fallback_model: str = ""
    embedding_model: str = ""
    latency_preference: str = "balanced"
    cost_preference: str = "balanced"

    @model_validator(mode="after")
    def check_budget(self):
        if self.max_tokens >= self.context_window:
            raise ValueError("Output budget must be smaller than the context window")
        return self

    @classmethod
    def from_env(cls, **overrides):
        values = {}
        for key in cls.model_fields:
            if (value := os.getenv(f"LLM_{key.upper()}")) not in (None, ""):
                values[key] = value
        values.setdefault("api_key", os.getenv("OPENAI_API_KEY", ""))
        values.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**values)


@dataclass
class LLMResponse:
    content: str
    tool_calls: list = field(default_factory=list)
    raw_response: dict | None = None
    latency_ms: float = 0
    usage: dict = field(default_factory=dict)
    model: str = ""
    simulated: bool = False


class LLMClient:
    ENDPOINTS = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "ollama": "http://localhost:11434/v1",
    }

    def __init__(self, provider=None, model=None, base_url=None, *, config=None, transport=None):
        self.config = config or ModelConfig.from_env(
            provider=provider, model=model, base_url=base_url
        )
        self.provider = self.active_provider = self.config.provider
        self.model = self.config.model
        self.transport = transport
        if self.provider == "mock":
            self.model = "explicit-demo-fixture-v2"
            return
        if self.provider not in {*self.ENDPOINTS, "azure", "openai-compatible"}:
            raise ValueError("Unsupported LLM_PROVIDER; auto fallback has been removed")
        if not self.model:
            raise ValueError("Set LLM_MODEL to a model/deployment supported by your provider")
        self.base_url = (self.config.base_url or self.ENDPOINTS.get(self.provider, "")).rstrip("/")
        parsed = urlparse(self.base_url)
        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("LLM_BASE_URL must be a credential-free API base URL")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1", "ollama"}
        ):
            raise ValueError("Remote provider endpoints require HTTPS")
        if self.provider != "ollama" and not self.config.api_key:
            raise ValueError(
                "Set LLM_API_KEY externally; missing credentials cannot activate mock mode"
            )

    def chat(self, messages, tools=None, temperature=None, output_schema=None):
        if self.provider == "anthropic" and output_schema:
            raise ValueError(
                "Anthropic compatibility ignores response_format; use a native structured-output adapter for extraction"
            )
        if self.provider == "mock":
            if output_schema:
                raise LLMError("Demo fixtures cannot perform document extraction")
            from src.agent.simulation import simulate

            return simulate(messages)
        if tools and not self.config.tool_calling:
            raise ValueError("Enable LLM_TOOL_CALLING only after validating the selected model")
        if output_schema and not self.config.structured_output:
            raise ValueError("Enable LLM_STRUCTURED_OUTPUT only for a validated compatible model")
        if (
            len(json.dumps(messages).encode())
            > (self.config.context_window - self.config.max_tokens) * 3
        ):
            raise ValueError("Input exceeds conservative configured context budget; chunk it first")
        payload = {"model": self.model, "messages": messages}
        payload[
            "max_completion_tokens" if self.provider in {"openai", "azure"} else "max_tokens"
        ] = self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature
        if temp is not None:
            payload["temperature"] = temp
        if self.config.top_p is not None:
            payload["top_p"] = self.config.top_p
        if tools:
            payload["tools"] = tools
        if output_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "result", "strict": True, "schema": output_schema},
            }
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        if self.provider == "azure":
            headers = {"api-key": self.config.api_key}
        start = time.perf_counter()
        models = [self.model] + ([self.config.fallback_model] if self.config.fallback_model else [])
        with httpx.Client(
            timeout=self.config.timeout, transport=self.transport, follow_redirects=False
        ) as client:
            for model in models:
                payload["model"] = model
                for attempt in range(self.config.retries + 1):
                    try:
                        response = client.post(
                            f"{self.base_url}/chat/completions", json=payload, headers=headers
                        )
                    except (httpx.TimeoutException, httpx.NetworkError):
                        response = None
                    if response is not None and response.status_code not in {
                        429,
                        500,
                        502,
                        503,
                        504,
                    }:
                        if response.status_code != 200:
                            raise LLMError(f"Provider request failed (HTTP {response.status_code})")
                        try:
                            data = response.json()
                            choice = data["choices"][0]
                            message = choice["message"]
                            if choice.get("finish_reason") in {
                                "length",
                                "content_filter",
                            } or message.get("refusal"):
                                raise LLMError("Provider refused or returned an incomplete result")
                            content = message.get("content") or ""
                            if output_schema:
                                validate(json.loads(content), output_schema)
                            return LLMResponse(
                                content=content,
                                tool_calls=message.get("tool_calls") or [],
                                raw_response=data,
                                usage=data.get("usage", {}),
                                model=data.get("model", model),
                                latency_ms=(time.perf_counter() - start) * 1000,
                            )
                        except LLMError:
                            raise
                        except Exception:
                            raise LLMError(
                                "Provider returned an invalid response or output schema"
                            ) from None
                    if attempt < self.config.retries:
                        time.sleep(min(0.25 * 2**attempt, 2))
        raise LLMError("Provider unavailable after bounded retries; no simulated answer produced")

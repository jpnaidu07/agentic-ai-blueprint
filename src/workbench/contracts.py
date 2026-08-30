"""Bounded workbench requests and model output contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Connection(Contract):
    provider: Literal["openai", "gemini", "ollama"]
    model: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_./:-]+$")
    api_key: SecretStr = SecretStr("")
    max_tokens: int = Field(default=8192, ge=1024, le=32768)
    context_window: int = Field(default=65536, ge=8192, le=200000)
    consent: bool = False


class ModelList(Contract):
    provider: Literal["openai", "gemini", "ollama"]
    api_key: SecretStr = SecretStr("")


class Brief(Contract):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{2,63}$")
    problem: str = Field(min_length=30, max_length=16000)
    constraints: str = Field(default="", max_length=4000)


class Stage(Contract):
    stage: Literal["design", "decomposition", "remaining"]


class Approval(Contract):
    reviewer: str = Field(min_length=2, max_length=80)
    confirmed: bool = False
    spec_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class SpecEdit(Contract):
    section: Literal["capability", "design", "decomposition"]
    content: str = Field(min_length=1, max_length=200000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmed: bool = False


class RunRequest(Contract):
    selector: str = Field(default="next", max_length=80)
    module: int | None = Field(default=None, ge=1, le=8)
    include_dependencies: bool = False
    execute: bool = False
    confirmed: bool = False
    max_tasks: int = Field(default=12, ge=1, le=25)


class Action(Contract):
    action: Literal[
        "install-ollama",
        "start-ollama",
        "pull-model",
        "build-runner",
        "launch-tender",
        "launch-generated",
        "stop-app",
    ]
    model: Literal["qwen3:4b", "qwen3:8b"] = "qwen3:4b"
    solution: str = Field(default="government-tender-processing", pattern=r"^[a-z][a-z0-9-]{2,63}$")
    confirmed: bool = False


class Question(Contract):
    text: str = Field(min_length=3, max_length=6000)
    solution: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9-]{2,63}$")


class SourceFile(Contract):
    path: str = Field(min_length=1, max_length=180)
    content: str = Field(max_length=100000)


class Implementation(Contract):
    lesson: str = Field(min_length=10, max_length=6000)
    files: list[SourceFile] = Field(max_length=20)
    verification: str = Field(min_length=5, max_length=5000)
    manual_steps: list[str] = Field(max_length=20)
    summary: str = Field(min_length=5, max_length=5000)


class Advice(Contract):
    answer: str = Field(min_length=1, max_length=12000)
    next_steps: list[str] = Field(max_length=12)
    limitations: list[str] = Field(max_length=12)

"""Solution-owned local model configuration, evaluation and lifecycle operations."""

import json
import statistics
import time
import uuid
from typing import Literal

import httpx
from pydantic import Field

from src.blueprint import specs
from src.workbench.contracts import Contract
from src.workbench.security import WorkbenchError, local_path, no_secrets


class Example(Contract):
    prompt: str = Field(min_length=5, max_length=8000)
    answer: str = Field(min_length=1, max_length=2000)
    category: str = Field(default="domain", min_length=1, max_length=80)


class LocalProfile(Contract):
    training_model: Literal[
        "HuggingFaceTB/SmolLM2-135M-Instruct",
        "HuggingFaceTB/SmolLM2-360M-Instruct",
        "Qwen/Qwen3-0.6B",
    ] = "HuggingFaceTB/SmolLM2-135M-Instruct"
    training_steps: int = Field(default=10, ge=1, le=100)
    inference_model: str = Field(
        default="qwen3:4b", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,119}$"
    )
    embedding_model: str = Field(
        default="embeddinggemma", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,119}$"
    )
    context_window: int = Field(default=4096, ge=512, le=8192)
    max_tokens: int = Field(default=256, ge=32, le=512)
    minimum_accuracy: float = Field(default=0.8, gt=0, le=1)
    maximum_latency_seconds: float = Field(default=60, gt=0, le=120)
    training: list[Example] = Field(default_factory=list, max_length=500)
    evaluation: list[Example] = Field(min_length=3, max_length=30)


class LifecycleAction(Contract):
    confirmed: bool = False
    report_id: str = Field(default="", pattern=r"^[a-f0-9]{0,32}$")


def read_profile(root, name):
    path = local_path(specs.safe_solution(root, name), "models/profile.json")
    if not path.exists():
        raise WorkbenchError("Save the solution's local model profile and held-out examples first.")
    return LocalProfile.model_validate_json(path.read_text(encoding="utf-8"))


def save_profile(root, name, profile):
    path = specs.safe_solution(root, name)
    if not path.is_dir():
        raise WorkbenchError("Create/select a solution first.")
    train = {row.prompt.strip().casefold() for row in profile.training}
    held = [row.prompt.strip().casefold() for row in profile.evaluation]
    if train.intersection(held) or len(set(held)) != len(held):
        raise WorkbenchError(
            "Evaluation prompts must be unique and separate from training prompts."
        )
    if profile.max_tokens >= profile.context_window:
        raise WorkbenchError("Output tokens must be smaller than the context window.")
    content = profile.model_dump_json(indent=2)
    no_secrets(content)
    target = local_path(path, "models/profile.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    # Never leave a machine-readable selection behind after its inputs change.
    local_path(path, "models/selection.json").unlink(missing_ok=True)
    return {
        "message": "Saved application model profile. Existing evaluation/approval must match its new digest.",
        "digest": specs.digest(profile.model_dump()),
    }


class LocalModels:
    def __init__(self, root, state, runtime, jobs):
        self.root, self.state, self.runtime, self.jobs = root, state, runtime, jobs

    def directory(self, name):
        specs.safe_solution(self.root, name)
        path = local_path(self.state, f"local-models/{name}")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def status(self, name):
        directory = self.directory(name)
        profile_path = local_path(specs.safe_solution(self.root, name), "models/profile.json")
        return {
            "profile": read_profile(self.root, name).model_dump()
            if profile_path.exists()
            else None,
            "reports": [
                json.loads(p.read_text()) for p in sorted(directory.glob("evaluation-*.json"))
            ],
            "training": json.loads((directory / "training.json").read_text())
            if (directory / "training.json").exists()
            else None,
            "approval": self.approved(name, required=False),
        }

    def evaluate(self, name, job, trained=False):
        profile = read_profile(self.root, name)
        digest = specs.digest(profile.model_dump())
        model = "trained" if trained else profile.inference_model
        directory = self.directory(name)
        endpoint = (
            self.runtime.local_training_url(name) + "/v1/chat/completions"
            if trained
            else "http://127.0.0.1:11434/api/chat"
        )
        self.jobs.event(
            job,
            "Evaluation lesson: held-out prompts measure generalization. Exact-answer accuracy is reproducible but narrow; inspect failures and add domain coverage before trusting a score.",
        )
        rows = []
        with httpx.Client(timeout=120, trust_env=False) as client:
            for example in profile.evaluation:
                self.jobs.check_cancelled()
                messages = [
                    {
                        "role": "system",
                        "content": "Answer using only the supplied evidence. Return only the requested answer. If evidence is missing, answer UNKNOWN.",
                    },
                    {"role": "user", "content": example.prompt},
                ]
                payload = {"model": model, "messages": messages, "stream": False}
                if trained:
                    payload["max_tokens"] = profile.max_tokens
                else:
                    payload["options"] = {
                        "temperature": 0,
                        "num_ctx": profile.context_window,
                        "num_predict": profile.max_tokens,
                    }
                    payload["think"] = False
                start = time.monotonic()
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                answer = (
                    data["choices"][0]["message"]["content"]
                    if trained
                    else data["message"]["content"]
                )
                no_secrets(answer)
                rows.append(
                    {
                        "category": example.category,
                        "prompt": example.prompt,
                        "expected": example.answer,
                        "actual": answer,
                        "correct": " ".join(answer.casefold().split())
                        == " ".join(example.answer.casefold().split()),
                        "seconds": round(time.monotonic() - start, 3),
                    }
                )
            # A genuine embedding call verifies the configured model, never simulated vectors.
            embedded = client.post(
                "http://127.0.0.1:11434/api/embed",
                json={"model": profile.embedding_model, "input": [profile.evaluation[0].prompt]},
            )
            embedded.raise_for_status()
            vector = embedded.json()["embeddings"][0]
            if not vector or not all(isinstance(x, (float, int)) for x in vector):
                raise WorkbenchError("Embedding model returned invalid vectors.")
        report = {
            "id": uuid.uuid4().hex,
            "profile_digest": digest,
            "model": model,
            "embedding_model": profile.embedding_model,
            "embedding_dimensions": len(vector),
            "accuracy": sum(r["correct"] for r in rows) / len(rows),
            "mean_seconds": statistics.mean(r["seconds"] for r in rows),
            "maximum_seconds": max(r["seconds"] for r in rows),
            "rows": rows,
            "trained": trained,
            "scope": "Exact-answer held-out evaluation; no claim of broad domain readiness.",
        }
        report["passed"] = (
            report["accuracy"] >= profile.minimum_accuracy
            and report["maximum_seconds"] <= profile.maximum_latency_seconds
        )
        if not report["passed"]:
            report["message"] = (
                "Evaluation completed, but quality or latency thresholds were not met. Inspect the per-case results before changing the model or training data."
            )
        if trained:
            report["training_digest"] = specs.digest(
                json.loads((directory / "training.json").read_text())
            )
        (directory / f"evaluation-{report['id']}.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        return report

    def approve(self, name, report_id):
        directory = self.directory(name)
        file = local_path(directory, f"evaluation-{report_id}.json")
        if not file.is_file():
            raise WorkbenchError("Select an existing evaluation report before approval.")
        report = json.loads(file.read_text())
        if not report["passed"] or report["profile_digest"] != specs.digest(
            read_profile(self.root, name).model_dump()
        ):
            raise WorkbenchError(
                "Run a passing evaluation against the current model profile before approval."
            )
        (directory / "approved.json").write_text(json.dumps(report), encoding="utf-8")
        selection = {
            "model": report["model"],
            "embedding_model": report["embedding_model"],
            "provider": "openai-compatible" if report["trained"] else "ollama",
            "profile_digest": report["profile_digest"],
            "evaluation_id": report["id"],
            "training_digest": report.get("training_digest"),
            "connection": "Resolved by the local Workbench at application launch; helper keys are not used.",
        }
        local_path(specs.safe_solution(self.root, name), "models/selection.json").write_text(
            json.dumps(selection, indent=2), encoding="utf-8"
        )
        return {
            "message": "Approved the measured local model configuration for this solution.",
            "configuration": self.approved(name),
        }

    def approved(self, name, required=True):
        directory = self.directory(name)
        file = directory / "approved.json"
        if not file.exists():
            if required:
                raise WorkbenchError("Evaluate and approve the application local model first.")
            return None
        result = json.loads(file.read_text())
        profile = read_profile(self.root, name)
        valid = result["profile_digest"] == specs.digest(profile.model_dump())
        if result["trained"]:
            valid = valid and result.get("training_digest") == specs.digest(
                json.loads((directory / "training.json").read_text())
            )
        if not valid:
            if required:
                raise WorkbenchError(
                    "Model configuration or training changed. Re-evaluate and approve it."
                )
            return None
        base_url = "http://127.0.0.1:11434/v1"
        if result["trained"]:
            try:
                base_url = self.runtime.local_training_url(name) + "/v1"
            except WorkbenchError:
                if required:
                    raise
                base_url = None
        return {
            "provider": "openai-compatible" if result["trained"] else "ollama",
            "model": result["model"],
            "base_url": base_url,
            "embedding_model": profile.embedding_model,
            "embedding_base_url": "http://127.0.0.1:11434",
            "context_window": min(profile.context_window, 2048)
            if result["trained"]
            else profile.context_window,
            "max_tokens": profile.max_tokens,
            "evaluation_id": result["id"],
        }

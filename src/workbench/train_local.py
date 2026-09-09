"""CPU LoRA laboratory and local OpenAI-compatible serving for the trained artifact.

Run with the separate training environment. Never loads model-supplied Python code.
"""

import argparse
import json
import os
import time
from pathlib import Path

BASE = "HuggingFaceTB/SmolLM2-135M-Instruct"


def evaluate(model, tokenizer, examples):
    import torch

    model.eval()
    rows = []
    for example in examples:
        inputs = tokenizer.apply_chat_template(
            [{"role": "user", "content": example["prompt"]}],
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
        )
        if inputs.shape[1] > 256:
            raise ValueError("Shorten evaluation prompts to 256 tokens for the CPU lab.")
        start = time.monotonic()
        with torch.inference_mode():
            result = model.generate(
                inputs,
                attention_mask=torch.ones_like(inputs),
                max_new_tokens=32,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        answer = tokenizer.decode(result[0, inputs.shape[1] :], skip_special_tokens=True)
        rows.append(
            {
                "prompt": example["prompt"],
                "answer": answer,
                "expected": example["answer"],
                "correct": " ".join(answer.casefold().split())
                == " ".join(example["answer"].casefold().split()),
                "seconds": time.monotonic() - start,
            }
        )
    return {"accuracy": sum(row["correct"] for row in rows) / len(rows), "rows": rows}


def load(base, local=False):
    if not local:
        try:
            return load(base, local=True)
        except OSError:
            pass  # Download missing official model files; cached models work offline.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(min(4, os.cpu_count() or 1))
    tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=False, local_files_only=local)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base,
        trust_remote_code=False,
        local_files_only=local,
        dtype=torch.float32,
        use_safetensors=True,
    )
    return model, tokenizer


def train(profile_file, output, steps):
    import torch
    from peft import LoraConfig, get_peft_model

    profile = json.loads(profile_file.read_text(encoding="utf-8"))
    examples = profile["training"]
    if len(examples) < 3:
        raise ValueError("Provide at least three training examples, separate from evaluation.")
    held = {e["prompt"].strip().casefold() for e in profile["evaluation"]}
    if any(e["prompt"].strip().casefold() in held for e in examples):
        raise ValueError("Training/evaluation overlap is forbidden.")
    output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(42)
    base = profile.get("training_model", BASE)
    if base not in {BASE, "HuggingFaceTB/SmolLM2-360M-Instruct", "Qwen/Qwen3-0.6B"}:
        raise ValueError("Choose a maintained CPU training model.")
    model, tokenizer = load(base)
    base_revision = getattr(model.config, "_commit_hash", None)
    baseline = evaluate(model, tokenizer, profile["evaluation"])
    model = get_peft_model(
        model,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
            task_type="CAUSAL_LM",
        ),
    )
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=0.0002)
    model.train()
    start, losses = time.monotonic(), []
    for step in range(steps):
        row = examples[step % len(examples)]
        messages = [{"role": "user", "content": row["prompt"]}]
        prefix = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
        )
        full = tokenizer.apply_chat_template(
            messages + [{"role": "assistant", "content": row["answer"]}],
            tokenize=True,
            enable_thinking=False,
        )
        if len(full) > 256 or len(prefix) >= len(full):
            raise ValueError(
                "Training example exceeds 256 tokens or has no assistant target. Shorten it for this CPU lab."
            )
        inputs = torch.tensor([full])
        labels = inputs.clone()
        labels[:, : len(prefix)] = -100
        optimizer.zero_grad()
        loss = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), labels=labels).loss
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite training loss; checkpoint was not promoted.")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
        print(json.dumps({"step": step + 1, "loss": losses[-1]}), flush=True)
    model.save_pretrained(output / "adapter", safe_serialization=True)
    adapted = evaluate(model, tokenizer, profile["evaluation"])
    model.merge_and_unload().save_pretrained(output / "merged", safe_serialization=True)
    tokenizer.save_pretrained(output / "merged")
    report = {
        "base": base,
        "steps": steps,
        "losses": losses,
        "seconds": round(time.monotonic() - start, 2),
        "device": "cpu",
        "method": "LoRA r=8 q_proj/v_proj; assistant-token loss only",
        "seed": 42,
        "artifact": str(output / "merged"),
        "quality": "Not evaluated; compare on held-out examples before approval.",
    }
    report.update(
        {
            "base_revision": base_revision,
            "baseline": baseline,
            "adapted": adapted,
            "quality": "Measured exact-answer accuracy on the supplied held-out set; application evaluation and approval are still required.",
        }
    )
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def serve(artifact, port):
    import threading

    import torch
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request

    model, tokenizer = load(str(artifact), local=True)
    model.eval()
    lock = threading.Lock()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        from fastapi.responses import JSONResponse

        if request.headers.get("host") != f"127.0.0.1:{port}" or request.headers.get("origin"):
            return JSONResponse({"detail": "Server-to-server loopback requests only"}, 403)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"model": "trained", "artifact": artifact.name, "status": "ready"}

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 32000:
                raise HTTPException(413, "Request too large")
        try:
            body = json.loads(raw)
        except ValueError:
            raise HTTPException(422, "Provide JSON") from None
        if not isinstance(body, dict):
            raise HTTPException(422, "Provide a chat request object")
        if body.get("model") != "trained" or body.get("stream"):
            raise HTTPException(422, "Use model trained with streaming disabled")
        messages = body.get("messages", [])
        if (
            not isinstance(messages, list)
            or not messages
            or len(json.dumps(messages)) > 16000
            or any(
                not isinstance(m, dict)
                or m.get("role") not in {"system", "user", "assistant"}
                or not isinstance(m.get("content"), str)
                for m in messages
            )
        ):
            raise HTTPException(422, "Provide bounded chat messages")
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", enable_thinking=False
        )
        if inputs.shape[1] > 1536:
            raise HTTPException(422, "CPU lab input exceeds 1536 tokens")
        maximum = body.get("max_tokens", 128)
        if not isinstance(maximum, int) or not 1 <= maximum <= 512:
            raise HTTPException(422, "Maximum output must be 1..512 tokens")
        # Single process owns one model. Offload CPU work so health checks remain responsive.
        from starlette.concurrency import run_in_threadpool

        def generate():
            with lock, torch.inference_mode():
                result = model.generate(
                    inputs,
                    attention_mask=torch.ones_like(inputs),
                    max_new_tokens=maximum,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            reason = "stop" if result[0, -1].item() == tokenizer.eos_token_id else "length"
            return tokenizer.decode(result[0, inputs.shape[1] :], skip_special_tokens=True), reason

        answer, reason = await run_in_threadpool(generate)
        return {
            "model": "trained",
            "choices": [
                {"finish_reason": reason, "message": {"role": "assistant", "content": answer}}
            ],
        }

    uvicorn.run(app, host="127.0.0.1", port=port, access_log=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["train", "serve", "inspect"])
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    if args.action == "inspect":
        import torch

        start = time.monotonic()
        tensor = torch.ones((128, 128))
        measured = (tensor @ tensor)[0, 0].item()
        print(
            json.dumps(
                {
                    "torch": torch.__version__,
                    "cpu_tensor_check": measured == 128,
                    "seconds": time.monotonic() - start,
                    "cuda_available": torch.cuda.is_available(),
                    "xpu_available": hasattr(torch, "xpu") and torch.xpu.is_available(),
                    "mps_available": hasattr(torch.backends, "mps")
                    and torch.backends.mps.is_available(),
                    "recipe_device": "cpu",
                    "note": "A working tensor test verifies the backend; model-size fit still depends on live available RAM, sequence length and batch size.",
                }
            )
        )
        return
    if args.output is None or (args.action == "train" and args.profile is None):
        parser.error("Provide --output and, for training, --profile")
    if not 1 <= args.steps <= 100 or not 1024 <= args.port <= 65535:
        parser.error("Use 1..100 training steps and an unprivileged port")
    if args.action == "train":
        train(args.profile, args.output, args.steps)
    else:
        serve(args.output, args.port)


if __name__ == "__main__":
    main()

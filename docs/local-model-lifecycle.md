# Local model engineering: the foundational FDE exercise

The Workbench helper reads the blueprint and helps implement the solution. The
application runs a separately selected local inference model and embedding model.
You can complete model deployment, evaluation and fine-tuning without connecting a
cloud helper once a solution and its profile exist.

Open **Solutions → select a solution → Local model lifecycle**. The panel supports
individual steps and **Run all lifecycle steps**. Save the reviewed profile first.
All-mode stops on setup/training failures and leaves completed evidence available.
Model approval remains an explicit choice after comparing measured results.

## What each step teaches

| Step | Concept and reason | Evidence of completion | Next decision |
|---|---|---|---|
| Detect environment | Model weights, context/KV cache, activations and optimizer state compete with the OS for memory. Inference fit does not establish training fit. | RAM/free disk/tools and conservative CPU training profiles | Choose a fitting profile; verify runtime acceleration separately |
| Define the profile | Requirements become measurable quality/latency thresholds and representative examples | `models/profile.json` inside the solution | Review extraction, comparisons, missing evidence and adversarial cases |
| Deploy local models | Ollama downloads and serves quantized inference weights; an embedding encoder maps text to vectors | Successful model download and actual inference/embedding requests | Check output, latency and vector dimension |
| Baseline evaluation | A held-out set detects failures before adaptation | Per-case expected/actual answers, exact-answer accuracy and latency | Improve prompt/RAG or change model if necessary |
| Prepare training examples | Supervised fine-tuning learns desired responses from prompt/answer pairs | Separate training/evaluation prompts; no overlap accepted | Add reviewed examples covering observed failures |
| Fine-tune with LoRA | Low-rank adapters update a small set of trainable weights, reducing optimizer storage | Step losses, base revision, seed, adapter and merged weights | Compare held-out performance, not just training loss |
| Serve the checkpoint | Exported weights must reload and answer requests independently of training | Healthy loopback server and OpenAI-compatible response | Run application evaluation against the served artifact |
| Approve and integrate | Application configuration must refer to the model that was measured | Approval tied to profile and training report digests | Generate/build against the configuration; re-evaluate changes |

## On an ASUS/Intel workstation

The provided training recipe runs on CPU with float32 weights, batch size one,
256-token training examples, LoRA rank 8 and q_proj/v_proj adapters. This deliberately
small exercise is executable on a laptop and does not assume CUDA support from a GPU
name. Choose `training_model` and `training_steps` in the profile:

| Training model | Currently free RAM estimate | Purpose |
|---|---:|---|
| HuggingFaceTB/SmolLM2-135M-Instruct | 4 GiB | Fast first deployment/training/serving exercise |
| HuggingFaceTB/SmolLM2-360M-Instruct | 6 GiB | Larger CPU adaptation experiment |
| Qwen/Qwen3-0.6B | 10 GiB | More demanding CPU exercise; measure duration |

These are screening estimates, not memory guarantees. The worker uses at most four
CPU threads and the Workbench action has a 30-minute process timeout. Steps are
bounded to 1–100; default 10 is an engineering smoke exercise, not adequate training
for a procurement application. Downloads/checkpoints also require several GB of disk.
If a model exceeds memory, select a smaller profile. Larger QLoRA/CUDA, Intel XPU or
Apple MLX training needs a separately tested recipe and compatible framework build;
the UI does not claim those accelerators were tested.

The training environment is installed at `.workbench/training-venv` using
`requirements-training.txt`, separate from the Workbench environment. Original model
weights use the Hugging Face cache. Solution checkpoints and evaluation outputs live
under `.workbench/local-models/<solution>/`. They are excluded from Git. The profile
contains the reviewed examples; use synthetic examples when sharing it.

## First exercise

1. Start Ollama from Setup (install it there if absent).
2. Select a solution and open Local model lifecycle.
3. Load the synthetic training exercise or adapt
   [the profile template](../templates/local-model-profile.json). Save the profile.
4. Download application models and evaluate the local baseline.
5. Install the training environment, then train LoRA locally.
6. Inspect the training report's baseline and adapted held-out answers. Loss going
   down does not prove improved generalization. The trainer masks prompt tokens so
   its learning objective is the assistant response.
7. Serve the trained model and evaluate it using the same application evaluation set.
8. Approve a passing report. If none passes, inspect failures and improve the model,
   data or prompt. Lowering a threshold merely to pass is not evidence of improvement.
9. Build/launch the application. The tender reference receives only the approved local
   connection; the helper's provider key is never reused. Existing applications must
   be relaunched after changing the selected local model.

For a terminal-only first training check (PowerShell, from the repository root):

```powershell
python -m venv .workbench/training-venv
.workbench/training-venv/Scripts/python -m pip install -r requirements-training.txt
.workbench/training-venv/Scripts/python src/workbench/train_local.py train --profile templates/local-model-profile.json --output .workbench/my-first-training --steps 3
.workbench/training-venv/Scripts/python src/workbench/train_local.py serve --output .workbench/my-first-training/merged --port 8084
```

Choose a new output directory for each run. On Linux/macOS use `bin/python` instead
of `Scripts/python`. A training worker failure leaves partial artifacts for inspection,
but the Workbench promotes a checkpoint only after a successful worker report.

## RAG, fine-tuning and pretraining

RAG retrieves current evidence at request time; use it for tender document facts,
citations and changing procurement rules. Fine-tuning changes response behavior:
for example, concise extraction, schema adherence or appropriate abstention.
Pretraining a model from scratch learns general language and requires a different
data/compute scale. LoRA is real fine-tuning of pretrained weights; it is the first
practical FDE adaptation exercise here.

An embedding smoke call establishes execution and dimensions, not retrieval quality.
Evaluate retrieval recall, ranking, citations and groundedness in the production-RAG
exercise before using document Q&A. Exact-answer evaluation here is useful for small
extraction tasks, but must be supplemented with the application's structured-output,
evidence and authorization tests. Never treat three synthetic examples as a domain
certification.

Advanced experiments: vary LoRA rank and learning rate; compare a prompt-only baseline
with adapter output; split related documents by tender rather than random chunks to
avoid leakage; track abstention separately from extraction; test for catastrophic
forgetting on unrelated tasks; measure long-context memory and response latency.
Keep a stable held-out test set and a separate development set for iterative tuning.

## Application connection

Generation receives the approved local configuration. Generated application code
reads `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` and `LLM_EMBEDDING_MODEL`. Its offline
tests mock the HTTP boundary. The isolated preview uses a trusted relay and an
authenticated gateway to only the selected local chat/embedding endpoints. Rebuild
the isolated runner after this update because its relay source changed. The gateway
binds a host port for Docker connectivity and requires a random per-preview token;
it does not expose arbitrary model management or arbitrary URLs. Stop the preview to
stop its gateway. Document traffic stays local.

The trained CPU server does not implement constrained JSON decoding. Schema-dependent
tasks must validate its output; a schema failure remains an error. Tensor acceleration,
large training recipes and Docker gateway networking are separate runtime checks.

References: [SmolLM2 model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct),
[Qwen3 model card](https://huggingface.co/Qwen/Qwen3-0.6B),
[PEFT](https://huggingface.co/docs/peft/index),
[Ollama embeddings](https://docs.ollama.com/api/embed).

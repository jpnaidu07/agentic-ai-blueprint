#!/usr/bin/env bash
set -e

echo "========================================================"
echo "🧠 Enterprise Agentic AI Platform Setup (Linux/macOS)"
echo "========================================================"

# 1. Install dependencies
echo "[1/3] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# 2. Check Ollama
echo "[2/3] Checking Ollama status..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama running. Pulling qwen2.5-coder:7b..."
    ollama pull qwen2.5-coder:7b || true
else
    echo "Ollama not running. Fallback mock engine will be used."
fi

# 3. Run verification
echo "[3/3] Running tests and eval harness..."
python3 -m pytest src/tests/ -v
python3 -m src.evals.eval_harness

echo "========================================================"
echo "🎉 Setup Complete! Run 'python3 -m src.api.server' and open http://localhost:8000"
echo "========================================================"

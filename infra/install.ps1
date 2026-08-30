# One-Click Setup Script for Windows (Intel Core Ultra 9 / Arc GPU)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "🧠 Enterprise Agentic AI Platform Setup (Windows)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/4] Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# 2. Install Dependencies
Write-Host "[2/4] Installing Python dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Pull Ollama Model (Optional)
Write-Host "[3/4] Checking Ollama service..." -ForegroundColor Yellow
try {
    $ollamaTest = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
    Write-Host "Ollama detected! Pulling Qwen 2.5 Coder model..." -ForegroundColor Green
    ollama pull qwen2.5-coder:7b
} catch {
    Write-Host "Ollama not running locally. System will use high-speed deterministic mock engine automatically." -ForegroundColor Gray
}

# 4. Run Verification Tests
Write-Host "[4/4] Running test suite & evaluation benchmark..." -ForegroundColor Yellow
python -m pytest src/tests/ -v
python -m src.evals.eval_harness

Write-Host "========================================================" -ForegroundColor Green
Write-Host "🎉 Platform Ready! Launch the dashboard with:" -ForegroundColor Green
Write-Host "   python -m src.api.server" -ForegroundColor White
Write-Host "   Then open http://localhost:8000" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green

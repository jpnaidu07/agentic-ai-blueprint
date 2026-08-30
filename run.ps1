param([switch]$LocalPython)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.env')) { throw 'Run setup.ps1 first.' }
if ($LocalPython) {
    & '.venv/Scripts/python.exe' -m src.api.server
} else {
    & docker compose up --build --wait
}
if ($LASTEXITCODE -ne 0) { throw "Startup failed with exit code $LASTEXITCODE" }

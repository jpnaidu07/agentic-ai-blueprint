param([switch]$LocalPython)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows, then reopen the terminal.' }
if ($LocalPython) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Install Python 3.11+ and add it to PATH.' }
    Invoke-Checked 'python' @('-c', 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"')
    if (-not (Test-Path '.venv/Scripts/python.exe')) { Invoke-Checked 'python' @('-m','venv','.venv') }
    Invoke-Checked '.venv/Scripts/python.exe' @('-m','pip','install','-r','requirements-dev.txt','-e','.')
    Invoke-Checked '.venv/Scripts/python.exe' @('scripts/init_env.py')
    Invoke-Checked '.venv/Scripts/python.exe' @('-m','pytest','-q')
    Write-Host 'Run: ./run.ps1 -LocalPython'
} else {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install Docker Desktop with WSL2, start it, and reopen the terminal. See docs/setup.md.' }
    Invoke-Checked 'docker' @('info','--format','{{.ServerVersion}}')
    Invoke-Checked 'docker' @('compose','version')
    Invoke-Checked 'docker' @('run','--rm','--mount',"type=bind,source=$PSScriptRoot,target=/workspace",'-w','/workspace','python:3.12-slim','python','scripts/init_env.py')
    Invoke-Checked 'docker' @('compose','config','--quiet')
    Invoke-Checked 'docker' @('compose','build')
    Write-Host 'Run: ./run.ps1. Cloud inference is optional until extraction is enabled.'
}

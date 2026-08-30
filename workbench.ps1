param([int]$Port = 8080)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Use a port from 1024 to 65535.' }
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Install Python 3.11+ from python.org, then reopen the terminal.' }
    Invoke-Checked 'python' @('-c', 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"')
    Invoke-Checked 'python' @('-m','venv','.venv')
}
Invoke-Checked '.venv/Scripts/python.exe' @('-m','pip','install','-r','requirements.txt','-e','.')
Write-Host 'Starting the local workbench. Open the printed URL and paste its pairing token. Ctrl+C stops it.'
Invoke-Checked '.venv/Scripts/python.exe' @('-m','src.workbench.server','--port',"$Port")

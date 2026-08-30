param([switch]$LocalPython)
& (Join-Path $PSScriptRoot '../setup.ps1') -LocalPython:$LocalPython

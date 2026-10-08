$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Run scripts/setup.ps1 first."
}

$env:PYTHONPATH = $backendDir
Push-Location $backendDir
try {
    & $python -m app.seed
}
finally {
    Pop-Location
}

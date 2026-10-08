$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Run scripts/setup.ps1 first."
}

$env:PYTHONPATH = Join-Path $projectRoot "backend"
& $python -m pytest (Join-Path $projectRoot "backend\tests") --basetemp (Join-Path $projectRoot ".tmp\pytest")

Push-Location (Join-Path $projectRoot "frontend")
try {
    npm test
    npm run build
    npm run test:e2e
}
finally {
    Pop-Location
}

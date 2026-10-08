$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    python -m venv (Join-Path $projectRoot ".venv")
}

& $venvPython -m pip install -r (Join-Path $projectRoot "backend\requirements-dev.txt")
Push-Location (Join-Path $projectRoot "frontend")
try {
    npm install
    npx playwright install chromium
}
finally {
    Pop-Location
}

Write-Host "Setup complete. Copy backend/.env.example to backend/.env, then run the two start scripts."

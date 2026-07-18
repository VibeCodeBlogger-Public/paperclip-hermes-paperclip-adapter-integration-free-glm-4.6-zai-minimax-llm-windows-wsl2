# ============================================================
#  Location of this file:
#    Any folder on Windows — run it as your user.
#    e.g. C:\Users\<YOUR_USER>\Downloads\install_hermes_wsl.ps1
#
#  How to run:
#    Right-click -> "Run with PowerShell"
#    or in PowerShell: .\install_hermes_wsl.ps1
#
#  What this script does:
#    1. Installs hermes-agent in WSL Ubuntu via pip
#    2. Writes config.yaml (model zai/glm-4.6)
#    3. Writes .env with your API key
#    4. Creates hermes.bat in C:\Users\<USER>\bin\ for the Windows PATH
#    5. Verifies the install
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hermes Agent x ZAI x Paperclip Setup " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Ask for the API key ─────────────────────────────────────
Write-Host "Get an API key: https://z.ai/manage-apikey/apikey-list" -ForegroundColor Yellow
Write-Host ""
$ZAI_API_KEY = Read-Host "Enter your ZAI_API_KEY"

if ([string]::IsNullOrWhiteSpace($ZAI_API_KEY)) {
    Write-Host "[ERROR] The API key cannot be empty." -ForegroundColor Red
    exit 1
}

# ── STEP 1: Install hermes-agent in WSL ────────────────────
Write-Host ""
Write-Host "[1/4] Installing hermes-agent in WSL Ubuntu..." -ForegroundColor Yellow

wsl -d Ubuntu -- bash -c "pip install --upgrade hermes-agent 2>&1 | tail -3"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] hermes-agent installation failed." -ForegroundColor Red
    Write-Host "Make sure WSL Ubuntu is installed: wsl --install -d Ubuntu" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] hermes-agent installed." -ForegroundColor Green

# ── STEP 2: Write config.yaml and .env into WSL ────────────
Write-Host ""
Write-Host "[2/4] Writing configuration into WSL..." -ForegroundColor Yellow

$configYaml = @"
# Hermes Agent - ZAI (z.ai / GLM-4.6) config
# Location: ~/.hermes/config.yaml (inside WSL Ubuntu)
model: zai/glm-4.6
provider: zai
base_url: https://api.z.ai/api/paas/v4

compression:
  enabled: true
  threshold: 0.50
  summary_model: ""
  summary_provider: auto
"@

$envContent = @"
ZAI_API_KEY=$ZAI_API_KEY
GLM_API_KEY=$ZAI_API_KEY
"@

$tempConfig = "$env:TEMP\hermes_config.yaml"
$tempEnv    = "$env:TEMP\hermes_env"

$configYaml | Out-File -FilePath $tempConfig -Encoding utf8 -NoNewline
$envContent | Out-File -FilePath $tempEnv    -Encoding utf8 -NoNewline

$wslTempConfig = (wsl -d Ubuntu -- wslpath -u ($tempConfig -replace '\\','/')).Trim()
$wslTempEnv    = (wsl -d Ubuntu -- wslpath -u ($tempEnv    -replace '\\','/')).Trim()

wsl -d Ubuntu -- bash -c "mkdir -p ~/.hermes && cp '$wslTempConfig' ~/.hermes/config.yaml && cp '$wslTempEnv' ~/.hermes/.env"
Remove-Item $tempConfig, $tempEnv -ErrorAction SilentlyContinue

Write-Host "[OK] config.yaml and .env written into WSL (~/.hermes/)." -ForegroundColor Green

# ── STEP 3: Create hermes.bat on the Windows PATH ──────────
Write-Host ""
Write-Host "[3/4] Creating hermes.bat for the Windows PATH..." -ForegroundColor Yellow

$binDir = "$env:USERPROFILE\bin"
if (!(Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir | Out-Null
    Write-Host "[OK] Created folder: $binDir" -ForegroundColor Green
}

$batContent = @"
@echo off
rem Forwards hermes from Windows into WSL Ubuntu
wsl bash -lc "hermes %*"
"@
$batContent | Out-File -FilePath "$binDir\hermes.bat" -Encoding ascii -NoNewline

# Add to PATH if missing
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$binDir", "User")
    Write-Host "[OK] $binDir added to the Windows PATH." -ForegroundColor Green
    Write-Host "     IMPORTANT: restart your terminal/Paperclip so PATH refreshes." -ForegroundColor Yellow
} else {
    Write-Host "[OK] $binDir is already on the Windows PATH." -ForegroundColor Green
}

# ── STEP 4: Verify ─────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Verifying the install..." -ForegroundColor Yellow

$version = wsl -d Ubuntu -- bash -lc "hermes --version 2>&1 | head -1"
if ($version -match "Hermes") {
    Write-Host "[OK] $version" -ForegroundColor Green
} else {
    Write-Host "[WARN] hermes --version did not return a version. You may need to restart WSL:" -ForegroundColor Yellow
    Write-Host "       wsl --shutdown  (then open it again)" -ForegroundColor Yellow
}

# ── Done ───────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DONE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  1. Start Paperclip:" -ForegroundColor White
Write-Host "     npx paperclipai@latest start" -ForegroundColor Yellow
Write-Host "  2. Open your browser: http://127.0.0.1:3100" -ForegroundColor White
Write-Host "  3. Create an agent with the 'Hermes Agent (Local)' adapter" -ForegroundColor White
Write-Host "     Agents: http://127.0.0.1:3100/MYA/agents/" -ForegroundColor Yellow
Write-Host "  4. In the agent settings set the model: zai/glm-4.6" -ForegroundColor White
Write-Host ""

# OpenClaw — Start local inference servers
Write-Host "Starting OpenClaw local servers..." -ForegroundColor Cyan

$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaExe) {
    $running = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if (-not $running) {
        Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep 2
        Write-Host "  Ollama: STARTED (localhost:11434)" -ForegroundColor Green
    } else {
        Write-Host "  Ollama: already running" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Ollama: not found" -ForegroundColor Red
}

$lmsPaths = @(
    "$env:LOCALAPPDATA\Programs\LM-Studio\LM Studio.exe",
    "$env:LOCALAPPDATA\Programs\LM Studio\LM Studio.exe",
    "C:\Program Files\LM Studio\LM Studio.exe",
    "$env:APPDATA\LM Studio\LM Studio.exe"
)
$lmsExe = $lmsPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($lmsExe) {
    $running = Get-Process -Name "*LM*Studio*" -ErrorAction SilentlyContinue
    if (-not $running) {
        Start-Process -FilePath $lmsExe
        Start-Sleep 3
        Write-Host "  LM Studio: STARTED -- load Devstral then click Start Server" -ForegroundColor Green
    } else {
        Write-Host "  LM Studio: already running" -ForegroundColor Yellow
    }
} else {
    Write-Host "  LM Studio: not installed -- code prompts will fall back to Claude Haiku" -ForegroundColor Yellow
}

Write-Host "`nAll servers started. OpenClaw is ready." -ForegroundColor Cyan

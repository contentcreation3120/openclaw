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

$lmsExe = "$env:LOCALAPPDATA\Programs\LM-Studio\LM Studio.exe"
if (Test-Path $lmsExe) {
    $running = Get-Process -Name "*LM Studio*" -ErrorAction SilentlyContinue
    if (-not $running) {
        Start-Process -FilePath $lmsExe
        Start-Sleep 3
        Write-Host "  LM Studio: STARTED (localhost:1234) -- load Devstral then Start Server" -ForegroundColor Green
    } else {
        Write-Host "  LM Studio: already running" -ForegroundColor Yellow
    }
} else {
    Write-Host "  LM Studio: not found" -ForegroundColor Red
}

Write-Host "`nAll servers started. OpenClaw is ready." -ForegroundColor Cyan

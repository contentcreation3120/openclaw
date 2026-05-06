# OpenClaw — Stop local inference servers
Write-Host "Stopping OpenClaw local servers..." -ForegroundColor Yellow
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Write-Host "  Ollama: stopped" -ForegroundColor Green
Stop-Process -Name "*LM Studio*" -Force -ErrorAction SilentlyContinue
Write-Host "  LM Studio: stopped" -ForegroundColor Green
Write-Host "All servers stopped." -ForegroundColor Yellow

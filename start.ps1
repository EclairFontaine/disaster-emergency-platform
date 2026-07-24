Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Disaster Emergency Platform Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Docker
Write-Host "[1/4] Starting Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
do { Start-Sleep 2 } until (& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" info 2>$null)
Write-Host "      Docker ready" -ForegroundColor Green

# 2. PostgreSQL
Write-Host "[2/4] Starting PostgreSQL..." -ForegroundColor Yellow
& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" start disaster-pg 2>$null
do { Start-Sleep 1 } until (& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" exec disaster-pg pg_isready -U postgres 2>$null)
Write-Host "      PostgreSQL ready" -ForegroundColor Green

# 3. Backend
Write-Host "[3/4] Starting Backend (port 8000)..." -ForegroundColor Yellow
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process python -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "$PSScriptRoot\backend"
Start-Sleep 8
Write-Host "      Backend ready" -ForegroundColor Green

# 4. Frontend
Write-Host "[4/4] Starting Frontend (port 3000)..." -ForegroundColor Yellow
Get-Process -Name "node*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process npx -ArgumentList "vite","--host","127.0.0.1","--port","3000" -WorkingDirectory "$PSScriptRoot\frontend"
Start-Sleep 4

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services running!" -ForegroundColor Green
Write-Host "  Frontend: http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  Backend:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Login:    admin / admin123" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

Start-Process "http://127.0.0.1:3000"
Read-Host "Press Enter to exit"

@echo off
chcp 65001 >nul
echo ========================================
echo   应急平台一键启动
echo ========================================
echo.

echo [1/4] 启动 Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo 等待 Docker 就绪...
:wait_docker
timeout /t 3 >nul
"C:\Program Files\Docker\Docker\resources\bin\docker.exe" info >nul 2>&1
if errorlevel 1 goto wait_docker
echo Docker 已就绪

echo [2/4] 启动 PostgreSQL...
"C:\Program Files\Docker\Docker\resources\bin\docker.exe" start disaster-pg >nul 2>&1
:wait_pg
"C:\Program Files\Docker\Docker\resources\bin\docker.exe" exec disaster-pg pg_isready -U postgres >nul 2>&1
if errorlevel 1 (timeout /t 2 >nul & goto wait_pg)
echo PostgreSQL 已就绪

echo [3/4] 启动后端 (port 8000)...
start "Backend" cmd /c "cd /d D:\第10天\disaster-emergency-platform\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 6 >nul
echo 后端已启动

echo [4/4] 启动前端 (port 3000)...
start "Frontend" cmd /c "cd /d D:\第10天\disaster-emergency-platform\frontend && npx vite --host 127.0.0.1 --port 3000"
timeout /t 4 >nul

echo.
echo ========================================
echo   全部启动完成！
echo   前端: http://127.0.0.1:3000
echo   后端: http://127.0.0.1:8000/docs
echo   账号: admin / admin123
echo ========================================
echo.
start http://127.0.0.1:3000
pause

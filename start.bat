@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "backend\cameras.json" (
  echo {"monitors": {"mon1": "monitor 1"}, "cameras": []}>backend\cameras.json
  echo Created empty backend\cameras.json
)
REM Clear stale containers (e.g. from another folder running the same stack)
docker rm -f ivs-mediamtx ivs-backend ivs-sim >nul 2>&1
echo Starting IAS-Viewer-Server...
echo (first run downloads images - please wait a few minutes)
docker compose up -d
if errorlevel 1 (
  echo.
  echo Failed to start. See the error above.
  pause
  exit /b 1
)
echo Waiting for services to start...
timeout /t 20 /nobreak >nul
start http://localhost:8000/?monitor=mon1
echo.
echo Done! Dashboard: http://localhost:8000/?monitor=mon1
pause

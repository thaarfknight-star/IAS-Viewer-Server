@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "backend\cameras.json" (
  echo {"monitors": {"mon1": "monitor 1"}, "cameras": []}>backend\cameras.json
  echo Created empty backend\cameras.json
)
echo Starting IAS-Viewer-Server...
echo (first run downloads images - please wait a few minutes)
docker compose up -d
if errorlevel 1 (
  echo.
  echo Docker is not running. Please start Docker Desktop and try again.
  pause
  exit /b 1
)
echo Waiting for services to start...
timeout /t 20 /nobreak >nul
start http://localhost:8000/?monitor=mon1
echo.
echo Done! Dashboard: http://localhost:8000/?monitor=mon1
pause

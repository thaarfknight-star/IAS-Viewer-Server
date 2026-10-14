@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "backend\cameras.json" copy /y "backend\cameras.json" "backend\cameras.json.bak" >nul
echo {"monitors": {"mon1": "monitor 1"}, "cameras": [{"id": "cam1", "name": "Test camera", "rtsp": "", "monitor": "mon1"}]}>backend\cameras.json
echo (test camera config written - previous cameras.json backed up to .bak)
REM Clear stale containers (e.g. from another folder running the same stack)
docker rm -f ivs-mediamtx ivs-backend ivs-sim >nul 2>&1
echo Starting IAS-Viewer-Server with SIMULATED camera...
echo (first run downloads images - please wait a few minutes)
docker compose --profile sim up -d
if errorlevel 1 (
  echo.
  echo Failed to start. See the error above.
  pause
  exit /b 1
)
echo Waiting for services to start...
timeout /t 25 /nobreak >nul
start http://localhost:8000/?monitor=mon1
echo.
echo Done! Dashboard: http://localhost:8000/?monitor=mon1
echo Recordings page: http://localhost:8000/recordings.html
pause

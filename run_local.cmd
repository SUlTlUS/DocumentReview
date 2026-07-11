@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Backend virtual environment is missing.
  echo Install backend\requirements.txt first.
  pause
  exit /b 1
)

"backend\.venv\Scripts\python.exe" "scripts\start_local.py"
if errorlevel 1 (
  echo.
  echo [ERROR] Startup failed. Check output\*-live.*.log.
  pause
  exit /b 1
)

endlocal

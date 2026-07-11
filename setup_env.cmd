@echo off
setlocal
cd /d "%~dp0"

where py.exe >nul 2>nul
if not errorlevel 1 (
  py.exe -3 "scripts\setup_environment.py" %*
) else (
  where python.exe >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python 3 was not found. Install Python 3.11 or newer and enable Add Python to PATH.
    pause
    exit /b 1
  )
  python.exe "scripts\setup_environment.py" %*
)

if errorlevel 1 (
  echo.
  echo [ERROR] Environment installation failed. Review the error above.
  pause
  exit /b 1
)

echo.
echo Environment is ready. Double-click run_local.cmd to start the application.
pause
endlocal

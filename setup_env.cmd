@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap_environment.ps1" %*
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

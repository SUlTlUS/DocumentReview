@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Backend virtual environment is missing.
  echo Install backend\requirements.txt first.
  pause
  exit /b 1
)

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm.cmd was not found. Install Node.js and add npm to PATH.
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [ERROR] Frontend dependencies are missing.
  echo Run: cd frontend ^&^& npm install
  pause
  exit /b 1
)

if not exist "output" mkdir "output"

echo [1/3] Checking backend...
powershell.exe -NoLogo -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue ^| Where-Object LocalAddress -in '127.0.0.1','0.0.0.0')) { Start-Process -FilePath '%~dp0backend\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory '%~dp0backend' -WindowStyle Hidden -RedirectStandardOutput '%~dp0output\backend-live.stdout.log' -RedirectStandardError '%~dp0output\backend-live.stderr.log' }"
if errorlevel 1 goto :failed

echo [2/3] Checking frontend...
powershell.exe -NoLogo -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue ^| Where-Object LocalAddress -in '127.0.0.1','0.0.0.0')) { Start-Process -FilePath (Get-Command npm.cmd).Source -ArgumentList 'run','dev','--','--host','127.0.0.1','--port','5173' -WorkingDirectory '%~dp0frontend' -WindowStyle Hidden -RedirectStandardOutput '%~dp0output\frontend-live.stdout.log' -RedirectStandardError '%~dp0output\frontend-live.stderr.log' }"
if errorlevel 1 goto :failed

echo [3/3] Waiting for services...
powershell.exe -NoLogo -NoProfile -Command "$deadline=(Get-Date).AddSeconds(45); do { try { $api=(Invoke-WebRequest 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 2).StatusCode } catch {}; try { $web=(Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2).StatusCode } catch {}; if ($api -eq 200 -and $web -eq 200) { exit 0 }; Start-Sleep -Milliseconds 400 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 goto :failed

echo Ready: http://127.0.0.1:5173
start "" "http://127.0.0.1:5173"
timeout /t 3 /nobreak >nul
exit /b 0

:failed
echo.
echo [ERROR] Startup failed. Check output\*-live.*.log.
pause
exit /b 1

endlocal

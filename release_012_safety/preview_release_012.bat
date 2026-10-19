@echo off
setlocal
cd /d "%~dp0"
set "TENDERPROOF_RUNTIME_ROOT=%~dp0preview"
set "TENDERPROOF_DB_PATH=%~dp0preview\storage\tenderproof.db"
set "PYTHON=%~dp0..\tenderproof_os\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo ERROR: The verified local Python environment was not found.
  pause
  exit /b 1
)
echo Starting the isolated Release 012 review preview...
cd tenderproof_os
"%PYTHON%" run_app.py --run --port 8512
if errorlevel 1 pause
endlocal

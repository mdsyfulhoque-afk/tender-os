@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================
echo TenderProof OS / ProposalGuard local launcher
echo ================================================
echo.

echo Checking Python...
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found. Install Python 3.11 or newer, then run this file again.
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo ERROR: Python 3.11 or newer is required.
  pause
  exit /b 1
)

echo Creating virtual environment...
if not exist ".venv\Scripts\activate.bat" (
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create .venv.
    pause
    exit /b 1
  )
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Could not activate .venv.
  pause
  exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: pip upgrade failed.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: dependency installation failed.
  pause
  exit /b 1
)

echo Creating required folders...
if not exist data mkdir data
if not exist storage mkdir storage
if not exist storage\uploads mkdir storage\uploads
if not exist storage\extracted_text mkdir storage\extracted_text
if not exist storage\reports mkdir storage\reports
if not exist storage\exports mkdir storage\exports
if not exist storage\backups mkdir storage\backups

echo Initializing database...
python run_app.py --init-db
if errorlevel 1 (
  echo ERROR: database initialization failed.
  pause
  exit /b 1
)

echo Running tests...
python -m pytest -q
if errorlevel 1 (
  echo ERROR: tests failed. Fix the failing tests before using client-ready outputs.
  pause
  exit /b 1
)

echo Starting TenderProof OS...
echo App URL: http://localhost:8501
python run_app.py --run
if errorlevel 1 (
  echo ERROR: Streamlit exited with an error.
  pause
  exit /b 1
)

endlocal


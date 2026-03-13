@echo off
echo ============================================================
echo  PredictPath AI - Tool 1 Setup Script
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment and installing dependencies...
call .\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo [3/4] Creating required data directories...
mkdir data\output 2>nul
mkdir data\dlq 2>nul
mkdir data\models 2>nul
mkdir data\uploads 2>nul
mkdir data\samples 2>nul
echo      Directories created.

echo [4/4] Verifying install...
python -c "import polars, pydantic, pyarrow, typer; print('All core packages OK')"
if errorlevel 1 (
    echo [ERROR] Package verification failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup complete! You can now run Tool 1:
echo.
echo    .venv\Scripts\python.exe -m src.main ingest ^<path-to-log^>
echo.
echo  Example:
echo    .venv\Scripts\python.exe -m src.main ingest "..\scripts\saved-logs\wazuh_report_20260311_131245.json" --type universal
echo ============================================================
pause

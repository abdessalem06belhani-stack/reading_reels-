@echo off
REM ============================================================
REM  reading_reels - one-time setup for Windows 10
REM  Double-click this file. It creates a virtual environment
REM  and installs everything needed.
REM ============================================================
cd /d "%~dp0"
echo.
echo === [1/4] Creating virtual environment (.venv) ===
py -3 -m venv .venv 2>nul || python -m venv .venv

echo.
echo === [2/4] Activating environment ===
call ".venv\Scripts\activate.bat"

echo.
echo === [3/4] Upgrading pip ===
python -m pip install --upgrade pip

echo.
echo === [4/4] Installing dependencies (this can take a few minutes) ===
pip install -r requirements.txt

echo.
echo === Done! Running an environment check ===
python -m app.main doctor

echo.
echo ============================================================
echo  Setup complete.
echo  Next: double-click  run.bat  to make videos.
echo  To enable AI scripts / real backgrounds / auto-upload,
echo  copy  .env.example  to  .env  and read  docs\API_KEYS.md
echo ============================================================
pause

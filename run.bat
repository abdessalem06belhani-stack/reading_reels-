@echo off
REM ============================================================
REM  reading_reels  -  Telegram bot launcher
REM ============================================================
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Virtual environment not found. Please run setup.bat first.
  pause
  exit /b
)
call ".venv\Scripts\activate.bat"
python -m telegram_bot.bot
pause

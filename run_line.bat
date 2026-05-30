@echo off
cd /d "%~dp0"
echo Using: "%~dp0.venv\Scripts\python.exe"
".venv\Scripts\python.exe" -u send_line_message.py
echo.
echo --- exit code %ERRORLEVEL% ---
pause

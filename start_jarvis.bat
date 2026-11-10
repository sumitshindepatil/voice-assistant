@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python and tick "Add to PATH".
    pause
    exit /b 1
)

:loop
python voice_assistant.py
if errorlevel 1 (
    echo Assistant stopped unexpectedly. Restarting in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto loop
)

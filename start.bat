@echo off
REM Claude Desktop Bridge - Tek komutla başlat

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python bridge.py
pause

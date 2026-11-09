@echo off
REM Launch KESHAV AI natively as a Windows desktop application
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Launching KESHAV AI Native Windows Desktop Application...
python main.py
pause

@echo off
REM Package KESHAV AI as a standalone Windows Desktop Application (.exe)
cd /d "%~dp0\.."

echo ==============================================
echo Building KESHAV AI for Windows Desktop
echo ==============================================

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

flet build windows ^
    --project keshav_ai ^
    --product "KESHAV AI" ^
    --org "org.keshav.ai" ^
    --build-version "1.0.0" ^
    --build-number 1 ^
    -o dist\windows

echo Windows Desktop App built in dist\windows\!
pause

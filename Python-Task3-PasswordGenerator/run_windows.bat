@echo off
setlocal
cd /d "%~dp0"
echo NOMOLI FORGE - Password Forge
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py
) else (
  py -3 main.py
)
if errorlevel 1 pause

@echo off
cd /d "%~dp0"

echo Starting Wind Automation Pipeline...
echo.

if not exist "runtime\python\python.exe" (
    echo [ERROR] Local Python runtime not found.
    echo Please run install_portable_local_python.bat first.
    echo.
    pause
    exit /b 1
)

runtime\python\python.exe bin\runner.py

echo.
if %ERRORLEVEL% == 0 (
    echo Pipeline completed successfully.
) else (
    echo Pipeline FAILED. See errors above.
)

pause
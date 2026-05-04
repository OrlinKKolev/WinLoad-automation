@echo off
cd /d "%~dp0"
echo Starting Wind Automation Pipeline...
echo.

python bin/runner.py

echo.
if %ERRORLEVEL% == 0 (
    echo Pipeline completed successfully.
) else (
    echo Pipeline FAILED. See errors above.
)

pause

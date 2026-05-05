@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  clean_data.bat
::  Place this file inside the data\ folder and run from there.
::
::  KEEPS:
::    STxxxx_Wind load check.xlsx   (output template)
::    schemes_input.xlsx            (input template)
::    clean_data.bat                (this script)
::
::  DELETES:
::    schemes_output.xlsx           (generated output)
::    reports\*                    (generated reports)
::    temp\*                       (temporary JSON files)
:: ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo  Wind Load Automation - Clean Data Folder
echo ============================================================
echo.
echo The following will be deleted:
echo   schemes_output.xlsx
echo   reports\*  (all files)
echo   temp\*     (all files)
echo.
set /p CONFIRM=Are you sure? (Y/N): 
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    exit /b 0
)

echo.

:: ── Delete generated output Excel ─────────────────────────────────────────
if exist "schemes_output.xlsx" (
    del /f /q "schemes_output.xlsx"
    echo [DELETED]  schemes_output.xlsx
) else (
    echo [SKIPPED]  schemes_output.xlsx (not found)
)

:: ── Clear reports folder (keep the folder itself) ─────────────────────────
if exist "reports\" (
    del /f /q "reports\*.*" >nul 2>&1
    for /d %%D in ("reports\*") do rd /s /q "%%D" >nul 2>&1
    echo [CLEARED]  reports\
) else (
    mkdir "reports"
    echo [CREATED]  reports\  (was missing)
)

:: Ensure .gitkeep exists in reports\
type nul > "reports\.gitkeep"

:: ── Clear temp folder (keep the folder itself) ────────────────────────────
if exist "temp\" (
    del /f /q "temp\*.*" >nul 2>&1
    for /d %%D in ("temp\*") do rd /s /q "%%D" >nul 2>&1
    echo [CLEARED]  temp\
) else (
    mkdir "temp"
    echo [CREATED]  temp\  (was missing)
)

:: Ensure .gitkeep exists in temp\
type nul > "temp\.gitkeep"

echo.
echo ============================================================
echo  Done. Template files preserved:
echo    STxxxx_Wind load check.xlsx
echo    schemes_input.xlsx
echo    reports\.gitkeep
echo    temp\.gitkeep
echo ============================================================
echo.

endlocal
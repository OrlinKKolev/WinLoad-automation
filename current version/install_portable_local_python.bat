@echo off
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

echo ===============================================
echo   Wind Automation - Portable Local Installer
echo ===============================================
echo.

set "PY_VER=3.11.9"
set "PY_SHORT=311"
set "PY_ZIP=python-%PY_VER%-embed-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/%PY_ZIP%"
set "PY_DIR=%CD%\runtime\python"
set "GETPIP=%PY_DIR%\get-pip.py"

echo [1/7] Creating runtime folder...
if not exist "runtime" mkdir "runtime"
if not exist "%PY_DIR%" mkdir "%PY_DIR%"

echo [2/7] Downloading embedded Python...
powershell -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%TEMP%\%PY_ZIP%'"
if errorlevel 1 (
    echo [ERROR] Failed to download embedded Python.
    set "FINAL_ERROR=1"
    goto :END
)

echo [3/7] Extracting embedded Python...
powershell -Command "Expand-Archive -Force '%TEMP%\%PY_ZIP%' '%PY_DIR%'"
if errorlevel 1 (
    echo [ERROR] Failed to extract embedded Python.
    set "FINAL_ERROR=1"
    goto :END
)

echo [4/7] Enabling site-packages...
powershell -Command ^
    "$pth='%PY_DIR%\python%PY_SHORT%._pth';" ^
    "$c=Get-Content $pth;" ^
    "$c=$c -replace '#import site','import site';" ^
    "Set-Content -Encoding ASCII $pth $c"
if errorlevel 1 (
    echo [ERROR] Failed to update python%PY_SHORT%._pth
    set "FINAL_ERROR=1"
    goto :END
)

echo [5/7] Downloading get-pip.py...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%GETPIP%'"
if errorlevel 1 (
    echo [ERROR] Failed to download get-pip.py
    set "FINAL_ERROR=1"
    goto :END
)

echo [6/7] Installing pip and Python packages...
"%PY_DIR%\python.exe" "%GETPIP%"
if errorlevel 1 (
    echo [ERROR] Failed to install pip in embedded Python.
    set "FINAL_ERROR=1"
    goto :END
)

"%PY_DIR%\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    set "FINAL_ERROR=1"
    goto :END
)

"%PY_DIR%\python.exe" -m pip install pandas openpyxl pillow requests playwright pywin32
if errorlevel 1 (
    echo [ERROR] Failed to install required packages.
    set "FINAL_ERROR=1"
    goto :END
)

echo [7/7] Installing Playwright Chromium...
set "PLAYWRIGHT_BROWSERS_PATH=0"
"%PY_DIR%\python.exe" -m playwright install chromium
if errorlevel 1 (
    echo [ERROR] Failed to install Playwright Chromium.
    set "FINAL_ERROR=1"
    goto :END
)

echo Cleaning temporary files...
if exist "%TEMP%\%PY_ZIP%" del /f /q "%TEMP%\%PY_ZIP%"
if exist "%GETPIP%" del /f /q "%GETPIP%"

set "FINAL_ERROR=0"

:END
echo.
if "%FINAL_ERROR%"=="0" (
    echo Portable installation completed successfully.
    echo From now on, the user only needs to run the pipeline BAT.
) else (
    echo Installation FAILED.
    echo Review the messages above to see where it stopped.
)
echo.
pause
endlocal
exit /b %FINAL_ERROR%
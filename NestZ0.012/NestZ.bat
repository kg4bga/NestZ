@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  Nested ZIP Extractor - Setup Script
::  1. Checks if Python is installed
::  2. Installs Python if missing
::  3. Creates a Desktop shortcut for the extractor
:: ============================================================

title Nested ZIP Extractor Setup
color 0A
echo.
echo ========================================
echo   Nested ZIP Extractor - Setup
echo ========================================
echo.

:: ----------------------------------------------------------
:: Configuration - change these if needed
:: ----------------------------------------------------------
set "SCRIPT_NAME=nested_zip_extractor.py"
set "SHORTCUT_NAME=Nested ZIP Extractor.lnk"
set "PYTHON_VERSION=3.12.7"
set "PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%"

:: Get the folder where this .bat lives
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%%SCRIPT_NAME%"

:: Desktop path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"

echo [INFO] Script folder : %SCRIPT_DIR%
echo [INFO] Python script : %PYTHON_SCRIPT%
echo [INFO] Desktop       : %DESKTOP%
echo.

:: ----------------------------------------------------------
:: 1. Check if the Python script exists
:: ----------------------------------------------------------
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Cannot find "%SCRIPT_NAME%"
    echo         Please put this .bat file in the same folder as the Python script.
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------
:: 2. Check if Python is already installed
:: ----------------------------------------------------------
echo [1/3] Checking for Python...

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    echo       Found: !PY_VER!
    goto :create_shortcut
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('py --version 2^>^&1') do set "PY_VER=%%v"
    echo       Found: !PY_VER!  (via py launcher)
    goto :create_shortcut
)

echo       Python is NOT installed.
echo.

:: ----------------------------------------------------------
:: 3. Install Python
:: ----------------------------------------------------------
echo [2/3] Installing Python %PYTHON_VERSION% ...
echo.

:: Try winget first (cleanest method on Windows 10/11)
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo       Using winget...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
    if !errorlevel! equ 0 (
        echo       Python installed successfully via winget.
        goto :refresh_path
    )
    echo       winget install failed, falling back to official installer...
)

:: Fallback: download official installer
echo       Downloading official Python installer...
set "INSTALLER=%TEMP%\%PYTHON_INSTALLER%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%' -UseBasicParsing"

if not exist "%INSTALLER%" (
    echo [ERROR] Failed to download Python installer.
    echo         Please install Python manually from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo       Running silent install (this may take a minute)...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_pip=1 Include_tcltk=1

:: Clean up installer
del /f /q "%INSTALLER%" >nul 2>&1

:refresh_path
:: Refresh PATH in the current session
echo       Refreshing PATH...
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"

:: Final check
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo [WARNING] Python was installed but is not yet available in this terminal.
        echo           Please close this window, open a NEW Command Prompt, and run the script again
        echo           OR just create the shortcut manually.
        echo.
        pause
        exit /b 1
    )
)

echo       Python is now available.
echo.

:: ----------------------------------------------------------
:: 4. Create Desktop Shortcut
:: ----------------------------------------------------------
:create_shortcut
echo [3/3] Creating Desktop shortcut...

:: Determine which python command to use
set "PYTHON_CMD=python"
where python >nul 2>&1
if %errorlevel% neq 0 set "PYTHON_CMD=py"

set "SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%"

:: Use PowerShell to create a proper .lnk shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$s.TargetPath = 'cmd.exe'; " ^
    "$s.Arguments = '/c start \"\" \"%PYTHON_CMD%\" \"%PYTHON_SCRIPT%\"'; " ^
    "$s.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$s.Description = 'Nested ZIP Extractor'; " ^
    "$s.IconLocation = 'shell32.dll,45'; " ^
    "$s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo       Shortcut created successfully:
    echo       %SHORTCUT_PATH%
) else (
    echo [ERROR] Failed to create shortcut.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup completed successfully!
echo ========================================
echo.
echo You can now double-click the shortcut on your Desktop
echo to run the Nested ZIP Extractor.
echo.
pause
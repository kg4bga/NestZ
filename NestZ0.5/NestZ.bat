@echo off
setlocal EnableDelayedExpansion

title Nested ZIP Extractor - Setup
color 0A
echo.
echo ========================================
echo   Nested ZIP Extractor - Full Setup
echo ========================================
echo.

set "SCRIPT_NAME=nested_zip_extractor.py"
set "SHORTCUT_NAME=Nested ZIP Extractor.lnk"
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%%SCRIPT_NAME%"

:: Desktop path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"

echo [INFO] Script folder : %SCRIPT_DIR%
echo.

if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Cannot find "%SCRIPT_NAME%"
    echo         Put this .bat in the same folder as the Python script.
    pause
    exit /b 1
)

:: ----------------------------------------------------------
:: 1. Check / Install Python
:: ----------------------------------------------------------
echo [1/4] Checking for Python...

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo       Found: %%v
    goto :install_deps
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo       Found: %%v
    goto :install_deps
)

echo       Python not found. Installing...

where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo       Using winget...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
) else (
    echo       Downloading official installer...
    set "INSTALLER=%TEMP%\python-3.12.7-amd64.exe"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
        "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '!INSTALLER!' -UseBasicParsing"
    
    if exist "!INSTALLER!" (
        "!INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
        del /f /q "!INSTALLER!" >nul 2>&1
    )
)

:: Refresh PATH
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"

:install_deps
echo.
echo [2/4] Installing required packages...

python -m pip install --upgrade pip >nul 2>&1
python -m pip install tkinterdnd2 sv_ttk

if %errorlevel% neq 0 (
    echo       Trying with py launcher...
    py -m pip install --upgrade pip >nul 2>&1
    py -m pip install tkinterdnd2 sv_ttk
)

echo       Done.
echo.

:: ----------------------------------------------------------
:: 3. Create Desktop Shortcut
:: ----------------------------------------------------------
echo [3/4] Creating Desktop shortcut...

set "PYTHON_CMD=python"
where python >nul 2>&1
if %errorlevel% neq 0 set "PYTHON_CMD=py"

set "SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$s.TargetPath = 'cmd.exe'; " ^
    "$s.Arguments = '/c start \"\" \"%PYTHON_CMD%\" \"%PYTHON_SCRIPT%\"'; " ^
    "$s.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$s.Description = 'Nested ZIP Extractor'; " ^
    "$s.IconLocation = 'shell32.dll,45'; " ^
    "$s.Save()"

echo       Shortcut created: %SHORTCUT_PATH%
echo.

echo [4/4] Setup complete!
echo.
echo ========================================
echo   You can now run the program from the
echo   Desktop shortcut or by double-clicking
echo   the .py file.
echo ========================================
echo.
pause
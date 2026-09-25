@echo off
setlocal
title HamiScraper - Windows Build
cd /d "%~dp0"

echo ==========================================
echo   HamiScraper - Windows Build
echo ==========================================
echo.

REM ---------------------------------------------------------------
REM  1. Locate a Python interpreter
REM ---------------------------------------------------------------
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)

if not defined PY (
    echo [ERROR] Python was not found on this machine.
    echo.
    echo         Install Python 3.10 or newer from
    echo             https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" during setup,
    echo         then close this window and run the script again.
    goto :fail
)

echo [1/5] Using Python:
%PY% --version
if errorlevel 1 goto :fail
echo.

REM ---------------------------------------------------------------
REM  2. Install build + runtime dependencies
REM ---------------------------------------------------------------
echo [2/5] Installing dependencies ^(this may take a few minutes^)...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install the packages listed in requirements.txt.
    goto :fail
)
echo.

REM ---------------------------------------------------------------
REM  3. Clean previous build output  (never delete the .spec file)
REM ---------------------------------------------------------------
echo [3/5] Cleaning previous build output...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
echo.

REM ---------------------------------------------------------------
REM  4. Build the executable
REM ---------------------------------------------------------------
echo [4/5] Building HamiScraper.exe ^(this takes several minutes^)...
%PY% -m PyInstaller --noconfirm --clean build_windows.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller reported an error. See the output above.
    goto :fail
)
echo.

REM ---------------------------------------------------------------
REM  5. Verify and stage the release folder
REM ---------------------------------------------------------------
echo [5/5] Verifying output...
if not exist "dist\HamiScraper.exe" (
    echo [ERROR] dist\HamiScraper.exe was not produced.
    goto :fail
)

REM pairs.json is the hami list, it is not secret and the app expects it
REM next to the exe. config.json is NOT copied - it holds credentials.
if exist "pairs.json" copy /y "pairs.json" "dist\pairs.json" >nul

echo.
echo ==========================================
echo   BUILD SUCCESSFUL
echo ==========================================
echo.
echo   Executable : %CD%\dist\HamiScraper.exe
echo.
echo   Ship the whole "dist" folder. On first run the app creates
echo   its own config.json next to the exe.
echo.
echo   Remember: the app still needs chromedriver.exe on the target
echo   machine, matching the installed Google Chrome version.
echo.
pause
exit /b 0

:fail
echo.
echo ==========================================
echo   BUILD FAILED
echo ==========================================
echo.
pause
exit /b 1

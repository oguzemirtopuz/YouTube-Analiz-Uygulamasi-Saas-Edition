@echo off
setlocal
chcp 65001 >nul
echo =========================================
echo Analysis Pro AI - Full Deployment Script
echo =========================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "SRC_DB=%~dp0channels.db"
set "SRC_DIR=%~dp0"

:: ── ADIM 1: Masaustu Temizligi ─────────────────────────────
echo [1/4] Cleaning the desktop...
if exist "%DESKTOP%\Analiz Pro AI.exe"  del /F /Q "%DESKTOP%\Analiz Pro AI.exe"
if exist "%DESKTOP%\server.exe"          del /F /Q "%DESKTOP%\server.exe"
if exist "%DESKTOP%\channels.db"         del /F /Q "%DESKTOP%\channels.db"
for %%f in ("%DESKTOP%\*.lnk") do       del /F /Q "%%f"
echo Cleaning is ok.
echo.

:: ── ADIM 2: Dogru DB'yi Masaustune Kopyala ─────────────────
echo [2/4] Copying the correct database (containing OğuzE)...
if not exist "%SRC_DB%" (
    echo.
    echo ERROR: Source DB not found!
    echo Searched path: %SRC_DB%
    echo Please check the road.
    pause
    exit /b 1
)
copy /Y "%SRC_DB%" "%DESKTOP%\channels.db" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy DB!
    pause
    exit /b 1
)
echo channels.db was copied successfully.
echo.

:: ── ADIM 3: Build ──────────────────────────────────────────
echo [3/4] Starting the build (running build.bat)...
cd /D "%SRC_DIR%"
if not exist "build.bat" (
    echo ERROR: build.bat not found! It should be in the same folder as the script.
    pause
    exit /b 1
)
call build.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Compilation failed! See the error message above.
    pause
    exit /b 1
)
echo.

:: ── ADIM 4: EXE'yi Masaustune Tasi ────────────────────────
echo [4/4] Transferring EXE to desktop...
if exist "dist\Analiz Pro AI.exe" (
    copy /Y "dist\Analiz Pro AI.exe" "%DESKTOP%\Analiz Pro AI.exe" >nul
    echo EXE copied.
) else (
    echo WARNING: EXE not found in disk folder. Build.bat may have already been moved.
)

echo.
echo =========================================
echo DONE!
echo.
echo Files on the desktop:
echo - Analysis Pro AI.exe (compiled application)
echo - channels.db (real data containing OguzE)
echo.
echo Database Path Made Dynamic.
echo Original Data Moved to Desktop Next to EXE.
echo You can log in.
echo =========================================
pause

@echo off
setlocal
echo =========================================
echo Analysis Pro AI - Automated Compilation System
echo =========================================
echo.

echo Cleaning is being done (build, dist folders are being deleted)...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo.
echo Starting compilation with PyInstaller...
python -m PyInstaller --clean server.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] A problem occurred during compilation!
    pause
    exit /b %ERRORLEVEL%
)

echo Transferring to desktop...
set "DESKTOP_PATH=%USERPROFILE%\Desktop\Analiz Pro AI.exe"
copy /Y "dist\Analiz Pro AI.exe" "%DESKTOP_PATH%"

echo.
echo =========================================
powershell -Command "Write-Host 'SİSTEM: Masaüstüne başarıyla aktarıldı!' -ForegroundColor Green"
echo Location: %DESKTOP_PATH%
echo =========================================
echo.

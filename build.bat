@echo off
setlocal
echo =========================================
echo  Analiz Pro AI - Otomatik Derleme Sistemi
echo =========================================
echo.

echo Temizlik yapiliyor (build, dist klasorleri siliniyor)...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo.
echo PyInstaller ile derleme baslatiliyor...
python -m PyInstaller --clean server.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Derleme sirasinda bir sorun olustu!
    pause
    exit /b %ERRORLEVEL%
)

echo Masaustune aktariliyor...
set "DESKTOP_PATH=%USERPROFILE%\Desktop\Analiz Pro AI.exe"
copy /Y "dist\Analiz Pro AI.exe" "%DESKTOP_PATH%"

echo.
echo =========================================
powershell -Command "Write-Host 'SİSTEM: Masaüstüne başarıyla aktarıldı!' -ForegroundColor Green"
echo Konum: %DESKTOP_PATH%
echo =========================================
echo.

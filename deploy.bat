@echo off
setlocal
chcp 65001 >nul
echo =========================================
echo  Analiz Pro AI - Tam Deployment Scripti
echo =========================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "SRC_DB=%~dp0channels.db"
set "SRC_DIR=%~dp0"

:: ── ADIM 1: Masaustu Temizligi ─────────────────────────────
echo [1/4] Masaustu temizleniyor...
if exist "%DESKTOP%\Analiz Pro AI.exe"  del /F /Q "%DESKTOP%\Analiz Pro AI.exe"
if exist "%DESKTOP%\server.exe"          del /F /Q "%DESKTOP%\server.exe"
if exist "%DESKTOP%\channels.db"         del /F /Q "%DESKTOP%\channels.db"
for %%f in ("%DESKTOP%\*.lnk") do       del /F /Q "%%f"
echo    Temizlik tamam.
echo.

:: ── ADIM 2: Dogru DB'yi Masaustune Kopyala ─────────────────
echo [2/4] Dogru veritabani (OguzE iceren) kopyalaniyor...
if not exist "%SRC_DB%" (
    echo.
    echo   HATA: Kaynak DB bulunamadi!
    echo   Aranan yol: %SRC_DB%
    echo   Lutfen yolu kontrol edin.
    pause
    exit /b 1
)
copy /Y "%SRC_DB%" "%DESKTOP%\channels.db" >nul
if %ERRORLEVEL% NEQ 0 (
    echo   HATA: DB kopyalanamadi!
    pause
    exit /b 1
)
echo    channels.db basariyla kopyalandi.
echo.

:: ── ADIM 3: Build ──────────────────────────────────────────
echo [3/4] Derleme baslatiliyor (build.bat calistiriliyor)...
cd /D "%SRC_DIR%"
if not exist "build.bat" (
    echo   HATA: build.bat bulunamadi! Script ile ayni klasorde olmali.
    pause
    exit /b 1
)
call build.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   HATA: Derleme basarisiz! Yukaridaki hata mesajina bakin.
    pause
    exit /b 1
)
echo.

:: ── ADIM 4: EXE'yi Masaustune Tasi ────────────────────────
echo [4/4] EXE masaustune aktariliyor...
if exist "dist\Analiz Pro AI.exe" (
    copy /Y "dist\Analiz Pro AI.exe" "%DESKTOP%\Analiz Pro AI.exe" >nul
    echo    EXE kopyalandi.
) else (
    echo   UYARI: dist klasorunde EXE bulunamadi. Build.bat zaten tasimis olabilir.
)

echo.
echo =========================================
echo  TAMAMLANDI!
echo.
echo  Masaustundeki dosyalar:
echo    - Analiz Pro AI.exe   (derlenmis uygulama)
echo    - channels.db         (OguzE iceren gercek veri)
echo.
echo  Veritabani Yolu Dinamik Yapildi.
echo  Asil Veriler Masaustune EXE'nin Yanina Tasindi.
echo  Giris Yapabilirsiniz.
echo =========================================
pause

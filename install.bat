@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title YouTube Analiz Pro - Kurulum Sihirbazi

:: ============================================================
::   ██╗   ██╗████████╗██╗   ██╗██████╗ ███████╗    
::   ╚██╗ ██╔╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝    
::    ╚████╔╝    ██║   ██║   ██║██████╔╝█████╗      
::     ╚██╔╝     ██║   ██║   ██║██╔══██╗██╔══╝      
::      ██║      ██║   ╚██████╔╝██████╔╝███████╗    
::      ╚═╝      ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝    
::   YouTube Analiz Pro - 1-Click Installer v1.0
::   Global SaaS Setup Wizard
:: ============================================================

:: Proje kok dizini (bu script nerede calisiyorsa orasi)
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "FFMPEG_DIR=%PROJECT_DIR%ffmpeg"
set "FFMPEG_BIN=%FFMPEG_DIR%\bin"

:: ─── Renk fonksiyonu icin gecici vbs ────────────────────────
set "LOG_FILE=%PROJECT_DIR%install_log.txt"
echo. > "%LOG_FILE%"

call :print_banner
call :step_python
call :step_venv
call :step_ffmpeg
call :step_shortcut
call :finish
goto :eof

:: ============================================================
:: BANNER
:: ============================================================
:print_banner
cls
echo.
echo  ==========================================================
echo    YouTube Analiz Pro ^| 1-Click Installer
echo    Global SaaS Setup Wizard - v1.0
echo  ==========================================================
echo.
echo  Bu sihirbaz asagidaki adimlari otomatik gerceklestirecek:
echo    [1] Python kontrolu
echo    [2] Virtual Environment (venv) kurulumu
echo    [3] FFmpeg kurulumu ^(yoksa otomatik indirilir^)
echo    [4] Masaustu kisayolu olusturma
echo.
echo  ==========================================================
echo.
goto :eof


:: ============================================================
:: ADIM 1 — PYTHON KONTROLU
:: ============================================================
:step_python
echo  [1/4] Python kontrol ediliyor...
echo.

:: python komutunu dene
python --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    set "PYTHON_CMD=python"
    goto :python_ok
)

:: py launcher'i dene
py --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%v in ('py --version 2^>^&1') do set "PY_VER=%%v"
    set "PYTHON_CMD=py"
    goto :python_ok
)

:: Python bulunamadi
echo  [HATA] Python sisteminizde bulunamadi!
echo.
echo  Lutfen Python 3.10 veya uzeri yukleyin:
echo    https://www.python.org/downloads/
echo.
echo  ONEMLI: Kurulum sirasinda "Add Python to PATH"
echo           kutucugunu isaretle!
echo.
echo  Kurulumdan sonra bu scripti tekrar calistirin.
echo.
echo  [Herhangi bir tusa basin cikmak icin...]
pause >nul
exit /b 1

:python_ok
echo  [OK] !PY_VER! bulundu  (komut: !PYTHON_CMD!)
echo.
goto :eof


:: ============================================================
:: ADIM 2 — VIRTUAL ENVIRONMENT + REQUIREMENTS
:: ============================================================
:step_venv
echo  [2/4] Virtual Environment kurulumu...
echo.

:: Zaten venv var mi?
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo  [OK] Mevcut venv bulundu, atlanıyor...
    echo       Konum: %VENV_DIR%
    echo.
    goto :install_requirements
)

:: venv olustur
echo  [..] venv olusturuluyor: %VENV_DIR%
!PYTHON_CMD! -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo.
    echo  [HATA] venv olusturulamadi!
    echo         Lutfen Python kurulumunu kontrol edin.
    pause >nul
    exit /b 1
)
echo  [OK] venv olusturuldu.
echo.

:install_requirements
echo  [..] Gerekli paketler yukleniyor (bu birkaç dakika surebilir)...
echo       Lutfen bekleyin...
echo.

:: pip'i guncelle
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet 2>>"%LOG_FILE%"

:: requirements.txt kur
"%VENV_DIR%\Scripts\pip.exe" install -r "%PROJECT_DIR%requirements.txt" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo  [UYARI] Bazi paketler yuklenemedi. Detaylar icin install_log.txt dosyasina bakin.
    echo.
) else (
    echo  [OK] Tum Python paketleri basariyla yuklendi.
    echo.
)
goto :eof


:: ============================================================
:: ADIM 3 — FFMPEG KONTROLU + OTOMATIK KURULUM
:: ============================================================
:step_ffmpeg
echo  [3/4] FFmpeg kontrol ediliyor...
echo.

:: 1) Sistem PATH'inde var mi?
where ffmpeg >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%v in ('ffmpeg -version 2^>^&1 ^| findstr /i "version"') do (
        set "FF_VER=%%v"
        goto :ffmpeg_sys_ok
    )
    :ffmpeg_sys_ok
    echo  [OK] FFmpeg sistem PATH'inde bulundu.
    echo       !FF_VER!
    echo.
    goto :eof
)

:: 2) Proje icinde (./ffmpeg/bin) var mi?
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo  [OK] FFmpeg proje icinde bulundu: %FFMPEG_BIN%
    echo.
    goto :eof
)

:: 3) FFmpeg yok — otomatik indir
echo  [!!] FFmpeg bulunamadi. Otomatik olarak indiriliyor...
echo.
echo       Kaynak: https://github.com/BtbN/FFmpeg-Builds
echo       Bu islem internet baglantisi gerektirir.
echo       Lutfen bekleyin...
echo.

:: Indirme URL'si (BtbN FFmpeg-Builds — GPL, essentials, win64)
set "FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
set "FFMPEG_ZIP=%TEMP%\ffmpeg_download.zip"
set "FFMPEG_EXTRACT=%TEMP%\ffmpeg_extracted"

:: Eski dosyalari temizle
if exist "%FFMPEG_ZIP%" del /f /q "%FFMPEG_ZIP%"
if exist "%FFMPEG_EXTRACT%" rmdir /s /q "%FFMPEG_EXTRACT%"

:: PowerShell ile indir (progress goster)
echo  [..] Indiriliyor, lutfen bekleyin (bu biraz zaman alabilir)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$progressPreference='silentlyContinue'; " ^
    "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'"

if %errorlevel% neq 0 (
    echo.
    echo  [HATA] FFmpeg indirilemedi!
    echo.
    echo  Manuel kurulum secenekleri:
    echo    1) winget : PowerShell'de  winget install Gyan.FFmpeg  calistirin
    echo    2) Choco  : choco install ffmpeg
    echo    3) Manuel : https://ffmpeg.org/download.html adresinden indirip
    echo               ffmpeg.exe'yi  %FFMPEG_BIN%  klasorune koyun.
    echo.
    echo  Kuruluma devam ediliyor (FFmpeg olmadan bazi ozellikler calismayabilir)...
    echo.
    goto :eof
)

echo  [OK] Indirme tamamlandi.
echo  [..] ZIP dosyasi aciliyor...

:: Zip'i cikart
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_EXTRACT%' -Force"

if %errorlevel% neq 0 (
    echo  [HATA] ZIP acilamadi. Kurulum devam ediyor (FFmpeg eksik olabilir).
    goto :eof
)

:: Cikan klasoru bul (iceride tek bir klasor var: ffmpeg-master-...)
set "FFMPEG_INNER="
for /d %%d in ("%FFMPEG_EXTRACT%\*") do (
    if exist "%%d\bin\ffmpeg.exe" set "FFMPEG_INNER=%%d"
)

if not defined FFMPEG_INNER (
    echo  [HATA] ZIP icinden ffmpeg.exe bulunamadi.
    goto :eof
)

:: Proje icine kopyala
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
xcopy /e /i /q /y "%FFMPEG_INNER%\bin" "%FFMPEG_BIN%" >nul 2>&1
xcopy /e /i /q /y "%FFMPEG_INNER%\lib" "%FFMPEG_DIR%\lib" >nul 2>&1

:: Temizle
del /f /q "%FFMPEG_ZIP%" >nul 2>&1
rmdir /s /q "%FFMPEG_EXTRACT%" >nul 2>&1

:: Dogrula
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo  [OK] FFmpeg basariyla kuruldu: %FFMPEG_BIN%
    echo.
    echo  NOT: FFmpeg proje klasorune kuruldu.
    echo       Uygulama otomatik olarak bu yolu kullanacak.
    echo.
    
    :: Bu oturum icin PATH'e ekle (kalici degil, sadece dogrulama icin)
    set "PATH=%FFMPEG_BIN%;%PATH%"
) else (
    echo  [UYARI] FFmpeg kopyalanamadi. Lutfen manuel kurun.
    echo.
)
goto :eof


:: ============================================================
:: ADIM 4 — MASAUSTU KISAYOLU
:: ============================================================
:step_shortcut
echo  [4/4] Masaustu kisayolu olusturuluyor...
echo.

set "SHORTCUT_NAME=YouTube Analiz Pro"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\%SHORTCUT_NAME%.lnk"
set "LAUNCHER_BAT=%PROJECT_DIR%BASLAT.bat"

:: venv ile calisacak ozel launcher olustur
set "SMART_LAUNCHER=%PROJECT_DIR%launch.bat"
(
    echo @echo off
    echo setlocal
    echo cd /d "%PROJECT_DIR%"
    echo.
    echo :: FFmpeg PATH'e ekle (proje icinde kurulduysa^)
    echo if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo     set "PATH=%FFMPEG_BIN%;%%PATH%%"
    echo ^)
    echo.
    echo :: venv aktif et ve uygulamayi baslat
    echo if exist "%VENV_DIR%\Scripts\pythonw.exe" (
    echo     start /min "" "%VENV_DIR%\Scripts\pythonw.exe" "%PROJECT_DIR%server.pyw"
    echo ^) else (
    echo     start /min "" pythonw "%PROJECT_DIR%server.pyw"
    echo ^)
    echo exit
) > "%SMART_LAUNCHER%"

:: PowerShell ile .lnk olustur
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$Shortcut.TargetPath = '%SMART_LAUNCHER%'; " ^
    "$Shortcut.WorkingDirectory = '%PROJECT_DIR%'; " ^
    "$Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,220'; " ^
    "$Shortcut.WindowStyle = 7; " ^
    "$Shortcut.Description = 'YouTube Analiz Pro - SaaS Edition'; " ^
    "$Shortcut.Save()"

if %errorlevel% == 0 (
    echo  [OK] Masaustu kisayolu olusturuldu:
    echo       "%SHORTCUT_PATH%"
    echo.
) else (
    echo  [UYARI] Kisayol olusturulamadi. Uygulamayi BASLAT.bat ile balatabilirsiniz.
    echo.
)
goto :eof


:: ============================================================
:: KURULUM TAMAMLANDI
:: ============================================================
:finish
echo.
echo  ==========================================================
echo    KURULUM TAMAMLANDI!
echo  ==========================================================
echo.
echo  Uygulamayi asagidaki yontemlerden biriyle baslatabilirsiniz:
echo.
echo    [1] Masaustu'ndeki "YouTube Analiz Pro" kisayoluna cift tiklayin
echo    [2] launch.bat dosyasini calistirin
echo    [3] BASLAT.bat dosyasini calistirin
echo.
echo  Uygulama basladiktan sonra tarayicinizda acilir:
echo    http://127.0.0.1:8000
echo.
echo  Herhangi bir sorun icin install_log.txt dosyasini inceleyin.
echo  ==========================================================
echo.

:: Bekleme sayaci (5sn sonra kapanir ya da tusa basinca)
echo  Bu pencere 10 saniye sonra kapanacak...
echo  (Hemen kapatmak icin herhangi bir tusa basin)
echo.
timeout /t 10 /nobreak >nul 2>&1
exit /b 0

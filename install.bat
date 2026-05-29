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
echo . > "%LOG_FILE%"

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
echo YouTube Analysis Pro ^| 1-Click Installer
echo Global SaaS Setup Wizard - v1.0
echo  ==========================================================
echo.
echo This wizard will automatically perform the following steps:
echo [1] Python control
echo [2] Virtual Environment (venv) installation
echo [3] FFmpeg installation ^(otherwise it will be downloaded automatically^)
echo [4] Creating a desktop shortcut
echo.
echo  ==========================================================
echo.
goto :eof


:: ============================================================
:: ADIM 1 — PYTHON KONTROLU
:: ============================================================
:step_python
echo [1/4] Checking Python...
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
echo [ERROR] Python was not found on your system!
echo.
echo Please install Python 3.10 or later:
echo https://www.python.org/downloads/
echo.
echo IMPORTANT: "Add Python to PATH" during installation
echo Check the box!
echo.
echo After installation, run this script again.
echo.
echo [Press any key to exit...]
pause >nul
exit /b 1

:python_ok
echo [OK] !PY_VER! found (command: !PYTHON_CMD!)
echo.
goto :eof


:: ============================================================
:: ADIM 2 — VIRTUAL ENVIRONMENT + REQUIREMENTS
:: ============================================================
:step_venv
echo [2/4] Virtual Environment installation...
echo.

:: Zaten venv var mi?
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [OK] Existing venv found, skipping...
    echo Location: %VENV_DIR%
    echo.
    goto :install_requirements
)

:: venv olustur
echo [..] creating venv: %VENV_DIR%
!PYTHON_CMD! -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create venv!
    echo Please check the Python installation.
    pause >nul
    exit /b 1
)
echo [OK] venv created.
echo.

:install_requirements
echo [..] Installing the necessary packages (this may take a few minutes)...
echo Please wait...
echo.

:: pip'i guncelle
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet 2>>"%LOG_FILE%"

:: requirements.txt kur
"%VENV_DIR%\Scripts\pip.exe" install -r "%PROJECT_DIR%requirements.txt" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo [WARNING] Some packages could not be installed. See install_log.txt for details.
    echo.
) else (
    echo [OK] All Python packages have been installed successfully.
    echo.
)
goto :eof


:: ============================================================
:: ADIM 3 — FFMPEG KONTROLU + OTOMATIK KURULUM
:: ============================================================
:step_ffmpeg
echo [3/4] Checking FFmpeg...
echo.

:: 1) Sistem PATH'inde var mi?
where ffmpeg >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=*" %%v in ('ffmpeg -version 2^>^&1 ^| findstr /i "version"') do (
        set "FF_VER=%%v"
        goto :ffmpeg_sys_ok
    )
    :ffmpeg_sys_ok
    echo [OK] FFmpeg found in system PATH.
    echo !FF_VER!
    echo.
    goto :eof
)

:: 2) Proje icinde (./ffmpeg/bin) var mi?
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo [OK] FFmpeg found in project: %FFMPEG_BIN%
    echo.
    goto :eof
)

:: 3) FFmpeg yok — otomatik indir
echo [!!] FFmpeg not found. Downloading automatically...
echo.
echo Source: https://github.com/BtbN/FFmpeg-Builds
echo This process requires an internet connection.
echo Please wait...
echo.

:: Indirme URL'si (BtbN FFmpeg-Builds — GPL, essentials, win64)
set "FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
set "FFMPEG_ZIP=%TEMP%\ffmpeg_download.zip"
set "FFMPEG_EXTRACT=%TEMP%\ffmpeg_extracted"

:: Eski dosyalari temizle
if exist "%FFMPEG_ZIP%" del /f /q "%FFMPEG_ZIP%"
if exist "%FFMPEG_EXTRACT%" rmdir /s /q "%FFMPEG_EXTRACT%"

:: PowerShell ile indir (progress goster)
echo [..] Downloading, please wait (this may take some time)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$progressPreference='silentlyContinue'; " ^
    "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to download FFmpeg!
    echo.
    echo Manual installation options:
    echo 1) winget : Run winget install Gyan.FFmpeg in PowerShell
    echo 2) Choco: choco install ffmpeg
    echo 3) Manual: Download from https://ffmpeg.org/download.html
    echo Put ffmpeg.exe in the %FFMPEG_BIN% folder.
    echo.
    echo Installation continues (some features may not work without FFmpeg)...
    echo.
    goto :eof
)

echo [OK] Download completed.
echo [..] Opening the ZIP file...

:: Zip'i cikart
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_EXTRACT%' -Force"

if %errorlevel% neq 0 (
    echo [ERROR] ZIP could not be opened. Installation in progress (FFmpeg may be missing).
    goto :eof
)

:: Cikan klasoru bul (iceride tek bir klasor var: ffmpeg-master-...)
set "FFMPEG_INNER="
for /d %%d in ("%FFMPEG_EXTRACT%\*") do (
    if exist "%%d\bin\ffmpeg.exe" set "FFMPEG_INNER=%%d"
)

if not defined FFMPEG_INNER (
    echo [ERROR] ffmpeg.exe could not be found in the ZIP.
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
    echo [OK] FFmpeg installed successfully: %FFMPEG_BIN%
    echo.
    echo NOTE: FFmpeg was installed in the project folder.
    echo The application will automatically use this path.
    echo.
    
    :: Bu oturum icin PATH'e ekle (kalici degil, sadece dogrulama icin)
    set "PATH=%FFMPEG_BIN%;%PATH%"
) else (
    echo [WARNING] Failed to copy FFmpeg. Please install manually.
    echo.
)
goto :eof


:: ============================================================
:: ADIM 4 — MASAUSTU KISAYOLU
:: ============================================================
:step_shortcut
echo [4/4] Creating a desktop shortcut...
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
    echo :: Add FFmpeg to PATH (if installed within the project^)
    echo if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo set "PATH=%FFMPEG_BIN%;%%PATH%%"
    echo ^)
    echo.
    echo ::activate venv and start the application
    echo if exist "%VENV_DIR%\Scripts\pythonw.exe" (
    echo start /min "" "%VENV_DIR%\Scripts\pythonw.exe" "%PROJECT_DIR%server.pyw"
    echo ^) else (
    echo start /min "" pythonw "%PROJECT_DIR%server.pyw"
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
    echo [OK] Desktop shortcut created:
    echo "%SHORTCUT_PATH%"
    echo.
) else (
    echo [WARNING] Failed to create shortcut. You can start the application with START.bat.
    echo.
)
goto :eof


:: ============================================================
:: KURULUM TAMAMLANDI
:: ============================================================
:finish
echo.
echo  ==========================================================
echo INSTALLATION IS COMPLETE!
echo  ==========================================================
echo.
echo You can start the application in one of the following ways:
echo.
echo [1] Double-click the "YouTube Analysis Pro" shortcut on the desktop
echo [2] Run launch.bat
echo [3] Run the START.bat file
echo.
echo After the application starts, it opens in your browser:
echo http://127.0.0.1:8000
echo.
echo Review the install_log.txt file for any problems.
echo  ==========================================================
echo.

:: Bekleme sayaci (5sn sonra kapanir ya da tusa basinca)
echo This window will close in 10 seconds...
echo (Press any key to close immediately)
echo.
timeout /t 10 /nobreak >nul 2>&1
exit /b 0

@echo off
title YouTube Analiz Pro - Kisayol Olusturucu
color 0A

echo.
echo ========================================================
echo   YOUTUBE ANALIZ PRO - KISAYOL OLUSTURULUYOR
echo ========================================================
echo.
echo 3 farkli yontemle kisayol olusturulacak:
echo.
echo 1. VBS Launcher (Gorunmez pencere)
echo 2. BAT Launcher (Minimize pencere)  
echo 3. PowerShell Launcher (En guvenilir)
echo.
echo ========================================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [UYARI] Python bulunamadi!
        echo          Lutfen Python yukleyin: https://python.org/downloads
        echo.
        pause
        exit /b
    ) else (
        echo [OK] Python bulundu (py komutu)
    )
) else (
    echo [OK] Python bulundu
)
echo.

REM 1. VBS Kisayolu
echo [1/3] VBS kisayolu olusturuluyor...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analiz Pro (VBS).lnk'); $Shortcut.TargetPath = '%~dp0YouTube Analiz Pro.vbs'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analiz Pro - VBS Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [BASARILI] VBS kisayolu olusturuldu
) else (
    echo       [HATA] VBS kisayolu olusturulamadi
)

REM 2. BAT Kisayolu
echo [2/3] BAT kisayolu olusturuluyor...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analiz Pro (BAT).lnk'); $Shortcut.TargetPath = '%~dp0BASLAT.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analiz Pro - BAT Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [BASARILI] BAT kisayolu olusturuldu
) else (
    echo       [HATA] BAT kisayolu olusturulamadi
)

REM 3. PowerShell Kisayolu
echo [3/3] PowerShell kisayolu olusturuluyor...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analiz Pro (PS).lnk'); $Shortcut.TargetPath = 'powershell.exe'; $Shortcut.Arguments = '-ExecutionPolicy Bypass -WindowStyle Hidden -File \"%~dp0Start-YouTubeAnalyzer.ps1\"'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analiz Pro - PowerShell Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [BASARILI] PowerShell kisayolu olusturuldu
) else (
    echo       [HATA] PowerShell kisayolu olusturulamadi
)

echo.
echo ========================================================
echo   TAMAMLANDI!
echo ========================================================
echo.
echo Masaustunde 3 kisayol olusturuldu:
echo.
echo 1. "YouTube Analiz Pro (VBS)" - Gorunmez pencere
echo 2. "YouTube Analiz Pro (BAT)" - Minimize pencere
echo 3. "YouTube Analiz Pro (PS)"  - PowerShell (en guvenilir)
echo.
echo ONERILEN: PowerShell (PS) versiyonunu deneyin!
echo.
echo Hangisi calismiyorsa digerleri calisir.
echo.
echo ========================================================
pause

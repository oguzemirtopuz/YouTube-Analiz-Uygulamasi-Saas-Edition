@echo off
title YouTube Analyse Pro - Shortcut Creator
color 0A

echo.
echo ========================================================
echo   YOUTUBE ANALYZE PRO - CREATING SHORTCUTS
echo ========================================================
echo.
echo Shortcuts will be created using 3 different methods:
echo.
echo 1. VBS Launcher (Invisible window)
2. BAT Launcher (Minimized window)  
3. PowerShell Launcher (Most reliable)
echo.
echo ========================================================
echo.

REM Python check
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Python not found!
        echo          Please install Python: https://python.org/downloads
        echo.
        pause
        exit /b
    ) else (
        echo [OK] Python found (py command)
    )
) else (
    echo [OK] Python found
)
echo.

REM 1. VBS Shortcut
echo [1/3] Creating VBS shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analyse Pro (VBS).lnk'); $Shortcut.TargetPath = '%~dp0YouTube Analiz Pro.vbs'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analyse Pro - VBS Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [SUCCESS] VBS shortcut created
) else (
    echo       [ERROR] Failed to create VBS shortcut
)

REM 2. BAT Shortcut
echo [2/3] Creating BAT shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analyse Pro (BAT).lnk'); $Shortcut.TargetPath = '%~dp0BASLAT.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analyse Pro - BAT Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [SUCCESS] BAT shortcut created
) else (
    echo       [ERROR] Failed to create BAT shortcut
)

REM 3. PowerShell Shortcut
echo [3/3] Creating PowerShell shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\YouTube Analyse Pro (PS).lnk'); $Shortcut.TargetPath = 'powershell.exe'; $Shortcut.Arguments = '-ExecutionPolicy Bypass -WindowStyle Hidden -File \"%~dp0Start-YouTubeAnalyzer.ps1\"'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,165'; $Shortcut.Description = 'YouTube Analyse Pro - PowerShell Launcher'; $Shortcut.Save()" 2>nul

if %errorlevel% == 0 (
    echo       [SUCCESS] PowerShell shortcut created
) else (
    echo       [ERROR] Failed to create PowerShell shortcut
)

echo.
echo ========================================================
echo   COMPLETED!
echo ========================================================
echo.
echo 3 shortcuts have been created on the desktop:
echo.
echo 1. "YouTube Analyse Pro (VBS)" - Invisible window
echo 2. "YouTube Analyse Pro (BAT)" - Minimized window
echo 3. "YouTube Analyse Pro (PS)"  - PowerShell (most reliable)
echo.
echo RECOMMENDED: Try the PowerShell (PS) version!
echo.
echo If one does not work, the others will.
echo.
echo ========================================================
pause

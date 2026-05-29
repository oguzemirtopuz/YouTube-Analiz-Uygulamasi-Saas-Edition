$desktop = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "YouTube Analyzer Pro.lnk"
$workingDir = $PSScriptRoot
$targetPath = Join-Path $workingDir "YouTube Analiz Pro.vbs"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$targetPath`""
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll,165"
$Shortcut.Description = "YouTube Analyzer Pro - Start Without Terminal"
$Shortcut.Save()

Write-Host "Shortcut successfully created on desktop: $shortcutPath"

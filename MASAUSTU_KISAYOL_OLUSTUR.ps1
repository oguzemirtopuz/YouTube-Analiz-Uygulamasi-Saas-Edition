$desktop = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "YouTube Analiz Pro.lnk"
$targetPath = "c:\Users\Oğuz\Desktop\Projeler\Yt_Analiz\YT_AnalizPro\YouTube Analiz Pro.vbs"
$workingDir = "c:\Users\Oğuz\Desktop\Projeler\Yt_Analiz\YT_AnalizPro"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$targetPath`""
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll,165"
$Shortcut.Description = "YouTube Analiz Pro - Terminalsiz Başlat"
$Shortcut.Save()

Write-Host "Kısayol masaüstüne başarıyla oluşturuldu: $shortcutPath"

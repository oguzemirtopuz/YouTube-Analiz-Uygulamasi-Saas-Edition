# YouTube Analiz Pro Launcher
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverPath = Join-Path $scriptPath "server.pyw"

# Python komutunu bul
$pythonCmd = $null
$pythonCommands = @("python", "py", "python3")

foreach ($cmd in $pythonCommands) {
    try {
        $null = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {
        continue
    }
}

if ($null -eq $pythonCmd) {
    [System.Windows.Forms.MessageBox]::Show(
        "Python bulunamadı!`n`nLütfen Python yükleyin: https://python.org/downloads",
        "YouTube Analiz Pro",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

# Server.py kontrolü
if (-not (Test-Path $serverPath)) {
    [System.Windows.Forms.MessageBox]::Show(
        "server.py bulunamadı!`n`nDosya yolu: $serverPath",
        "YouTube Analiz Pro",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

# Uygulamayı başlat (görünmez)
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonCmd
$psi.Arguments = "`"$serverPath`""
$psi.WorkingDirectory = $scriptPath
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.CreateNoWindow = $true

[System.Diagnostics.Process]::Start($psi) | Out-Null

# YouTube Analyzer Pro Launcher
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverPath = Join-Path $scriptPath "server.pyw"

# Find Python command
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
        "Python not found!`n`nPlease install Python: https://python.org/downloads",
        "YouTube Analyzer Pro",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

# Check server.py
if (-not (Test-Path $serverPath)) {
    [System.Windows.Forms.MessageBox]::Show(
        "server.py not found!`n`nFile path: $serverPath",
        "YouTube Analyzer Pro",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

# Start application (invisible)
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonCmd
$psi.Arguments = "`"$serverPath`""
$psi.WorkingDirectory = $scriptPath
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.CreateNoWindow = $true

[System.Diagnostics.Process]::Start($psi) | Out-Null

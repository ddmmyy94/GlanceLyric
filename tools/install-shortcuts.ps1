param([switch]$Remove)

# Shortcut installer for GlanceLyric. Called by Install.bat / Uninstall.bat.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonw = Join-Path $root '.venv\Scripts\pythonw.exe'
$entry = Join-Path $root 'glancelyric.pyw'
$icon = Join-Path $root 'assets\glancelyric.ico'
$exe = Join-Path $root 'GlanceLyric.exe'
if (-not (Test-Path -LiteralPath $exe)) {
    $exe = Join-Path $root 'dist\GlanceLyric\GlanceLyric.exe'
}
$links = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'GlanceLyric.lnk'),
    (Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\GlanceLyric.lnk')
)

if ($Remove) {
    foreach ($link in $links) {
        if (Test-Path -LiteralPath $link) {
            Remove-Item -LiteralPath $link -Force
            Write-Host "  dihapus: $link"
        }
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $exe) -and -not (Test-Path -LiteralPath $pythonw)) {
    throw "pythonw.exe tidak ditemukan di $pythonw - jalankan Install.bat lebih dulu."
}

$shell = New-Object -ComObject WScript.Shell
foreach ($link in $links) {
    $shortcut = $shell.CreateShortcut($link)
    if (Test-Path -LiteralPath $exe) {
        $shortcut.TargetPath = $exe
        $shortcut.Arguments = ''
        $shortcut.IconLocation = "$exe,0"
    } else {
        $shortcut.TargetPath = $pythonw
        $shortcut.Arguments = "`"$entry`""
    }
    $shortcut.WorkingDirectory = $root
    $shortcut.Description = 'GlanceLyric v1.0 - lirik Spotify di taskbar'
    if (Test-Path -LiteralPath $icon) {
        $shortcut.IconLocation = "$icon,0"
    }
    $shortcut.Save()
    Write-Host "  dibuat: $link"
}

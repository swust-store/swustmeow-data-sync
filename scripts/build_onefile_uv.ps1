param(
  [string]$Icon = '',
  [string]$UPXDir = ''
)

$ErrorActionPreference = 'Stop'
function Info($m){ Write-Host "[build] $m" -ForegroundColor Cyan }

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $RepoRoot

Info "Using uv to run PyInstaller"

$entry = Join-Path $RepoRoot 'src\main.py'
$hook = Join-Path $RepoRoot 'scripts\runtime_hook_playwright.py'
$addData = @(
  "src\\tasks\\js;tasks/js"
)

$iconArg = ''
if ($Icon -ne '') { $iconArg = "--icon `"$Icon`"" }

# Ensure Playwright will NOT try to download browsers at runtime
$env:PLAYWRIGHT_BROWSERS_PATH = '0'
$env:PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = '1'

$cmd = @(
  'uv','run','--with','pyinstaller','--with','pyinstaller-hooks-contrib',
  'pyinstaller','--noconfirm','--onefile','--name','swustmeow-data-sync',
  '--icon','assets\icon.ico',
  '--runtime-hook', $hook,
  '--hidden-import','tkinter',
  '--hidden-import','playwright._impl._driver',
  '--console'
)

$upxDirToUse = ''
if ($UPXDir -ne '') {
  if (-not (Test-Path $UPXDir)) { throw "UPXDir not found: $UPXDir" }
  $upxDirToUse = (Resolve-Path $UPXDir)
} else {
  $upxCmd = Get-Command upx -ErrorAction SilentlyContinue
  if ($upxCmd) { $upxDirToUse = Split-Path -Parent $upxCmd.Source }
}

if ($upxDirToUse -ne '') {
  Info ("Using UPX from: $upxDirToUse")
  $cmd += @('--upx-dir', $upxDirToUse)
} else {
  Info "UPX not found. Building without UPX compression."
}

foreach ($d in $addData) { $cmd += @('--add-data', $d) }
if ($iconArg -ne '') { $cmd += $iconArg }
$cmd += $entry

Info ("Command: " + ($cmd -join ' '))

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  throw "uv not found on PATH. Please install uv and retry."
}

if ($cmd.Count -gt 1) {
  & $cmd[0] @($cmd[1..($cmd.Count-1)])
} else {
  & $cmd[0]
}

Info "Done. Output: dist/swustmeow-data-sync.exe"

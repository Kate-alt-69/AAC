[CmdletBinding()]
param(
    [ValidateSet('app', 'installers', 'all')]
    [string]$Target = 'all',
    [ValidateSet('exe', 'msi', 'all')]
    [string]$InstallerFormat = 'all',
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Backend = Join-Path $Root 'build_backend.py'
$PythonExe = $env:APEX_PYTHON
if (-not $PythonExe) {
    $PythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if (-not $PythonCommand) { $PythonCommand = Get-Command 'python' -ErrorAction SilentlyContinue }
    if ($PythonCommand) { $PythonExe = $PythonCommand.Source }
}
if (-not $PythonExe) { throw 'Python 3 was not found. Install Python and add it to PATH.' }

$BackendArgs = @($Backend, '--platform', 'windows', '--target', $Target, '--installer-format', $InstallerFormat)
if ($Clean) { $BackendArgs += '--clean' }
Push-Location $Root
try {
    & $PythonExe @BackendArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

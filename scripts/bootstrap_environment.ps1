[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SetupArgs
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Refresh-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Find-Python {
    $projectPython = Join-Path $root "backend\.venv\Scripts\python.exe"
    if (Test-Python311 -Executable $projectPython -Arguments @()) { return @($projectPython) }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $launcher -and (Test-Python311 -Executable $launcher.Source -Arguments @("-3.11"))) {
        return @($launcher.Source, "-3.11")
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $python -and (Test-Python311 -Executable $python.Source -Arguments @())) {
        return @($python.Source)
    }
    $userPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
    if (Test-Python311 -Executable $userPython -Arguments @()) { return @($userPython) }
    return @()
}

function Test-Python311 {
    param([string]$Executable, [string[]]$Arguments)
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { return $false }
    & $Executable @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
    return $LASTEXITCODE -eq 0
}

function Ensure-WinGet {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($null -ne $winget) { return $winget.Source }
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe -ErrorAction Stop
    } catch {
        # Registration is only available on newer Windows builds; the guidance below covers older systems.
    }
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw "WinGet is unavailable. Install Microsoft App Installer from https://aka.ms/getwinget, then run setup_env.cmd again."
    }
    return $winget.Source
}

function Install-WinGetPackage {
    param([string]$Winget, [string]$Id, [string]$Label)
    Write-Host "[bootstrap] Installing $Label..." -ForegroundColor Cyan
    & $Winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "WinGet failed to install $Label (exit code $LASTEXITCODE)." }
    Refresh-ProcessPath
}

function Resolve-Region {
    $override = $env:DOCUMENT_REVIEW_REGION
    for ($index = 0; $index -lt $SetupArgs.Count; $index++) {
        if ($SetupArgs[$index] -eq "--region" -and $index + 1 -lt $SetupArgs.Count) {
            $override = $SetupArgs[$index + 1]
        } elseif ($SetupArgs[$index] -like "--region=*") {
            $override = $SetupArgs[$index].Split("=", 2)[1]
        }
    }
    if ($override -match "^(cn|china)$") { return "cn" }
    if ($override -match "^(global|intl|international)$") { return "global" }
    $region = [Globalization.RegionInfo]::CurrentRegion.TwoLetterISORegionName
    $culture = [Globalization.CultureInfo]::CurrentUICulture.Name
    $timeZone = [TimeZoneInfo]::Local.Id
    if ($region -eq "CN" -or $culture -eq "zh-CN" -or $timeZone -eq "China Standard Time") { return "cn" }
    return "global"
}

$pythonArgs = @()
for ($index = 0; $index -lt $SetupArgs.Count; $index++) {
    if ($SetupArgs[$index] -eq "--region") { $index++; continue }
    if ($SetupArgs[$index] -like "--region=*") { continue }
    $pythonArgs += $SetupArgs[$index]
}

$region = Resolve-Region
if ($region -eq "cn") {
    $env:DOCUMENT_REVIEW_PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
    $env:DOCUMENT_REVIEW_NPM_REGISTRY = "https://registry.npmmirror.com"
    Write-Host "[region] China detected: using Tsinghua PyPI and npmmirror for this installation." -ForegroundColor Green
} else {
    $env:DOCUMENT_REVIEW_PIP_INDEX_URL = "https://pypi.org/simple"
    $env:DOCUMENT_REVIEW_NPM_REGISTRY = "https://registry.npmjs.org"
    Write-Host "[region] Global region detected: using official package registries." -ForegroundColor Green
}

$checkOnly = $pythonArgs -contains "--check-only"
$pythonCommand = @(Find-Python)
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue

if (-not $checkOnly -and ($pythonCommand.Count -eq 0 -or $null -eq $nodeCommand -or $null -eq $npmCommand)) {
    $winget = Ensure-WinGet
    if ($pythonCommand.Count -eq 0) {
        Install-WinGetPackage -Winget $winget -Id "Python.Python.3.11" -Label "Python 3.11"
    }
    if ($null -eq $nodeCommand -or $null -eq $npmCommand) {
        Install-WinGetPackage -Winget $winget -Id "OpenJS.NodeJS.LTS" -Label "Node.js LTS"
    }
    $pythonCommand = @(Find-Python)
}

if ($pythonCommand.Count -eq 0) { throw "Python 3.11+ was not found after bootstrap." }
Refresh-ProcessPath
if ($null -eq (Get-Command node.exe -ErrorAction SilentlyContinue) -or $null -eq (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm was not found after bootstrap. Restart Windows and run setup_env.cmd again."
}

$pythonExecutable = $pythonCommand[0]
$launcherArgs = @()
if ($pythonCommand.Count -gt 1) { $launcherArgs += $pythonCommand[1..($pythonCommand.Count - 1)] }
$launcherArgs += (Join-Path $PSScriptRoot "setup_environment.py")
$launcherArgs += $pythonArgs

& $pythonExecutable @launcherArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

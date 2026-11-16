<#
.SYNOPSIS
    Automated Reproducible Release Build Script for Findora.
.DESCRIPTION
    1. Validates test suites (120 Python tests + 12 .NET tests).
    2. Builds the standalone Python backend via PyInstaller into dist/Findora/backend/.
    3. Publishes the self-contained C# .NET 8 WPF frontend into dist/Findora/.
    4. Compiles the Inno Setup Windows installer (dist/Findora-Setup-v1.0.0.exe).
    5. Creates a standalone portable ZIP package (dist/Findora-v1.0.0-windows-x64.zip).
    6. Computes SHA-256 checksums (dist/SHA256SUMS.txt).
#>

[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Findora Windows Release Packager     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 0. Ensure Tools are on PATH
$LocalDotnet = Join-Path $env:LOCALAPPDATA "Microsoft\dotnet"
if (Test-Path (Join-Path $LocalDotnet "dotnet.exe")) {
    $env:PATH = "$LocalDotnet;$env:PATH"
}

# Locate Inno Setup ISCC.exe
$IsccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$IsccExe = $null
foreach ($cand in $IsccCandidates) {
    if (Test-Path $cand) {
        $IsccExe = $cand
        break
    }
}

# 1. Quality Gate (Unit & Integration Tests)
if (-not $SkipTests) {
    Write-Host "`n[1/6] Running quality gate test suites..." -ForegroundColor Yellow
    
    Write-Host "  -> Running Python test suite (120 tests)..." -ForegroundColor DarkGray
    python -m pytest tests/python -q --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python test suite failed. Aborting release build."
    }

    Write-Host "  -> Running .NET test suite (12 tests)..." -ForegroundColor DarkGray
    dotnet test Findora.sln -c Release --verbosity quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error ".NET test suite failed. Aborting release build."
    }
    Write-Host "  Quality gate passed: All 132 tests succeeded!" -ForegroundColor Green
} else {
    Write-Host "`n[1/6] Skipping test suites (-SkipTests specified)." -ForegroundColor DarkGray
}

# 2. Prepare Distribution Directories
Write-Host "`n[2/6] Preparing distribution directories..." -ForegroundColor Yellow
$DistDir = Join-Path $RootDir "dist\Findora"
$BackendDistDir = Join-Path $DistDir "backend"
$PyDist = Join-Path $RootDir "build\py_dist"
$PyWork = Join-Path $RootDir "build\py_work"

# Stop any running instances to unlock binaries
Get-Process -Name "Findora", "FindoraBackend" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

if (Test-Path $DistDir) {
    Remove-Item -Recurse -Force $DistDir
}
New-Item -ItemType Directory -Force -Path $BackendDistDir | Out-Null

# 3. Build Standalone Python Backend
Write-Host "`n[3/6] Packaging Python backend with PyInstaller..." -ForegroundColor Yellow
$MainPy = Join-Path $RootDir "src\Findora.Backend\main.py"
$BackendDir = Join-Path $RootDir "src\Findora.Backend"
$BuildDir = Join-Path $RootDir "build"

python -m PyInstaller --clean -y `
    --name FindoraBackend `
    --distpath $PyDist `
    --workpath $PyWork `
    --specpath $BuildDir `
    --paths $BackendDir `
    --hidden-import ipc_server `
    --hidden-import tree `
    --hidden-import storage `
    --hidden-import scanner `
    --hidden-import watcher `
    --hidden-import reconciler `
    --hidden-import queue_manager `
    --hidden-import icon_provider `
    $MainPy

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller backend build failed."
}

Write-Host "  -> Assembling backend files into $BackendDistDir..." -ForegroundColor DarkGray
Copy-Item -Recurse -Force "$PyDist\FindoraBackend\*" $BackendDistDir

# 4. Build & Publish C# WPF Frontend (Self-Contained)
Write-Host "`n[4/6] Publishing Findora WPF frontend (Self-Contained win-x64)..." -ForegroundColor Yellow
$WpfProject = Join-Path $RootDir "src\Findora.Wpf\Findora.Wpf.csproj"

dotnet publish $WpfProject `
    -c Release `
    -r win-x64 `
    --self-contained true `
    -p:PublishSingleFile=true `
    -o $DistDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet publish failed."
}

# 5. Verification of Binaries
$MainExe = Join-Path $DistDir "Findora.exe"
$BackendExe = Join-Path $BackendDistDir "FindoraBackend.exe"

if (-not ((Test-Path $MainExe) -and (Test-Path $BackendExe))) {
    Write-Error "Required output executables are missing!"
}
Write-Host "  -> Findora frontend and backend verified." -ForegroundColor Green

# 6. Packaging: Inno Setup Installer & Portable Zip
Write-Host "`n[5/6] Building installer and portable distribution packages..." -ForegroundColor Yellow
$DistRoot = Join-Path $RootDir "dist"
$ZipPackage = Join-Path $DistRoot "Findora-v1.0.0-windows-x64.zip"

if (Test-Path $ZipPackage) {
    Remove-Item -Force $ZipPackage
}
Write-Host "  -> Creating portable ZIP archive: $ZipPackage..." -ForegroundColor DarkGray
Compress-Archive -Path "$DistDir\*" -DestinationPath $ZipPackage -Force

if (-not $SkipInstaller) {
    if ($IsccExe) {
        Write-Host "  -> Compiling Inno Setup Windows installer with $IsccExe..." -ForegroundColor DarkGray
        $IssPath = Join-Path $RootDir "build\installer.iss"
        & $IsccExe /Q $IssPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Inno Setup compilation failed."
        }
        Write-Host "  -> Installer generated successfully." -ForegroundColor Green
    } else {
        Write-Warning "Inno Setup (ISCC.exe) not found. Skipping installer generation."
    }
}

# 7. Checksums
Write-Host "`n[6/6] Generating SHA-256 checksums..." -ForegroundColor Yellow
$ChecksumFile = Join-Path $DistRoot "SHA256SUMS.txt"
$Artifacts = @()

$InstallerExe = Join-Path $DistRoot "Findora-Setup-v1.0.0.exe"
if (Test-Path $InstallerExe) { $Artifacts += $InstallerExe }
if (Test-Path $ZipPackage) { $Artifacts += $ZipPackage }

$HashLines = @()
foreach ($art in $Artifacts) {
    $hash = (Get-FileHash -Path $art -Algorithm SHA256).Hash.ToLower()
    $name = Split-Path -Leaf $art
    $HashLines += "$hash  $name"
    Write-Host "  $hash  $name" -ForegroundColor Cyan
}
$HashLines | Set-Content -Path $ChecksumFile -Encoding utf8

# Clean root FindoraBackend.spec if present
$StraySpec = Join-Path $RootDir "FindoraBackend.spec"
if (Test-Path $StraySpec) { Remove-Item -Force $StraySpec }

Write-Host "`n========================================" -ForegroundColor Green
Write-Host " Findora Release Build Complete!       " -ForegroundColor Green
Write-Host " Artifacts written to: $DistRoot       " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

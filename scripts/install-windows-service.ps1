# PowerShell script to install Ollama Shim as a Windows Service using NSSM
# Requires: NSSM (https://nssm.cc/download)
#
# Run as Administrator:
# PowerShell -ExecutionPolicy Bypass -File install-windows-service.ps1

param(
    [string]$InstallPath = "C:\Program Files\ollama-shim",
    [switch]$Uninstall
)

$ServiceName = "OllamaShim"
$DisplayName = "Ollama Shim"
$Description = "LM Studio to Ollama API Bridge Service"

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

# Check if NSSM is available
$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if (-not $nssm) {
    Write-Error "NSSM not found. Please install from https://nssm.cc/download"
    Write-Host "Or use: choco install nssm (with Chocolatey)"
    exit 1
}

if ($Uninstall) {
    Write-Host "Uninstalling $ServiceName service..."
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
    Write-Host "Service uninstalled successfully"
    exit 0
}

# Get paths
$PythonExe = Join-Path $InstallPath ".venv\Scripts\python.exe"
$UvicornPath = Join-Path $InstallPath ".venv\Scripts\uvicorn.exe"
$WorkingDir = $InstallPath
$EnvFile = Join-Path $InstallPath ".env"

# Verify paths exist
if (-not (Test-Path $InstallPath)) {
    Write-Error "Installation path does not exist: $InstallPath"
    exit 1
}

if (-not (Test-Path $UvicornPath)) {
    Write-Warning "Uvicorn not found at $UvicornPath"
    Write-Host "Attempting to use python -m uvicorn instead..."
    $AppCommand = "$PythonExe -m uvicorn"
} else {
    $AppCommand = $UvicornPath
}

# Load SHIM_PORT from .env
$ShimPort = 11434
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile
    foreach ($line in $envContent) {
        if ($line -match "^\s*SHIM_PORT\s*=\s*(\d+)") {
            $ShimPort = $matches[1]
            break
        }
    }
}

Write-Host "Installing $ServiceName as a Windows Service..."
Write-Host "  Installation Path: $InstallPath"
Write-Host "  Port: $ShimPort"

# Remove existing service if it exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Stopping and removing existing service..."
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
}

# Install service
nssm install $ServiceName $UvicornPath "src.main:app" "--host" "0.0.0.0" "--port" $ShimPort
nssm set $ServiceName DisplayName $DisplayName
nssm set $ServiceName Description $Description
nssm set $ServiceName AppDirectory $WorkingDir

# Load environment variables from .env file
nssm set $ServiceName AppEnvironmentExtra $(Get-Content $EnvFile | Where-Object { $_ -notmatch "^\s*#" -and $_ -match "=" } | ForEach-Object { $_.Trim() })

# Configure service restart behavior
nssm set $ServiceName AppStdout "$WorkingDir\logs\service.log"
nssm set $ServiceName AppStderr "$WorkingDir\logs\service-error.log"
nssm set $ServiceName AppRotateFiles 1
nssm set $ServiceName AppRotateBytes 1048576  # 1MB

# Set service to start automatically
nssm set $ServiceName Start SERVICE_AUTO_START

Write-Host ""
Write-Host "Service installed successfully!"
Write-Host ""
Write-Host "To start the service:"
Write-Host "  nssm start $ServiceName"
Write-Host "  OR: net start $ServiceName"
Write-Host ""
Write-Host "To stop the service:"
Write-Host "  nssm stop $ServiceName"
Write-Host "  OR: net stop $ServiceName"
Write-Host ""
Write-Host "To view service status:"
Write-Host "  nssm status $ServiceName"
Write-Host ""
Write-Host "To uninstall:"
Write-Host "  PowerShell -ExecutionPolicy Bypass -File install-windows-service.ps1 -Uninstall"
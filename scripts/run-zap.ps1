param (
    [Parameter(Mandatory = $true)]
    [string]$TargetUrl
)

# -------------------------
# ZAP Location
# -------------------------
$zapDir = "C:\Program Files\ZAP\Zed Attack Proxy"
$zapBat = Join-Path $zapDir "zap.bat"

if (-not (Test-Path $zapBat)) {
    Write-Host "[ERROR] OWASP ZAP not found at $zapBat"
    exit 1
}

# -------------------------
# Log Directory (SAFE PATH BUILDING)
# -------------------------
$baseDir = "C:\Users\cisco\Documents\Niru-Predictpath-AI"
$toolsDir = Join-Path $baseDir "NiRu-predictpath-tools"
$reportDir = Join-Path $toolsDir "scripts\saved-logs"

if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $reportDir "zap_report_$timestamp.json"

# -------------------------
# Dynamic Port Selection
# -------------------------
# Prevent "Address already in use" errors by finding a random free port
function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = $listener.LocalEndpoint.Port
    $listener.Stop()
    return $port
}

$ZapPort = Get-FreePort
Write-Host "[*] Selected dynamic port for ZAP: $ZapPort"

# -------------------------
# Execute Scan
# -------------------------
Write-Host "Starting ZAP Scan on $TargetUrl..."
Write-Host "Report will be saved to:"
Write-Host "  $reportPath"
Write-Host ""

Push-Location $zapDir
try {
    & $zapBat `
        -port $ZapPort `
        -cmd `
        -quickurl "$TargetUrl" `
        -quickprogress `
        -quickout "$reportPath"
}
finally {
    Pop-Location
}

# -------------------------
# Validation
# -------------------------
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $reportPath)) {
    Write-Host ""
    Write-Host "[!] ZAP Scan FAILED"
    Write-Host "Exit Code:"
    Write-Host $LASTEXITCODE
    if (-not (Test-Path $reportPath)) {
        Write-Host "Report file was not created."
    }
    exit 1
}

Write-Host ""
Write-Host "[+] ZAP Scan completed successfully"
Write-Host "Report saved to:"
Write-Host $reportPath


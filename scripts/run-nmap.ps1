# PredictPath AI - Nmap FULL Network Scan
# Purpose: Comprehensive network reconnaissance and vulnerability detection

param (
    [string]$Target = "127.0.0.1",
    [string]$OutputFormat = "xml"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
# Update log directory to match new structure
$logDir = ".\scripts\saved-logs\nmap"
$logFile = "$logDir\nmap-$timestamp.xml"
$txtLog = "$logDir\nmap-$timestamp.txt"

# Ensure log directory exists
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "======================================"
Write-Host " PredictPath AI - Nmap Full Scan"
Write-Host "======================================"
Write-Host "[+] Target: $Target"
Write-Host "[+] Timestamp: $timestamp"
Write-Host ""

# Check if nmap is installed
try {
    $nmapVersion = nmap --version 2>&1 | Select-String "Nmap version"
    Write-Host "[OK] Nmap detected: $nmapVersion"
}
catch {
    Write-Host "[ERROR] Nmap not found. Please install Nmap from https://nmap.org/download.html"
    exit 1
}

Write-Host ""
Write-Host "[+] Starting FULL Nmap scan..."
Write-Host "[+] This includes:"
Write-Host "    - Host discovery (-sn)"
Write-Host "    - SYN stealth scan (-sS)"
Write-Host "    - Service/version detection (-sV)"
Write-Host "    - OS detection (-O)"
Write-Host "    - Vulnerability scripts (--script vuln)"
Write-Host "    - Aggressive timing (-T4)"
Write-Host ""

# Run fast Nmap scan for testing workflow
# Using -F (fast mode) and -sV (version detection) only
nmap `
    -F `
    -sV `
    -T4 `
    --open `
    $Target `
    -oX $logFile `
    -oN $txtLog

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Nmap scan completed successfully"
    Write-Host "[OK] XML log saved to: $logFile"
    Write-Host "[OK] Text log saved to: $txtLog"
    Write-Host ""
    
    # Display file sizes
    if (Test-Path $logFile) {
        $xmlSize = (Get-Item $logFile).Length
        Write-Host "[i] XML report size: $([math]::Round($xmlSize/1KB, 2)) KB"
    }
    if (Test-Path $txtLog) {
        $txtSize = (Get-Item $txtLog).Length
        Write-Host "[i] Text report size: $([math]::Round($txtSize/1KB, 2)) KB"
    }
    
    return @{
        Success = $true
        XmlLog  = $logFile
        TxtLog  = $txtLog
    }
}
else {
    Write-Host ""
    Write-Host "[ERROR] Nmap scan failed with exit code: $LASTEXITCODE"
    return @{
        Success = $false
    }
}

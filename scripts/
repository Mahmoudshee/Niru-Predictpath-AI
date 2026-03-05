# PredictPath AI - Nuclei Vulnerability Scanner
# Purpose: Template-based vulnerability detection with CVE coverage

param (
    [string]$Target = "http://192.168.1.1",
    [string]$Severity = "critical,high,medium,low",
    [switch]$UpdateTemplates
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = ".\logs\nuclei"
$logFile = "$logDir\nuclei-$timestamp.json"
$txtLog = "$logDir\nuclei-$timestamp.txt"

# Ensure log directory exists
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "======================================"
Write-Host " PredictPath AI — Nuclei Scan"
Write-Host "======================================"
Write-Host "[+] Target: $Target"
Write-Host "[+] Severity: $Severity"
Write-Host "[+] Timestamp: $timestamp"
Write-Host ""

# Check if Nuclei is installed
try {
    $nucleiVersion = nuclei -version 2>&1 | Select-String "Nuclei"
    Write-Host "[✓] Nuclei detected: $nucleiVersion"
} catch {
    Write-Host "[i] Nuclei not found locally, using Docker..."
    $useDocker = $true
}

# Update templates if requested
if ($UpdateTemplates) {
    Write-Host "[+] Updating Nuclei templates..."
    if ($useDocker) {
        docker run --rm projectdiscovery/nuclei -update-templates
    } else {
        nuclei -update-templates
    }
    Write-Host "[✓] Templates updated"
    Write-Host ""
}

Write-Host "[+] Starting Nuclei vulnerability scan..."
Write-Host "[+] This includes:"
Write-Host "    • CVE-based vulnerability detection"
Write-Host "    • Misconfigurations"
Write-Host "    • Exposed panels and services"
Write-Host "    • Security headers analysis"
Write-Host "    • Technology detection"
Write-Host ""

# Build Nuclei command
if ($useDocker) {
    # Run via Docker
    docker run --rm `
        -v "${PWD}/logs/nuclei:/output" `
        projectdiscovery/nuclei `
        -u $Target `
        -severity $Severity `
        -json `
        -o /output/nuclei-output.json `
        -stats `
        -silent
    
    # Also get text output
    docker run --rm `
        -v "${PWD}/logs/nuclei:/output" `
        projectdiscovery/nuclei `
        -u $Target `
        -severity $Severity `
        -o /output/nuclei-output.txt `
        -stats
    
    # Rename files
    if (Test-Path "$logDir\nuclei-output.json") {
        Move-Item "$logDir\nuclei-output.json" $logFile -Force
    }
    if (Test-Path "$logDir\nuclei-output.txt") {
        Move-Item "$logDir\nuclei-output.txt" $txtLog -Force
    }
} else {
    # Run locally
    nuclei `
        -u $Target `
        -severity $Severity `
        -json `
        -o $logFile `
        -stats
    
    nuclei `
        -u $Target `
        -severity $Severity `
        -o $txtLog `
        -stats
}

if (Test-Path $logFile) {
    Write-Host ""
    Write-Host "[✓] Nuclei scan completed successfully"
    Write-Host "[✓] JSON log saved to: $logFile"
    Write-Host "[✓] Text log saved to: $txtLog"
    Write-Host ""
    
    # Display file sizes and vulnerability count
    $jsonSize = (Get-Item $logFile).Length
    $txtSize = (Get-Item $txtLog).Length
    Write-Host "[i] JSON report size: $([math]::Round($jsonSize/1KB, 2)) KB"
    Write-Host "[i] Text report size: $([math]::Round($txtSize/1KB, 2)) KB"
    
    # Count vulnerabilities
    $vulnCount = (Get-Content $logFile | ConvertFrom-Json).Count
    Write-Host "[i] Vulnerabilities found: $vulnCount"
    
    return @{
        Success = $true
        JsonLog = $logFile
        TxtLog = $txtLog
        VulnCount = $vulnCount
    }
} else {
    Write-Host ""
    Write-Host "[✗] Nuclei scan failed - no output generated"
    return @{
        Success = $false
    }
}

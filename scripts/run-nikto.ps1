# PredictPath AI - Nikto Web Vulnerability Scanner
# Purpose: Web server and application vulnerability assessment

param (
    [string]$Target = "http://192.168.1.1",
    [int]$Port = 80,
    [switch]$SSL
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = ".\logs\nikto"
$logFile = "$logDir\nikto-$timestamp.xml"
$txtLog = "$logDir\nikto-$timestamp.txt"

# Ensure log directory exists
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "======================================"
Write-Host " PredictPath AI — Nikto Web Scan"
Write-Host "======================================"
Write-Host "[+] Target: $Target"
Write-Host "[+] Port: $Port"
Write-Host "[+] SSL: $($SSL.IsPresent)"
Write-Host "[+] Timestamp: $timestamp"
Write-Host ""

# Check if Nikto is installed (via Docker)
try {
    docker images | Select-String "nikto" | Out-Null
    Write-Host "[✓] Nikto Docker image found"
} catch {
    Write-Host "[i] Pulling Nikto Docker image..."
    docker pull securecodebox/nikto
}

Write-Host ""
Write-Host "[+] Starting Nikto web vulnerability scan..."
Write-Host "[+] This includes:"
Write-Host "    • Server misconfiguration detection"
Write-Host "    • Outdated software identification"
Write-Host "    • Dangerous files/CGI detection"
Write-Host "    • SSL/TLS configuration checks"
Write-Host ""

# Build Nikto command
$niktoArgs = "-h $Target -p $Port -Format xml -output /tmp/nikto-output.xml"
if ($SSL) {
    $niktoArgs += " -ssl"
}

# Run Nikto via Docker
docker run --rm `
    -v "${PWD}/logs/nikto:/tmp" `
    securecodebox/nikto `
    $niktoArgs

# Rename output file
if (Test-Path "$logDir\nikto-output.xml") {
    Move-Item "$logDir\nikto-output.xml" $logFile -Force
}

# Also run with text output
$niktoArgsTxt = "-h $Target -p $Port -Format txt -output /tmp/nikto-output.txt"
if ($SSL) {
    $niktoArgsTxt += " -ssl"
}

docker run --rm `
    -v "${PWD}/logs/nikto:/tmp" `
    securecodebox/nikto `
    $niktoArgsTxt

if (Test-Path "$logDir\nikto-output.txt") {
    Move-Item "$logDir\nikto-output.txt" $txtLog -Force
}

if (Test-Path $logFile) {
    Write-Host ""
    Write-Host "[✓] Nikto scan completed successfully"
    Write-Host "[✓] XML log saved to: $logFile"
    Write-Host "[✓] Text log saved to: $txtLog"
    Write-Host ""
    
    # Display file sizes
    $xmlSize = (Get-Item $logFile).Length
    $txtSize = (Get-Item $txtLog).Length
    Write-Host "[i] XML report size: $([math]::Round($xmlSize/1KB, 2)) KB"
    Write-Host "[i] Text report size: $([math]::Round($txtSize/1KB, 2)) KB"
    
    return @{
        Success = $true
        XmlLog = $logFile
        TxtLog = $txtLog
    }
} else {
    Write-Host ""
    Write-Host "[✗] Nikto scan failed - no output generated"
    return @{
        Success = $false
    }
}

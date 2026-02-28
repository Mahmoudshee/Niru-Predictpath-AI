# PredictPath AI - MASTER Network Security Orchestrator
# Purpose: Coordinate all vulnerability scanning tools in a single workflow

param (
    [string]$Target = "192.168.1.0/24",
    [string]$WebTarget = "",
    [switch]$SkipOpenVAS,
    [switch]$SkipNikto,
    [switch]$SkipNuclei,
    [switch]$QuickScan
)

$startTime = Get-Date
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = ".\logs"
$summaryFile = "$logDir\scan-summary-$timestamp.txt"

# Ensure all log directories exist
@("nmap", "openvas", "nikto", "nuclei") | ForEach-Object {
    $dir = Join-Path $logDir $_
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host ""
Write-Host "=============================================="
Write-Host " PredictPath AI — Network Security Analysis "
Write-Host "=============================================="
Write-Host ""
Write-Host "[i] Scan Configuration:"
Write-Host "    • Network Target: $Target"
if ($WebTarget) {
    Write-Host "    • Web Target: $WebTarget"
}
Write-Host "    • Quick Scan: $($QuickScan.IsPresent)"
Write-Host "    • Skip OpenVAS: $($SkipOpenVAS.IsPresent)"
Write-Host "    • Skip Nikto: $($SkipNikto.IsPresent)"
Write-Host "    • Skip Nuclei: $($SkipNuclei.IsPresent)"
Write-Host "    • Timestamp: $timestamp"
Write-Host ""
Write-Host "=============================================="
Write-Host ""

# Initialize results tracking
$results = @{
    Nmap = @{ Success = $false; Files = @() }
    OpenVAS = @{ Success = $false; Files = @() }
    Nikto = @{ Success = $false; Files = @() }
    Nuclei = @{ Success = $false; Files = @() }
}

# ============================================
# PHASE 1: Network Reconnaissance (Nmap)
# ============================================
Write-Host ""
Write-Host "[1/4] ═══════════════════════════════════════"
Write-Host "[1/4] Running Nmap Network Scan"
Write-Host "[1/4] ═══════════════════════════════════════"
Write-Host ""

try {
    $nmapResult = & .\scripts\run-nmap.ps1 -Target $Target
    $results.Nmap.Success = $nmapResult.Success
    if ($nmapResult.Success) {
        $results.Nmap.Files += $nmapResult.XmlLog
        $results.Nmap.Files += $nmapResult.TxtLog
    }
} catch {
    Write-Host "[✗] Nmap scan failed: $_"
}

# ============================================
# PHASE 2: Vulnerability Assessment (OpenVAS)
# ============================================
if (-not $SkipOpenVAS -and -not $QuickScan) {
    Write-Host ""
    Write-Host "[2/4] ═══════════════════════════════════════"
    Write-Host "[2/4] Running OpenVAS Vulnerability Scan"
    Write-Host "[2/4] ═══════════════════════════════════════"
    Write-Host ""
    
    try {
        $openvasResult = & .\scripts\run-openvas.ps1 -Target $Target
        $results.OpenVAS.Success = $openvasResult.Success
        if ($openvasResult.Success) {
            $results.OpenVAS.Files += $openvasResult.ReportFile
        }
    } catch {
        Write-Host "[✗] OpenVAS scan failed: $_"
    }
} else {
    Write-Host ""
    Write-Host "[2/4] ═══════════════════════════════════════"
    Write-Host "[2/4] OpenVAS Scan SKIPPED"
    Write-Host "[2/4] ═══════════════════════════════════════"
    Write-Host ""
}

# ============================================
# PHASE 3: Web Vulnerability Scan (Nikto)
# ============================================
if (-not $SkipNikto -and $WebTarget) {
    Write-Host ""
    Write-Host "[3/4] ═══════════════════════════════════════"
    Write-Host "[3/4] Running Nikto Web Vulnerability Scan"
    Write-Host "[3/4] ═══════════════════════════════════════"
    Write-Host ""
    
    try {
        $niktoResult = & .\scripts\run-nikto.ps1 -Target $WebTarget
        $results.Nikto.Success = $niktoResult.Success
        if ($niktoResult.Success) {
            $results.Nikto.Files += $niktoResult.XmlLog
            $results.Nikto.Files += $niktoResult.TxtLog
        }
    } catch {
        Write-Host "[✗] Nikto scan failed: $_"
    }
} else {
    Write-Host ""
    Write-Host "[3/4] ═══════════════════════════════════════"
    Write-Host "[3/4] Nikto Scan SKIPPED"
    Write-Host "[3/4] ═══════════════════════════════════════"
    Write-Host ""
}

# ============================================
# PHASE 4: CVE Detection (Nuclei)
# ============================================
if (-not $SkipNuclei -and $WebTarget) {
    Write-Host ""
    Write-Host "[4/4] ═══════════════════════════════════════"
    Write-Host "[4/4] Running Nuclei CVE Detection"
    Write-Host "[4/4] ═══════════════════════════════════════"
    Write-Host ""
    
    try {
        $nucleiResult = & .\scripts\run-nuclei.ps1 -Target $WebTarget
        $results.Nuclei.Success = $nucleiResult.Success
        if ($nucleiResult.Success) {
            $results.Nuclei.Files += $nucleiResult.JsonLog
            $results.Nuclei.Files += $nucleiResult.TxtLog
        }
    } catch {
        Write-Host "[✗] Nuclei scan failed: $_"
    }
} else {
    Write-Host ""
    Write-Host "[4/4] ═══════════════════════════════════════"
    Write-Host "[4/4] Nuclei Scan SKIPPED"
    Write-Host "[4/4] ═══════════════════════════════════════"
    Write-Host ""
}

# ============================================
# FINAL SUMMARY
# ============================================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "=============================================="
Write-Host " Network Security Analysis COMPLETED"
Write-Host "=============================================="
Write-Host ""
Write-Host "[i] Scan Duration: $($duration.ToString('hh\:mm\:ss'))"
Write-Host ""
Write-Host "[i] Results Summary:"
Write-Host ""

$summary = @"
PredictPath AI - Network Security Analysis Summary
Generated: $timestamp
Duration: $($duration.ToString('hh\:mm\:ss'))

═══════════════════════════════════════════════════════

SCAN RESULTS:

"@

foreach ($tool in $results.Keys) {
    $status = if ($results[$tool].Success) { "✓ SUCCESS" } else { "✗ FAILED" }
    $fileCount = $results[$tool].Files.Count
    
    Write-Host "    [$status] $tool - $fileCount file(s) generated"
    
    $summary += "`n[$status] $tool`n"
    
    if ($fileCount -gt 0) {
        foreach ($file in $results[$tool].Files) {
            Write-Host "        → $file"
            $summary += "    → $file`n"
        }
    }
}

Write-Host ""
Write-Host "=============================================="
Write-Host " All logs available in /logs folder"
Write-Host "=============================================="
Write-Host ""

# Save summary
$summary | Out-File -FilePath $summaryFile -Encoding UTF8
Write-Host "[✓] Summary saved to: $summaryFile"
Write-Host ""

return $results

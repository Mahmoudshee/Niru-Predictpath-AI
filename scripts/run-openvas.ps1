# ==========================================
# PredictPath AI - OpenVAS FULL Scan Script
# ==========================================

param (
    [string]$Target = "127.0.0.1",
    [string]$ContainerName = "openvas"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = ".\scripts\saved-logs\openvas"
$reportFile = "$logDir\openvas-$timestamp.xml"

if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "======================================"
Write-Host " PredictPath AI - OpenVAS Full Scan"
Write-Host "======================================"
Write-Host "[+] Target: $Target"
Write-Host "[+] Timestamp: $timestamp"
Write-Host ""

# ------------------------------------------------
# STEP 1: Ensure Docker service is running
# ------------------------------------------------
$dockerService = Get-Service com.docker.service -ErrorAction SilentlyContinue

if ($dockerService.Status -ne "Running") {
    Write-Host "[*] Starting Docker service..."
    Start-Service com.docker.service
    Start-Sleep 10
}

$dockerService = Get-Service com.docker.service
if ($dockerService.Status -ne "Running") {
    Write-Host "[ERROR] Docker service failed to start"
    exit 1
}

Write-Host "[OK] Docker service running"

# ------------------------------------------------
# STEP 2: Verify Docker engine
# ------------------------------------------------
docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker engine not responding"
    exit 1
}

Write-Host "[OK] Docker engine ready"

# ------------------------------------------------
# STEP 3: Verify OpenVAS container exists
# ------------------------------------------------
$containerExists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }

if (-not $containerExists) {
    Write-Host "[ERROR] OpenVAS container '$ContainerName' not found"
    Write-Host "       Create it once manually before using this script."
    exit 1
}

# ------------------------------------------------
# STEP 4: Start container if stopped
# ------------------------------------------------
$running = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }

if (-not $running) {
    Write-Host "[*] Starting OpenVAS container..."
    docker start $ContainerName | Out-Null
    Start-Sleep 10
}

Write-Host "[OK] OpenVAS container running"

# ------------------------------------------------
# STEP 5: Wait for GMP (TCP 9390) Readiness
# ------------------------------------------------
Write-Host "[*] Waiting for OpenVAS GMP service (TCP:9390)..."

$gvmCmd = "docker exec $ContainerName gvm-cli --gmp-username admin --gmp-password admin --host 127.0.0.1 --port 9390"

$retryCount = 0
$maxRetries = 180 # 180 * 15s = 45 minutes wait (VT loading can take ~20-30 mins)

while ($true) {
    # Check if we can get version info via TCP
    Invoke-Expression "$gvmCmd --xml '<get_version/>'" *> $null
    
    if ($LASTEXITCODE -eq 0) { 
        break 
    }
    
    $retryCount++
    if ($retryCount -ge $maxRetries) {
        Write-Host "[ERROR] OpenVAS timed out waiting for readiness (waited 45 mins)"
        exit 1
    }

    $timeLeft = [math]::Round((($maxRetries - $retryCount) * 15) / 60, 1)
    Write-Host "[*] GMP service not ready - waiting 15s... (Timeout in ${timeLeft}m)"
    Start-Sleep 15
}

Write-Host "[OK] OpenVAS fully initialized"

# ------------------------------------------------
# STEP 6: Create target
# ------------------------------------------------
$targetXml = "<create_target><name>Target-$timestamp</name><hosts>$Target</hosts></create_target>"
$targetOut = Invoke-Expression "$gvmCmd --xml ""$targetXml""" 2>&1
$targetId = ($targetOut | Select-String 'id="' | Select-Object -First 1).Matches.Groups[1].Value

if (-not $targetId) {
    Write-Host "[ERROR] Failed to create target"
    exit 1
}

Write-Host "[OK] Target ID: $targetId"

# ------------------------------------------------
# STEP 7: Create scan task
# ------------------------------------------------
$taskXml = "<create_task><name>Task-$timestamp</name><target id='$targetId'/><config id='daba56c8-73ec-11df-a475-002264764cea'/></create_task>"
$taskOut = Invoke-Expression "$gvmCmd --xml ""$taskXml""" 2>&1
$taskId = ($taskOut | Select-String 'id="' | Select-Object -First 1).Matches.Groups[1].Value

if (-not $taskId) {
    Write-Host "[ERROR] Failed to create scan task"
    exit 1
}

Write-Host "[OK] Task ID: $taskId"

# ------------------------------------------------
# STEP 8: Start scan
# ------------------------------------------------
Write-Host "[+] Starting vulnerability scan..."
Invoke-Expression "$gvmCmd --xml ""$taskXml"" <start_task task_id='$taskId'/>" | Out-Null
# The previous line had a bug in concept, use explicit start command string
Invoke-Expression "$gvmCmd --xml ""<start_task task_id='$taskId'/>""" | Out-Null


do {
    Start-Sleep 30
    $statusOut = Invoke-Expression "$gvmCmd --xml ""<get_tasks task_id='$taskId'/>"""
    $status = ($statusOut | Select-String "<status>").Line.Trim()
    # Extract just the status text if wrapped in tags
    if ($status -match "<status>(.+)</status>") {
        $status = $matches[1]
    }
    
    $progress = "0"
    if ($statusOut -match "<progress>(\d+)</progress>") {
         $progress = $matches[1]
    }
    
    Write-Host "[*] Scan running... Status: $status | Progress: $progress%"
} while ($status -ne "Done" -and $status -ne "Stopped" -and $status -ne "Interrupted")

Write-Host "[OK] Scan completed"

# ------------------------------------------------
# STEP 9: Export report
# ------------------------------------------------
$reportIdMatches = $statusOut | Select-String "<report id=""([^""]+)"""
if ($reportIdMatches) {
    $reportId = $reportIdMatches.Matches.Groups[1].Value
    $reportXml = "<get_report report_id='$reportId' format_id='a994b278-1f62-11e1-96ac-406186ea4fc5'/>"
    
    $reportData = Invoke-Expression "$gvmCmd --xml ""$reportXml"""
    $reportData | Out-File -FilePath $reportFile -Encoding UTF8
    
    Write-Host "[OK] Report saved: $reportFile"
} else {
    Write-Host "[WARN] Could not find report ID to export"
}

# ------------------------------------------------
# STEP 10: Shutdown OpenVAS & Docker
# ------------------------------------------------
Write-Host "[*] Stopping OpenVAS container..."
docker stop $ContainerName | Out-Null

Write-Host "[*] Stopping Docker service..."
Stop-Service com.docker.service

Write-Host "======================================"
Write-Host "[SUCCESS] OpenVAS scan complete"
Write-Host "======================================"

<#
.SYNOPSIS
    Orchestrates an on-demand Wazuh Endpoint Scan from Windows PowerShell.
    Follows strict "MASTER ENGINEERING PROMPT" specifications.

.DESCRIPTION
    1. Activates Windows Wazuh Agent.
    2. Activates/Restarts Linux Wazuh Manager (via WSL).
    3. Sets a scan session timestamp.
    4. Forces immediate execution of Syscheck, Rootcheck, Vulnerability, and SCA modules.
    5. Waits 30 seconds for scan completion.
    6. Extracts, filters, and generates a single JSON report containing only new findings.
    7. Saves the report to the local saved-logs directory.

.NOTES
    - Requires WSL (Windows Subsystem for Linux) to be installed and configured with the Wazuh Manager.
    - Requires 'jq' to be installed on the Linux instance.
    - Requires 'wazuh-manager' and 'wazuh-agent' services to be present.
    - HARDCODED PASSWORD "kenty1234" used for WSL sudo operations per user request.
#>

$ErrorActionPreference = "Stop"

# Configuration
$LocalLogPath = "C:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\scripts\saved-logs\wazuh_final_report.json"
$LinuxReportPath = "/opt/predictpath/final_report.json"
$ScanStartFlag = "/opt/predictpath/wazuh_scan_start.txt"
$WslPass = "kenty1234" # Per user request for local dev environment

Write-Host "[*] Starting Endpoint Audit Scan..." -ForegroundColor Cyan

# 1. Agent & Manager Activation
Write-Host "[1/6] Activating Services..."
try {
    # Windows Agent
    $service = Get-Service -Name "WazuhSvc" -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -ne 'Running') {
            Write-Host "    Starting Windows Wazuh Agent..."
            sc.exe start WazuhSvc | Out-Null
        }
        else {
            Write-Host "    Windows Wazuh Agent is running."
        }
    }
    else {
        Write-Warning "    WazuhSvc service not found on this Windows host."
    }

    # Linux Manager (WSL)
    Write-Host "    Initializing Linux Subsystem (WSL)..."
    
    # Step 1: Launch WSL as a persistent background process (like opening it manually)
    # This creates a full session with taskbar icon and complete systemd initialization
    Write-Host "    Launching WSL background session..."
    
    # Start a persistent WSL process that will keep running
    $wslProcess = Start-Process -FilePath "wsl.exe" -ArgumentList "bash", "-c", "sleep 300" -WindowStyle Hidden -PassThru
    
    # Step 2: Give WSL time to fully initialize (systemd, user session, all services)
    Write-Host "    Waiting for full WSL initialization..."
    Start-Sleep -Seconds 5
    
    # Step 3: Verify WSL is responsive
    try {
        $sysInfo = wsl --exec uname -a
        if ([string]::IsNullOrWhiteSpace($sysInfo)) {
            throw "WSL returned empty status."
        }
        Write-Host "    WSL is fully initialized and ready."
    }
    catch {
        throw "Failed to initialize WSL. Please ensure WSL is installed and working. Details: $_"
    }

    # Step 4: Restart Manager Service
    Write-Host "    Restarting Wazuh Manager Service..."
    wsl bash -c "echo '$WslPass' | sudo -S systemctl restart wazuh-manager"
    Write-Host "    Service restart command sent."
}
catch {
    Write-Error "Failed to activate services: $_"
    exit 1
}

# 2. Scan Session Timestamp
Write-Host "[2/6] Setting Scan Session Timestamp..."
# Ensure directory exists and capture timestamp on Linux side
wsl bash -c "mkdir -p /opt/predictpath && date -u +'%Y-%m-%dT%H:%M:%S' > $ScanStartFlag"
if ($LASTEXITCODE -ne 0) { throw "Failed to set timestamp on Linux host." }
$Timestamp = wsl cat $ScanStartFlag
Write-Host "    Scan Session Start: $Timestamp"

# 3. Force Immediate Scans
Write-Host "[3/6] Triggering Wazuh Modules..."
$Modules = @("syscheck", "rootcheck", "vulnerability", "sca")
foreach ($mod in $Modules) {
    Write-Host "    Restarting $mod..."
    wsl sh -c "echo '$WslPass' | sudo -S /var/ossec/bin/wazuh-control $mod restart" | Out-Null
}

# 4. Controlled Scan Window
Write-Host "[4/6] Waiting for Scan Cycles (30s)..."
Start-Sleep -Seconds 30

# 5. Generate Single JSON Report
Write-Host "[5/6] Generating Compliance & Security Report..."

# Use SINGLE QUOTED Here-String to prevent PowerShell from touching ANY special characters ($ or `)
# We use placeholders __PASS__ and __FLAG__ to inject values safely afterwards
$BashScriptTemplate = @'
#!/bin/bash
set -e
# Warm up sudo with the provided password
echo '__PASS__' | sudo -S ls > /dev/null

START=$(cat __FLAG__)
echo "Filtering events since: $START"

# Create output dir with sudo
echo '__PASS__' | sudo -S mkdir -p /opt/predictpath
echo '__PASS__' | sudo -S chmod 777 /opt/predictpath

# Run JQ with sudo to read ossec logs
# Wazuh alerts.json is NDJSON (line-delimited). We use a two-stage filter:
# 1. Filter lines strictly by timestamp (fast, stream processing)
# 2. Slurp only the relevant events into memory for grouping
echo '__PASS__' | sudo -S cat /var/ossec/logs/alerts/alerts.json | jq -c --arg start "$START" '
  select(.timestamp > $start)
' | jq -s '
  {
    vulnerability: map(select(.rule.groups | index("vulnerability"))),
    malware_behavior: map(select(.rule.groups | (index("malware") or index("rootcheck") or index("syscheck")))),
    privilege_escalation: map(select(.rule.groups | (index("sudo") or index("authentication")))),
    persistence: map(select(.rule.groups | (index("startup") or index("service") or index("rootcheck"))))
  }
' > /opt/predictpath/final_report.json

# Ensure output is readable by normal user
echo '__PASS__' | sudo -S chmod 644 /opt/predictpath/final_report.json
'@

# Inject the PowerShell variables into the template
$BashScript = $BashScriptTemplate.Replace("__PASS__", $WslPass).Replace("__FLAG__", $ScanStartFlag)

# Write Bash script to local temp file (force LF line endings for Linux)
$TempBashPath = "C:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\scripts\wazuh_filter.sh"
[IO.File]::WriteAllText($TempBashPath, $BashScript.Replace("`r`n", "`n"))

# Convert local path to WSL path
$WslScriptPath = "/mnt/c/Users/cisco/Documents/Niru-Predictpath-AI/NiRu-predictpath-tools/scripts/wazuh_filter.sh"

# Execute inside WSL using bash directly (avoids systemd user session issues)
Write-Host "    Executing filter script inside WSL..."
wsl bash -c "bash $WslScriptPath"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate JSON report on Linux host."
    exit 1
}

# 6. Retrieve Report
Write-Host "[6/6] Retrieving Report to Windows..."
try {
    # Ensure local directory exists
    $OutputDir = Split-Path $LocalLogPath -Parent
    if (!(Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }

    # Copy from WSL to Windows
    # Using wsl cat > file ensures we read the content directly
    wsl cat $LinuxReportPath | Out-File -FilePath $LocalLogPath -Encoding UTF8
    
    Write-Host "SUCCESS: Report saved to: $LocalLogPath" -ForegroundColor Green
}
catch {
    Write-Error "Failed to retrieve report: $_"
    exit 1
}

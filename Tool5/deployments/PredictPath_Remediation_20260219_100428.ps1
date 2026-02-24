#======================================================================
# PredictPath AI — Automated Remediation Script
# Generated: 20260219_100428 UTC
# Total Actions: 2  |  Requires Approval: 0
#
# HOW TO USE THIS SCRIPT:
#   1. Review every command carefully before running.
#   2. Open PowerShell as Administrator.
#   3. Run: .\<this_filename>.ps1
#   4. Commands marked '# ROLLBACK:' can undo the change if needed.
#
# WARNING: Some commands modify firewall rules and user accounts.
# Do NOT run on production systems without change-management approval.
#======================================================================

# Ensure running as Administrator
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host '[ERROR] Please run this script as Administrator.' -ForegroundColor Red
    exit 1
}

Write-Host '=== PredictPath AI Remediation Script Starting ===' -ForegroundColor Cyan


#======================================================================
# SECTION 2: ENDPOINT SECURITY MITIGATIONS
# These commands harden the local OS, accounts, and audit policies.
# Run on the affected endpoint (workstation or server).
#======================================================================

# [ENDPOINT] Increase Monitoring for Suspicious User — Session: Activity on System
# Enables verbose logging for the target account: Activity on System
# This uses Windows Advanced Audit Policy for user-level tracking.
auditpol /set /user:"Activity on System" /subcategory:"Detailed File Share" /success:enable
auditpol /set /user:"Activity on System" /subcategory:"Logon" /success:enable /failure:enable
Write-Host '[DONE] Enhanced monitoring active for Activity on System' -ForegroundColor Cyan

# [ENDPOINT] Enable Process Creation Auditing — Session: Activity on 172.20.192.1
# Records every process launch in the Windows Security Event Log.
# This is critical for detecting malware execution chains.
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
Write-Host '[DONE] Process auditing enabled' -ForegroundColor Green
# ROLLBACK: auditpol /set /subcategory:"Process Creation" /success:disable /failure:disable


#======================================================================
# END OF SCRIPT
Write-Host '' 
Write-Host '=== All remediation commands completed. ===' -ForegroundColor Cyan
Write-Host 'Review the output above for any errors.' -ForegroundColor Yellow
#======================================================================
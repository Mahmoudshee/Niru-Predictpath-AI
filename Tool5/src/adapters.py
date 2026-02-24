"""
Tool 5 - Remediation Script Builder
Generates context-aware PowerShell commands based on Tool 4 decisions.
NO auto-execution. Scripts are written to disk for the user to review and run manually.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Domain Classification
# ─────────────────────────────────────────────

NETWORK_ACTIONS = {
    "Block Inbound SMB",
    "Block Outbound C2",
    "Isolate Host",
    "Rate Limit User",
}

ENDPOINT_ACTIONS = {
    "Disable Account",
    "Reset Password",
    "Enable Process Auditing",
    "Enable Logon Failure Auditing",
    "Terminate Process",
    "Monitor User Behavior",
}

WEB_ACTIONS = {
    "Terminate Web Shell Process",
    "Restore Security Configurations",
    "Restrict File Access",
    "Block Inbound IP",
}


def classify_domain(action_type: str) -> str:
    if action_type in NETWORK_ACTIONS:
        return "Network"
    if action_type in ENDPOINT_ACTIONS:
        return "Endpoint"
    if action_type in WEB_ACTIONS:
        return "Web"
    return "General"


# ─────────────────────────────────────────────
# Script Builders — one per action type
# ─────────────────────────────────────────────

def build_block_smb(target: str, session_id: str, cvss: float) -> List[str]:
    return [
        f"# [NETWORK] Block Inbound SMB — Session: {session_id}",
        f"# Threat: SMB lateral movement detected. CVSS Score: {cvss}",
        f"# This rule blocks TCP port 445 from the suspicious source IP.",
        f"netsh advfirewall firewall add rule `",
        f"    name='PredictPath-BlockSMB-{target}' `",
        f"    dir=in action=block protocol=TCP `",
        f"    localport=445 remoteip={target}",
        f"Write-Host '[DONE] SMB blocked from {target}' -ForegroundColor Green",
        "",
    ]


def build_isolate_host(target: str, session_id: str) -> List[str]:
    return [
        f"# [NETWORK] Full Host Isolation — Session: {session_id}",
        f"# WARNING: This will block ALL inbound and outbound traffic on this machine.",
        f"# Run on the compromised host: {target}",
        f"netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound",
        f"Write-Host '[DONE] Host {target} is now ISOLATED' -ForegroundColor Red",
        "",
    ]


def build_rate_limit(target: str, session_id: str) -> List[str]:
    return [
        f"# [NETWORK] Rate Limit Suspicious User — Session: {session_id}",
        f"# Applies a QoS policy to throttle traffic from {target}",
        f"New-NetQosPolicy -Name 'PredictPath-RateLimit-{target}' `",
        f"    -IPSrcPrefix {target}/32 `",
        f"    -ThrottleRateActionBitsPerSecond 1MB",
        f"Write-Host '[DONE] Rate limit applied to {target}' -ForegroundColor Yellow",
        "",
    ]


def build_disable_account(target: str, session_id: str) -> List[str]:
    return [
        f"# [ENDPOINT] Disable Compromised Account — Session: {session_id}",
        f"# Disables the user account to prevent further access.",
        f"# Target account: {target}",
        f"net user \"{target}\" /active:no",
        f"Write-Host '[DONE] Account {target} has been disabled' -ForegroundColor Green",
        f"# ROLLBACK: net user \"{target}\" /active:yes",
        "",
    ]


def build_reset_password(target: str, session_id: str) -> List[str]:
    return [
        f"# [ENDPOINT] Force Password Reset — Session: {session_id}",
        f"# Forces the user to reset their password on next login.",
        f"net user \"{target}\" /logonpasswordchg:yes",
        f"Write-Host '[DONE] Password reset forced for {target}' -ForegroundColor Green",
        "",
    ]


def build_process_auditing(session_id: str) -> List[str]:
    return [
        f"# [ENDPOINT] Enable Process Creation Auditing — Session: {session_id}",
        f"# Records every process launch in the Windows Security Event Log.",
        f"# This is critical for detecting malware execution chains.",
        f"auditpol /set /subcategory:\"Process Creation\" /success:enable /failure:enable",
        f"Write-Host '[DONE] Process auditing enabled' -ForegroundColor Green",
        f"# ROLLBACK: auditpol /set /subcategory:\"Process Creation\" /success:disable /failure:disable",
        "",
    ]


def build_logon_auditing(session_id: str) -> List[str]:
    return [
        f"# [ENDPOINT] Enable Logon Failure Auditing — Session: {session_id}",
        f"# Records failed login attempts — key indicator of brute-force attacks.",
        f"auditpol /set /subcategory:\"Logon\" /failure:enable",
        f"Write-Host '[DONE] Logon failure auditing enabled' -ForegroundColor Green",
        f"# ROLLBACK: auditpol /set /subcategory:\"Logon\" /failure:disable",
        "",
    ]


def build_monitor_user(target: str, session_id: str) -> List[str]:
    return [
        f"# [ENDPOINT] Increase Monitoring for Suspicious User — Session: {session_id}",
        f"# Enables verbose logging for the target account: {target}",
        f"# This uses Windows Advanced Audit Policy for user-level tracking.",
        f"auditpol /set /user:\"{target}\" /subcategory:\"Detailed File Share\" /success:enable",
        f"auditpol /set /user:\"{target}\" /subcategory:\"Logon\" /success:enable /failure:enable",
        f"Write-Host '[DONE] Enhanced monitoring active for {target}' -ForegroundColor Cyan",
        "",
    ]


def build_web_guidance(action_type: str, target: str, session_id: str, guidelines: List[str]) -> List[str]:
    lines = [
        f"# [WEB] {action_type} — Session: {session_id}",
        f"Write-Host '[GUIDANCE] This action requires manual steps on the web console/server.' -ForegroundColor Cyan",
        f"Write-Host 'Target: {target}' -ForegroundColor White",
        f"# See Tactical_Remediation_Guideline.md for full step-by-step instructions.",
    ]
    for g in guidelines:
        lines.append(f"# • {g}")
    lines.append("")
    return lines


# ─────────────────────────────────────────────
# Main Script Builder Entry Point
# ─────────────────────────────────────────────

def build_script_block(action_type: str, target: str, session_id: str, vuln_details: Dict[str, Any], guidelines: List[str] = None) -> List[str]:
    """Returns a list of PowerShell lines for the given action."""
    cvss = vuln_details.get("max_cvss", 0.0)
    g_list = guidelines or []

    dispatch = {
        "Block Inbound SMB":          lambda: build_block_smb(target, session_id, cvss),
        "Isolate Host":               lambda: build_isolate_host(target, session_id),
        "Rate Limit User":            lambda: build_rate_limit(target, session_id),
        "Disable Account":            lambda: build_disable_account(target, session_id),
        "Reset Password":             lambda: build_reset_password(target, session_id),
        "Enable Process Auditing":    lambda: build_process_auditing(session_id),
        "Enable Logon Failure Auditing": lambda: build_logon_auditing(session_id),
        "Monitor User Behavior":      lambda: build_monitor_user(target, session_id),
        
        # Web Actions - Guidance based
        "Terminate Web Shell Process":   lambda: build_web_guidance("Terminate Web Shell Process", target, session_id, g_list),
        "Restore Security Configurations": lambda: build_web_guidance("Restore Security Configurations", target, session_id, g_list),
        "Restrict File Access":          lambda: build_web_guidance("Restrict File Access", target, session_id, g_list),
        "Block Inbound IP":              lambda: build_web_guidance("Block Inbound IP", target, session_id, g_list),
    }

    builder = dispatch.get(action_type)
    if builder:
        return builder()
    
    # Fallback for unknown actions
    lines = [
        f"# [GENERAL] {action_type} — Session: {session_id}",
        f"# No specific command template available for this action.",
        f"# Manual review required for target: {target}",
        f"Write-Host '[MANUAL] Review required: {action_type} on {target}' -ForegroundColor Yellow",
    ]
    for g in g_list:
        lines.append(f"# • {g}")
    lines.append("")
    return lines

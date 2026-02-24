from typing import Dict, List, Literal, Tuple

# Action Definitions with Base Cost (0.0 - 1.0)
ACTION_COSTS = {
    "Monitor User Behavior": 0.0,
    "Enable Process Auditing": 0.1,
    "Enable Logon Failure Auditing": 0.1,
    "Alert SOC (High Priority)": 0.2,
    "Block Inbound SMB": 0.5,
    "Block Inbound IP": 0.5,
    "Disable Account": 0.6,
    "Terminate Web Shell Process": 0.7,
    "Restore Security Configurations": 0.4,
    "Restrict File Access": 0.5,
    "Isolate Host": 0.9
}

# Thresholds
CONFIDENCE_THRESHOLDS = {
    "Monitor User Behavior": 0.0,
    "Enable Process Auditing": 0.1,
    "Enable Logon Failure Auditing": 0.1,
    "Alert SOC (High Priority)": 0.35,
    "Block Inbound SMB": 0.6,
    "Block Inbound IP": 0.6,
    "Disable Account": 0.75,
    "Terminate Web Shell Process": 0.7,
    "Restore Security Configurations": 0.5,
    "Restrict File Access": 0.6,
    "Isolate Host": 0.85
}

# Mapping: Predicted Technique -> List of Candidate Countermeasures (Desc Impact)
TECHNIQUE_RESPONSE_MAP = {
    "T1078": ["Disable Account", "Enable Logon Failure Auditing"], 
    "T1110": ["Disable Account", "Alert SOC (High Priority)"], 
    "T1046": ["Isolate Host", "Enable Process Auditing"],
    "T1021": ["Isolate Host", "Block Inbound SMB"], 
    "T1003": ["Isolate Host", "Alert SOC (High Priority)"], 
    "T1560": ["Isolate Host", "Alert SOC (High Priority)"], 
    "T1041": ["Isolate Host", "Alert SOC (High Priority)"],
    "T1486": ["Isolate Host"],
    "T1190": ["Isolate Host", "Enable Process Auditing"],
    "T1059": ["Isolate Host", "Enable Process Auditing"],
    "T1505": ["Isolate Host", "Terminate Web Shell Process"],
    "T1562": ["Isolate Host", "Restore Security Configurations"],
    "T1592": ["Enable Process Auditing", "Monitor User Behavior"],
    "T1595": ["Block Inbound IP", "Monitor User Behavior"],
    "T1083": ["Enable Process Auditing", "Restrict File Access"],
}

# Human-Readable Guidelines per Action
MITIGATION_GUIDELINES = {
    "Monitor User Behavior": [
        "Increase telemetry depth for this principal.",
        "Scan session logs for unusual data access patterns.",
        "Cross-reference activity with known baseline for this role."
    ],
    "Enable Process Auditing": [
        "Activate Sysmon or similar tool to track process creation.",
        "Review command-line arguments for suspicious encoded strings.",
        "Monitor for unauthorized use of living-off-the-land (LotL) binaries."
    ],
    "Enable Logon Failure Auditing": [
        "Track source IPs of failed authentication attempts.",
        "Implement account lockout policies if not already present.",
        "Review VPN/Remote access logs for anomalous geolocation."
    ],
    "Alert SOC (High Priority)": [
        "Immediate notification to IR team for deep-dive analysis.",
        "Preserve volatile memory and artifacts on the source host.",
        "Initiate comprehensive threat hunting in the surrounding segment."
    ],
    "Block Inbound SMB": [
        "Disable NetBIOS and SMB over port 445 on the host.",
        "Verify firewall rules to restrict SMB to admin-only IPs.",
        "Review for lateral movement attempts via PsExec or WMI."
    ],
    "Disable Account": [
        "Revoke all active tokens and sessions immediately.",
        "Reset all associated secrets (passwords, MFA keys).",
        "Conduct audit of last 24 hours of account history."
    ],
    "Isolate Host": [
        "Disconnect host from all internal and external networks.",
        "For Cloud/Web assets: Suspend deployment or enable 'Maintenance Mode' in console.",
        "Scan all other hosts in the same segment for persistence."
    ],
    "Block Inbound IP": [
        "Add source IP to global edge firewall deny list.",
        "Verify if any other internal assets have communicated with this IP.",
        "Initiate WHOIS investigation to determine actor origin."
    ],
    "Terminate Web Shell Process": [
        "Identify parent process (often httpd/nginx/iis) for exploit path.",
        "Quarantine the suspected web shell file for analysis.",
        "Patch the vulnerability used to upload the shell (check CWE-434)."
    ],
    "Restore Security Configurations": [
        "Re-enable Defender/AV that was likely disabled by the actor.",
        "Audit firewall rules for new 'allow' entries.",
        "Verify integrity of security logging configuration."
    ],
    "Restrict File Access": [
        "Apply Principle of Least Privilege to sensitive directories.",
        "Enable File Integrity Monitoring (FIM) for core files.",
        "Review for unauthorized modification of permission masks (CWE-264)."
    ]
}

# Risk Reduction Estimates (Heuristic)
RISK_REDUCTION_MAP = {
    "Enable Logon Failure Auditing": 0.2, 
    "Disable Account": 0.95, 
    "Isolate Host": 0.99, 
    "Enable Process Auditing": 0.25,
    "Block Inbound SMB": 0.8, 
    "Alert SOC (High Priority)": 0.5,
    "Block Inbound IP": 0.7,
    "Terminate Web Shell Process": 0.9,
    "Restore Security Configurations": 0.4,
    "Restrict File Access": 0.6,
    "Monitor User Behavior": 0.1
}

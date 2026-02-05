from typing import Dict, List, Literal, Tuple

# Action Definitions with Base Cost (0.0 - 1.0)
ACTION_COSTS = {
    "Monitor User Behavior": 0.0,
    "Enable Process Auditing": 0.1,
    "Enable Logon Failure Auditing": 0.1,
    "Alert SOC (High Priority)": 0.2,
    "Block Inbound SMB": 0.5,
    "Disable Account": 0.6,
    "Isolate Host": 0.9
}

# Thresholds
CONFIDENCE_THRESHOLDS = {
    "Monitor User Behavior": 0.0,
    "Enable Process Auditing": 0.1,
    "Enable Logon Failure Auditing": 0.1,
    "Alert SOC (High Priority)": 0.35,
    "Block Inbound SMB": 0.6,
    "Disable Account": 0.75,
    "Isolate Host": 0.85
}

# Mapping: Predicted Technique -> List of Candidate Countermeasures (Desc Impact)
TECHNIQUE_RESPONSE_MAP = {
    "T1078": ["Disable Account", "Enable Logon Failure Auditing"], 
    "T1110": ["Disable Account", "Alert SOC (High Priority)"], 
    "T1046": ["Isolate Host", "Enable Process Auditing"], # Isolate is extreme for scan, but ensures rejection log
    "T1021": ["Isolate Host", "Block Inbound SMB"], 
    "T1003": ["Isolate Host", "Alert SOC (High Priority)"], 
    "T1560": ["Isolate Host", "Alert SOC (High Priority)"], 
    "T1041": ["Isolate Host", "Alert SOC (High Priority)"],
    "T1486": ["Isolate Host"],
    "T1190": ["Isolate Host", "Block Inbound SMB"]
}

# Risk Reduction Estimates (Heuristic)
RISK_REDUCTION_MAP = {
    "Enable Logon Failure Auditing": 0.2, 
    "Disable Account": 0.95, 
    "Isolate Host": 0.99, 
    "Enable Process Auditing": 0.2,
    "Block Inbound SMB": 0.8, 
    "Alert SOC (High Priority)": 0.5,
}

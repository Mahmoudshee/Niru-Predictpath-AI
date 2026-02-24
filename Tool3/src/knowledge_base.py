from typing import Dict, List, Tuple

# Transition Probabilities (Bayesian Priors)
TRANSITION_MATRIX: Dict[str, List[Tuple[str, float]]] = {
    # T1078 - Valid Accounts
    "T1078": [
        ("T1046", 0.40), # -> Network Service Discovery
        ("T1087", 0.30), # -> Account Discovery
        ("T1021", 0.20), # -> Remote Services (Lateral)
        ("T1059", 0.05)  # -> Command Execution
    ],
    
    # T1110 - Brute Force
    "T1110": [
        ("T1078", 0.50), # -> Valid Accounts (Success)
        ("T1003", 0.10), # -> OS Credential Dumping
        ("T1046", 0.10)  # -> Discovery (Pivot)
    ],
    
    # T1046 - Network Discovery
    "T1046": [
        ("T1021", 0.60), # -> Remote Services (Lateral Movement)
        ("T1190", 0.20), # -> Exploit Public Facing App
        ("T1041", 0.05)  # -> Exfil (Rare early)
    ],
    
    # T1021 - Remote Services (Lateral Movement)
    "T1021": [
        ("T1560", 0.40), # -> Archive Collected Data
        ("T1003", 0.30), # -> Credential Dumping (on new host)
        ("T1059", 0.20)  # -> Execution
    ],
    
    # T1059 - Command & Scripting
    "T1059": [
        ("T1003", 0.30), # -> Credential Dumping
        ("T1046", 0.30), # -> Discovery
        ("T1560", 0.20), # -> Collection
        ("T1486", 0.10)  # -> Data Encrypted for Impact (Ransomware)
    ],
    
    # T1560 - Archive Collected Data
    "T1560": [
        ("T1048", 0.70), # -> Exfiltration Over Alternative Protocol
        ("T1041", 0.25)  # -> Exfiltration Over C2 Channel
    ],
    
    # T1041 - Exfiltration
    "T1041": [
        ("T1486", 0.50), # -> Impact (Encryption)
        ("T1496", 0.20)  # -> Resource Hijacking (Mining)
    ],
    
    # T1550 - Use Alt Auth Material (Pass the Hash)
    "T1550": [
        ("T1021", 0.80), # -> Lateral Movement (Primary Goal)
        ("T1003", 0.10)  # -> More Dumping
    ],

    # T1190 - Exploit Public Facing App
    "T1190": [
        ("T1059", 0.60), # -> Execution (Command Injection)
        ("T1083", 0.20), # -> File/Dir Discovery
        ("T1505", 0.10), # -> Persistence (Web Shell)
        ("T1562.001", 0.10) # -> Disable Security Tools
    ],

    # T1083 - File/Directory Discovery
    "T1083": [
        ("T1003", 0.40), # -> Credential Dumping (searching configs)
        ("T1560", 0.40), # -> Data Collection
        ("T1046", 0.20)  # -> Further network discovery
    ],

    # T1592 - Gather Victim Host Information (Recon)
    "T1592": [
        ("T1190", 0.50), # -> Exploit (using gathered info)
        ("T1046", 0.30), # -> Network Discovery
        ("T1083", 0.20)  # -> File Discovery
    ],

    # T1562 - Impair Defenses
    "T1562": [
        ("T1059", 0.60), # -> Execution (now that tools are down)
        ("T1021", 0.30), # -> Lateral Movement
        ("T1041", 0.10)  # -> Exfil
    ],

    # T1595 - Active Scanning
    "T1595": [
        ("T1592", 0.40), # -> Information Gathering
        ("T1190", 0.40), # -> Web Exploit
        ("T1046", 0.20)  # -> Discovery
    ]
}

# Dwell Time Estimates (in seconds)
TIME_PRIORS: Dict[str, Tuple[float, float]] = {
    "T1078": (60, 3600),     # 1m - 1h
    "T1110": (1, 600),       # 1s - 10m
    "T1046": (30, 900),      # 30s - 15m
    "T1021": (300, 7200),    # 5m - 2h
    "T1059": (10, 600),      # 10s - 10m
    "T1003": (60, 1800),     # 1m - 30m
    "T1560": (120, 3600),    # 2m - 1h
    "T1041": (300, 14400),   # 5m - 4h
    "T1486": (60, 300),      # Ransomware is fast once started
    "T1190": (10, 300),      # Exploits are usually followed quickly by execution
    "T1083": (10, 600),
    "T1505": (300, 86400),   # Web shells can sit for a day
    "T1562.001": (5, 60),    # Disabling tools is instant
    "T1562": (10, 300),
    "T1592": (300, 172800),  # Recon can last days
    "T1595": (1, 300),       # Scans are fast
}

# Negative Explainability (What usually comes before?)
# Used to say "We predict T1021, supported by observed T1046"
PREREQUISITES: Dict[str, List[str]] = {
    "T1021": ["T1078", "T1046", "T1550"], # Needs creds or visibility
    "T1003": ["T1059", "T1078", "T1083"], # Needs admin or access
    "T1486": ["T1021", "T1059", "T1041"], # usually late stage
    "T1059": ["T1190", "T1078", "T1562"],
}

def get_technique_name(tid: str) -> str:
    names = {
        "T1078": "Valid Accounts",
        "T1110": "Brute Force",
        "T1046": "Network Service Discovery",
        "T1087": "Account Discovery",
        "T1021": "Remote Services",
        "T1059": "Command and Scripting Interpreter",
        "T1003": "OS Credential Dumping",
        "T1560": "Archive Collected Data",
        "T1041": "Exfiltration Over C2 Channel",
        "T1048": "Exfiltration Over Alternative Protocol",
        "T1190": "Exploit Public-Facing Application",
        "T1486": "Data Encrypted for Impact",
        "T1550": "Use Alternate Authentication Material",
        "T1083": "File and Directory Discovery",
        "T1505": "Server Software Component (Web Shell)",
        "T1562.001": "Impair Defenses: Disable or Modify Tools",
        "T1562": "Impair Defenses",
        "T1592": "Gather Victim Host Information",
        "T1595": "Active Scanning"
    }
    return names.get(tid, tid)

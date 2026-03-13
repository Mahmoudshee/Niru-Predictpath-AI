"""
Enricher - MITRE ATT&CK mapping + VulnIntel CVE/CWE enrichment.
Production-quality: keyword rules + live DB lookups, fully fault-tolerant.
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional, List

from ..core.vulnintel_bridge import (
    extract_cve_ids,
    extract_cwe_ids,
    enrich_with_vulnintel,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MITRE ATT&CK Keyword Rules
# (technique_id, confidence, tactic, technique_name, keywords)
# ─────────────────────────────────────────────────────────────────────────────
_MITRE_RULES: List[Tuple[str, float, str, str, List[str]]] = [
    # Defense Evasion
    ("T1562", 0.80, "defense-evasion", "Impair Defenses",
     ["antivirus disabled", "windows defender disabled", "av disabled", "firewall disabled",
      "security disabled", "defender turned off"]),
    # Process Injection
    ("T1055", 0.75, "defense-evasion", "Process Injection",
     ["process injection", "dll injection", "hollowing", "reflective dll", "shellcode"]),
    # Brute Force
    ("T1110", 0.85, "credential-access", "Brute Force",
     ["failed login", "authentication failure", "auth failure", "invalid password",
      "brute force", "login failed", "incorrect password", "multiple failed", "bad password",
      "logon failure", "account lockout"]),
    # Valid Accounts
    ("T1078", 0.80, "defense-evasion", "Valid Accounts",
     ["successful login", "user logon", "authentication success", "logged on", "logged in",
      "session opened", "logon success", "accepted password", "new session"]),
    # Remote Services
    ("T1021", 0.75, "lateral-movement", "Remote Services",
     ["rdp", "3389", "smb", "445", "ssh", "22 open", "remote desktop",
      "winrm", "psexec", "wmi", "dcom"]),
    # Network Service Scanning
    ("T1046", 0.80, "discovery", "Network Service Scanning",
     ["port scan", "nmap", "network scan", "service scan", "host discovery",
      "open port", "masscan", "zenmap"]),
    # Exploit Public-Facing Application
    ("T1190", 0.75, "initial-access", "Exploit Public-Facing Application",
     ["sql injection", "sqlmap", "xss", "rce", "remote code execution",
      "buffer overflow", "path traversal", "directory traversal", "lfi", "rfi",
      "arbitrary code", "web exploit", "deserialization"]),
    # Command & Scripting
    ("T1059", 0.75, "execution", "Command and Scripting Interpreter",
     ["powershell", "cmd.exe", "bash", "sh -c", "command execution",
      "script execution", "wscript", "cscript", "mshta"]),
    # Privilege Escalation
    ("T1548", 0.85, "privilege-escalation", "Abuse Elevation Control Mechanism",
     ["sudo", "privilege escalat", "elevation", "setuid", "run as administrator",
      "uac bypass", "administrator access", "root access"]),
    # File/Registry Integrity
    ("T1565", 0.70, "impact", "Data Manipulation",
     ["integrity checksum changed", "file modified", "syscheck", "hash changed",
      "md5 changed", "sha1 changed", "file integrity"]),
    # Registry Modification
    ("T1112", 0.80, "defense-evasion", "Modify Registry",
     ["registry", "hklm", "hkcu", "hkey_local_machine", "hkey_current_user",
      "reg add", "reg delete", "regedit", "registry key modified"]),
    # Indicator Removal
    ("T1070", 0.70, "defense-evasion", "Indicator Removal on Host",
     ["log cleared", "event log cleared", "audit log deleted", "security log cleared",
      "winevt", "clear-eventlog"]),
    # Obfuscation
    ("T1027", 0.70, "defense-evasion", "Obfuscated Files or Information",
     ["base64", "obfuscat", "encoded payload", "packed executable", "encoded command",
      "-encodedcommand", "-enc ", "iex "]),
    # C2 Communication
    ("T1071", 0.65, "command-and-control", "Application Layer Protocol",
     ["c2", "command and control", "beacon", "c&c", "malware communication",
      "reverse shell", "callback"]),
    # Pass the Hash
    ("T1550", 0.75, "lateral-movement", "Use Alternate Authentication Material",
     ["pass the hash", "pth", "pass the ticket", "golden ticket", "overpass"]),
    # Kerberos Attacks
    ("T1558", 0.80, "credential-access", "Steal or Forge Kerberos Tickets",
     ["kerberos", "kerberoast", "as-rep", "asrep", "tgt", "tgs"]),
    # Exfiltration
    ("T1041", 0.75, "exfiltration", "Exfiltration Over C2 Channel",
     ["exfiltrat", "data leak", "data exfil", "ftp put", "upload to external"]),
    # Malware / Rootkit Generic
    ("T1204", 0.60, "execution", "User Execution",
     ["malware", "ransomware", "trojan", "rootkit", "worm", "keylogger",
      "spyware", "adware", "virus detected"]),
    # Active Scanning
    ("T1595", 0.65, "reconnaissance", "Active Scanning",
     ["recon", "reconnaissance", "enumerat", "fingerprint", "os detection"]),
    # Account Discovery
    ("T1087", 0.65, "discovery", "Account Discovery",
     ["whoami", "net user", "net group", "getent passwd", "id command"]),
    # System Info Discovery
    ("T1082", 0.60, "discovery", "System Information Discovery",
     ["systeminfo", "uname -a", "hostname", "ipconfig", "ifconfig",
      "host info", "system info"]),
    # PowerShell-specific
    ("T1086", 0.85, "execution", "PowerShell",
     ["invoke-expression", "downloadstring", "download cradle",
      "new-object net.webclient", "start-process"]),
    # Scheduled Tasks
    ("T1053", 0.75, "persistence", "Scheduled Task/Job",
     ["schtasks", "cron", "at.exe", "scheduled task", "crontab",
      "task scheduler", "new-scheduledtask"]),
    # Persistence via startup
    ("T1547", 0.70, "persistence", "Boot or Logon Autostart Execution",
     ["autostart", "startup", "runkey", "hkcu\\software\\microsoft\\windows\\currentversion\\run",
      "hklm\\software\\microsoft\\windows\\currentversion\\run", "startup folder"]),
]


class Enricher:
    """
    Production enricher: MITRE ATT&CK keyword mapping + VulnIntel CVE/CWE lookup.
    Never raises — always returns safe defaults on failure.
    """

    MODEL_VERSION = "keyword-rules-v3+vulnintel"

    def infer_mitre(self, text: str) -> Tuple[Optional[str], float, Optional[str], Optional[str]]:
        """
        Returns (technique_id, confidence, tactic, technique_name) based on keyword matching.
        Searches entire text including nested JSON fields.
        """
        if not text:
            return None, 0.0, None, None

        text_lower = text.lower()

        # Find the best (highest confidence) matching rule
        best = (None, 0.0, None, None)
        for tech_id, confidence, tactic, tech_name, keywords in _MITRE_RULES:
            for kw in keywords:
                if kw in text_lower:
                    if confidence > best[1]:
                        best = (tech_id, confidence, tactic, tech_name)
                    break  # Only match once per rule

        return best

    def calculate_severity(self, event_type: str, mitre_conf: float, cve_max_cvss: Optional[float]) -> str:
        """Map event attributes to a severity label."""
        # CVE-driven
        if cve_max_cvss is not None:
            if cve_max_cvss >= 9.0:
                return "critical"
            elif cve_max_cvss >= 7.0:
                return "high"
            elif cve_max_cvss >= 4.0:
                return "medium"
            return "low"

        # MITRE confidence-driven
        if mitre_conf >= 0.80:
            return "high"
        elif mitre_conf >= 0.65:
            return "medium"
        elif mitre_conf > 0.0:
            return "low"

        # Event type fallback
        if event_type in ("auth_failure", "security_alert"):
            return "medium"
        return "info"

    def calculate_data_quality(self, source_host: Optional[str], user: Optional[str],
                                protocol: Optional[str], timestamp_valid: bool) -> float:
        """Score data quality (1.0 = perfect, penalize missing fields)."""
        score = 1.0
        if not source_host or source_host == "unknown":
            score -= 0.15
        if not user:
            score -= 0.15
        if not protocol or protocol.upper() in ("UNKNOWN", ""):
            score -= 0.10
        if not timestamp_valid:
            score -= 0.20
        return max(0.0, round(score, 2))

    def calculate_risk_score(self, confidence: float, cve_max_cvss: Optional[float],
                              is_kev: bool, severity: str) -> float:
        """
        Composite risk score (0.0 – 1.0):
        - MITRE confidence contributes 40%
        - CVE CVSS score contributes 40%
        - KEV multiplier adds 20%
        """
        mitre_component = confidence * 0.4
        cve_component = (min(cve_max_cvss or 0.0, 10.0) / 10.0) * 0.4
        kev_bonus = 0.20 if is_kev else 0.0
        base = mitre_component + cve_component + kev_bonus

        # Severity floor
        floors = {"critical": 0.80, "high": 0.60, "medium": 0.40, "low": 0.20, "info": 0.0}
        floor = floors.get(severity, 0.0)

        return round(min(1.0, max(floor, base)), 3)

    def enrich(self, normalized: Dict[str, Any], rich_text: str, raw_dict: Any) -> Dict[str, Any]:
        """
        Main enrichment entry point. Mutates and returns the normalized dict.
        Never raises — guarantees safe defaults.
        """
        try:
            # Build enrichment text from all available fields
            all_text = self._build_enrichment_text(rich_text, raw_dict)

            # 1. MITRE ATT&CK
            tech_id, confidence, tactic, tech_name = self.infer_mitre(all_text)
            normalized["mitre_technique"] = tech_id
            normalized["mitre_tactic"] = tactic
            normalized["mitre_technique_name"] = tech_name
            normalized["confidence_score"] = round(confidence, 3)

            # 2. CVE/CWE extraction from raw text
            cve_ids = extract_cve_ids(all_text)
            cwe_ids = extract_cwe_ids(all_text)
            normalized["observed_cve_ids"] = cve_ids
            normalized["observed_cwe_ids"] = cwe_ids

            # 3. VulnIntel enrichment
            cve_max_cvss, cve_severity, is_kev = enrich_with_vulnintel(cve_ids)
            normalized["cve_max_cvss"] = cve_max_cvss
            normalized["cve_severity"] = cve_severity
            normalized["is_kev"] = is_kev

            # 4. Severity calculation
            severity = self.calculate_severity(
                normalized.get("event_type", ""),
                confidence,
                cve_max_cvss,
            )
            normalized["severity"] = severity

            # 5. Data quality
            normalized["data_quality_score"] = self.calculate_data_quality(
                normalized.get("source_host"),
                normalized.get("user"),
                normalized.get("protocol"),
                timestamp_valid=True,
            )

            # 6. Risk score
            normalized["risk_score"] = self.calculate_risk_score(
                confidence, cve_max_cvss, is_kev, severity
            )

            # 7. Model version
            normalized["model_version"] = self.MODEL_VERSION

        except Exception as e:
            logger.error(f"Enrichment failed: {e}", exc_info=True)
            # Apply safe defaults — NEVER let enrichment failure kill the pipeline
            normalized.setdefault("mitre_technique", None)
            normalized.setdefault("mitre_tactic", None)
            normalized.setdefault("mitre_technique_name", None)
            normalized.setdefault("confidence_score", 0.0)
            normalized.setdefault("observed_cve_ids", [])
            normalized.setdefault("observed_cwe_ids", [])
            normalized.setdefault("cve_max_cvss", None)
            normalized.setdefault("cve_severity", None)
            normalized.setdefault("is_kev", False)
            normalized.setdefault("severity", "info")
            normalized.setdefault("data_quality_score", 0.5)
            normalized.setdefault("risk_score", 0.0)
            normalized.setdefault("model_version", self.MODEL_VERSION)

        return normalized

    def _build_enrichment_text(self, rich_text: str, raw_dict: Any) -> str:
        """Concatenate all useful text fields for keyword matching."""
        parts = [rich_text or ""]

        if isinstance(raw_dict, dict):
            # Harvest all nested string values
            self._flatten_strings(raw_dict, parts, depth=0)

        return " ".join(p for p in parts if p).lower()

    def _flatten_strings(self, obj: Any, parts: List[str], depth: int) -> None:
        """Recursively extract string values from nested dicts/lists."""
        if depth > 5:
            return
        if isinstance(obj, str):
            parts.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                self._flatten_strings(v, parts, depth + 1)
        elif isinstance(obj, list):
            for item in obj[:20]:  # Cap list traversal
                self._flatten_strings(item, parts, depth + 1)

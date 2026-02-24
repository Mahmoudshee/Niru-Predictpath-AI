import sqlite3
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class VulnManager:
    """
    Vulnerability Intelligence Access Layer (READ-ONLY).
    Indexed and cached per execution cycle.
    """
    def __init__(self, db_path: str = "C:/Users/cisco/Documents/Niru-Predictpath-AI/NiRu-predictpath-tools/VulnIntel/data/db/vuln.db"):
        self.db_path = db_path
        self._cache = {}

    def batch_lookup_cves(self, cve_ids: List[str]) -> Dict[str, Any]:
        """
        Batch query CVE/KEV status.
        """
        if not cve_ids:
            return {}

        results = {}
        missing = [c for c in cve_ids if c not in self._cache]
        
        if missing:
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                placeholders = ','.join(['?'] * len(missing))
                
                # Fetch CVE, CVSS, KEV status and CWE mappings
                query = """
                    SELECT 
                        c.cve_id, 
                        c.cvss_v3_score, 
                        c.description,
                        (SELECT GROUP_CONCAT(cwe_id) FROM cve_cwe_map m WHERE m.cve_id = c.cve_id) as cwe_list,
                        (SELECT 1 FROM kev k WHERE k.cve_id = c.cve_id) as is_kev,
                        (SELECT k.vulnerability_name FROM kev k WHERE k.cve_id = c.cve_id) as kev_name
                    FROM cve c 
                    WHERE c.cve_id IN ({placeholders})
                """.format(placeholders=placeholders)
                cursor.execute(query, missing)
                
                for row in cursor.fetchall():
                    results[row['cve_id']] = {
                        "cvss": row['cvss_v3_score'] or 0.0,
                        "description": row['description'] or "",
                        "cwe_ids": row['cwe_list'].split(',') if row['cwe_list'] else [],
                        "is_kev": bool(row['is_kev']),
                        "kev_name": row['kev_name']
                    }
                
                conn.close()
                self._cache.update(results)
            except Exception as e:
                logger.error(f"Vulnerability DB Query Error: {e}")

        # Return from cache
        return {c: self._cache.get(c, {"cvss": 0.0, "description": "", "cwe_ids": [], "is_kev": False, "kev_name": None}) for c in cve_ids}

    def _humanize_cwe(self, cwe_id: str, official_name: str) -> str:
        """
        Translates academic CWE titles into common attack names for non-technical users.
        """
        mapping = {
            "CWE-89": "SQL Injection",
            "CWE-78": "OS Command Injection",
            "CWE-79": "Cross-site Scripting (XSS)",
            "CWE-434": "Unrestricted File Upload",
            "CWE-22": "Path Traversal (File Access)",
            "CWE-94": "Code Injection",
            "CWE-20": "Improper Input Validation",
            "CWE-352": "Cross-Site Request Forgery (CSRF)",
            "CWE-611": "XML External Entity (XXE)",
            "CWE-918": "Server-Side Request Forgery (SSRF)",
            "CWE-287": "Improper Authentication",
            "CWE-798": "Hardcoded Credentials",
            "CWE-200": "Information Exposure",
            "CWE-693": "Protection Mechanism Failure",
            "CWE-264": "Incorrect Permissions (Access Control)",
            "CWE-525": "Sensitive Information in Brower Cache",
            "CWE-1021": "Clickjacking (UI Redressing)",
            "CWE-615": "Sensitive Info in Source Comments",
            "CWE-276": "Incorrect Default Permissions",
            "CWE-284": "Improper Access Control",
            "CWE-306": "Missing Authentication for Critical Function",
            "CWE-307": "Improper Restriction of Excessive Authentication Attempts (Brute Force)",
            "CWE-521": "Weak Password Requirements",
            "CWE-285": "Improper Authorization",
            "CWE-77": "Command Injection",
            "CWE-209": "Information Exposure through an Error Message"
        }
        return mapping.get(cwe_id, official_name)

    def batch_lookup_cwes(self, cwe_ids: List[str]) -> Dict[str, Any]:
        """
        Batch query CWE descriptions/classes.
        """
        if not cwe_ids:
            return {}

        results = {}
        missing = [c for c in cwe_ids if c not in self._cache]
        
        if missing:
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                placeholders = ','.join(['?'] * len(missing))
                cursor.execute(f"SELECT cwe_id, name, abstraction FROM cwe WHERE cwe_id IN ({placeholders})", missing)
                
                for row in cursor.fetchall():
                    results[row['cwe_id']] = {
                        "name": self._humanize_cwe(row['cwe_id'], row['name']),
                        "abstraction": row['abstraction']
                    }
                conn.close()
                self._cache.update(results)
            except Exception as e:
                logger.error(f"CWE Query Error: {e}")

        return {c: self._cache.get(c, {"name": self._humanize_cwe(c, "Unknown"), "abstraction": "Unknown"}) for c in cwe_ids}

    def get_mitre_name(self, tech_id: str) -> str:
        """
        Returns human readable name for a MITRE technique.
        """
        seed = {
            "T1078": "Valid Accounts",
            "T1110": "Brute Force",
            "T1059": "Command and Scripting Interpreter",
            "T1046": "Network Service Discovery",
            "T1190": "Exploit Public-Facing Application",
            "T1558": "Steal or Forge Kerberos Tickets",
            "T1550": "Use Alternate Authentication Material",
            "T1021": "Remote Services",
            "T1112": "Modify Registry",
            "T1562.001": "Impair Defenses: Disable or Modify Tools",
            "T1041": "Exfiltration Over C2 Channel"
        }
        return seed.get(tech_id, f"Adversary Technique {tech_id}")

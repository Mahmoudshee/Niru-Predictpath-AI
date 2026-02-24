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
        self._cve_cache: Dict[str, Any] = {}
        self._cwe_cache: Dict[str, Any] = {}

    def batch_lookup_cves(self, cve_ids: List[str]) -> Dict[str, Any]:
        """
        Batch query CVE/KEV status.
        """
        if not cve_ids:
            return {}

        results = {}
        missing = [c for c in cve_ids if c not in self._cve_cache]

        if missing:
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                placeholders = ','.join(['?'] * len(missing))

                query = f"""
                    SELECT c.cve_id, c.cvss_score, c.cwe_ids,
                           (SELECT 1 FROM kev k WHERE k.cve_id = c.cve_id) as is_kev
                    FROM cve c
                    WHERE c.cve_id IN ({placeholders})
                """
                cursor.execute(query, missing)

                for row in cursor.fetchall():
                    self._cve_cache[row['cve_id']] = {
                        "cvss": row['cvss_score'] or 0.0,
                        "cwe_ids": row['cwe_ids'].split(',') if row['cwe_ids'] else [],
                        "is_kev": bool(row['is_kev'])
                    }

                conn.close()
            except Exception as e:
                logger.error(f"Vulnerability DB Query Error: {e}")

        return {c: self._cve_cache.get(c, {"cvss": 0.0, "cwe_ids": [], "is_kev": False}) for c in cve_ids}

    def batch_lookup_cwes(self, cwe_ids: List[str]) -> Dict[str, Any]:
        """
        Batch query CWE descriptions/classes.
        """
        if not cwe_ids:
            return {}

        missing = [c for c in cwe_ids if c not in self._cwe_cache]

        if missing:
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                placeholders = ','.join(['?'] * len(missing))
                cursor.execute(
                    f"SELECT cwe_id, name, weakness_abstraction FROM cwe WHERE cwe_id IN ({placeholders})",
                    missing
                )

                for row in cursor.fetchall():
                    self._cwe_cache[row['cwe_id']] = {
                        "name": row['name'],
                        "abstraction": row['weakness_abstraction']
                    }
                conn.close()
            except Exception as e:
                logger.error(f"CWE Query Error: {e}")

        return {c: self._cwe_cache.get(c, {"name": "Unknown", "abstraction": "Unknown"}) for c in cwe_ids}

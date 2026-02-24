"""Query API for VulnIntel - Public interface for vulnerability intelligence."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import DATABASE_PATH, QUERY_LIMITS
from src.database.connection import get_db_context
from src.database.schema import get_database_stats
from src.utils.logger import get_logger
from src.utils.validators import normalize_cve_id, normalize_cwe_id

logger = get_logger(__name__)


class VulnIntelAPI:
    """Public API for querying vulnerability intelligence data."""
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize VulnIntel API.
        
        Args:
            db_path: Path to database file (defaults to config DATABASE_PATH)
        """
        self.db_path = db_path or DATABASE_PATH
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}. "
                "Run 'python -m src.main init' to initialize."
            )
    
    def get_cve_by_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get CVE details by ID.
        
        Args:
            cve_id: CVE identifier (e.g., "CVE-2024-1234")
            
        Returns:
            CVE record dictionary or None if not found
            
        Example:
            >>> api = VulnIntelAPI()
            >>> cve = api.get_cve_by_id("CVE-2024-1234")
            >>> print(cve['cvss_v3_score'])
        """
        cve_id = normalize_cve_id(cve_id)
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cve WHERE cve_id = ?", (cve_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            cve = dict(row)
            
            # Parse JSON fields
            if cve.get("affected_cpes"):
                cve["affected_cpes"] = json.loads(cve["affected_cpes"])
            if cve.get("reference_urls"):
                cve["reference_urls"] = json.loads(cve["reference_urls"])
            
            # Add CWE mappings
            cursor.execute(
                "SELECT cwe_id FROM cve_cwe_map WHERE cve_id = ?",
                (cve_id,)
            )
            cve["cwe_ids"] = [row["cwe_id"] for row in cursor.fetchall()]
            
            return cve
    
    def get_cwe_by_id(self, cwe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get CWE details by ID.
        
        Args:
            cwe_id: CWE identifier (e.g., "CWE-79")
            
        Returns:
            CWE record dictionary or None if not found
        """
        cwe_id = normalize_cwe_id(cwe_id)
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cwe WHERE cwe_id = ?", (cwe_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            cwe = dict(row)
            
            # Parse JSON fields
            for field in ["common_consequences", "applicable_platforms", 
                         "modes_of_introduction", "detection_methods"]:
                if cwe.get(field):
                    cwe[field] = json.loads(cwe[field])
            
            return cwe
    
    def get_cves_by_cwe(self, cwe_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get CVEs associated with a CWE.
        
        Args:
            cwe_id: CWE identifier (e.g., "CWE-79")
            limit: Maximum number of results
            
        Returns:
            List of CVE records
        """
        cwe_id = normalize_cwe_id(cwe_id)
        limit = min(limit, QUERY_LIMITS["max_limit"])
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.* FROM cve c
                JOIN cve_cwe_map m ON c.cve_id = m.cve_id
                WHERE m.cwe_id = ?
                ORDER BY c.cvss_v3_score DESC, c.published_date DESC
                LIMIT ?
                """,
                (cwe_id, limit)
            )
            
            cves = []
            for row in cursor.fetchall():
                cve = dict(row)
                # Parse JSON fields
                if cve.get("affected_cpes"):
                    cve["affected_cpes"] = json.loads(cve["affected_cpes"])
                if cve.get("reference_urls"):
                    cve["reference_urls"] = json.loads(cve["reference_urls"])
                cves.append(cve)
            
            return cves
    
    def is_cve_exploited(self, cve_id: str) -> bool:
        """
        Check if a CVE is in the KEV catalog (known to be exploited).
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            True if CVE is in KEV, False otherwise
        """
        cve_id = normalize_cve_id(cve_id)
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM kev WHERE cve_id = ?",
                (cve_id,)
            )
            row = cursor.fetchone()
            return row["count"] > 0
    
    def get_high_risk_cves(
        self,
        min_cvss: float = 7.0,
        kev_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get high-risk CVEs.
        
        Args:
            min_cvss: Minimum CVSS score (default: 7.0)
            kev_only: Only return CVEs in KEV catalog
            limit: Maximum number of results
            
        Returns:
            List of CVE records sorted by CVSS score (descending)
        """
        limit = min(limit, QUERY_LIMITS["max_limit"])
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            
            if kev_only:
                query = """
                    SELECT DISTINCT c.* FROM cve c
                    JOIN kev k ON c.cve_id = k.cve_id
                    WHERE c.cvss_v3_score >= ?
                    ORDER BY c.cvss_v3_score DESC, c.published_date DESC
                    LIMIT ?
                """
            else:
                query = """
                    SELECT * FROM cve
                    WHERE cvss_v3_score >= ?
                    ORDER BY cvss_v3_score DESC, published_date DESC
                    LIMIT ?
                """
            
            cursor.execute(query, (min_cvss, limit))
            
            cves = []
            for row in cursor.fetchall():
                cve = dict(row)
                # Parse JSON fields
                if cve.get("affected_cpes"):
                    cve["affected_cpes"] = json.loads(cve["affected_cpes"])
                if cve.get("reference_urls"):
                    cve["reference_urls"] = json.loads(cve["reference_urls"])
                # Add KEV status
                cve["is_exploited"] = self.is_cve_exploited(cve["cve_id"])
                cves.append(cve)
            
            return cves
    
    def get_cves_for_cpe(self, cpe_string: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get CVEs affecting a specific CPE.
        
        Args:
            cpe_string: CPE 2.3 string (e.g., "cpe:2.3:a:apache:http_server:2.4.49")
            limit: Maximum number of results
            
        Returns:
            List of CVE records
        """
        limit = min(limit, QUERY_LIMITS["max_limit"])
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM cve
                WHERE affected_cpes LIKE ?
                ORDER BY cvss_v3_score DESC, published_date DESC
                LIMIT ?
                """,
                (f"%{cpe_string}%", limit)
            )
            
            cves = []
            for row in cursor.fetchall():
                cve = dict(row)
                # Parse JSON fields
                if cve.get("affected_cpes"):
                    cve["affected_cpes"] = json.loads(cve["affected_cpes"])
                if cve.get("reference_urls"):
                    cve["reference_urls"] = json.loads(cve["reference_urls"])
                cves.append(cve)
            
            return cves
    
    def get_kev_entries(
        self,
        days_back: int = 30,
        ransomware_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get KEV entries.
        
        Args:
            days_back: Number of days to look back from today
            ransomware_only: Only return CVEs with known ransomware use
            
        Returns:
            List of KEV records
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            
            if ransomware_only:
                query = """
                    SELECT * FROM kev
                    WHERE date_added >= ? AND known_ransomware_use = 'Known'
                    ORDER BY date_added DESC
                """
            else:
                query = """
                    SELECT * FROM kev
                    WHERE date_added >= ?
                    ORDER BY date_added DESC
                """
            
            cursor.execute(query, (cutoff_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_vuln_stats(self) -> Dict[str, Any]:
        """
        Get vulnerability database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with get_db_context(self.db_path) as conn:
            stats = get_database_stats(conn)
            
            # Add additional stats
            cursor = conn.cursor()
            
            # CVE severity breakdown
            cursor.execute("""
                SELECT cvss_v3_severity, COUNT(*) as count
                FROM cve
                WHERE cvss_v3_severity IS NOT NULL
                GROUP BY cvss_v3_severity
            """)
            stats["cve_by_severity"] = {row["cvss_v3_severity"]: row["count"] 
                                        for row in cursor.fetchall()}
            
            # KEV ransomware stats
            cursor.execute("""
                SELECT known_ransomware_use, COUNT(*) as count
                FROM kev
                GROUP BY known_ransomware_use
            """)
            stats["kev_ransomware"] = {row["known_ransomware_use"]: row["count"] 
                                       for row in cursor.fetchall()}
            
            # Recent CVEs (last 30 days)
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT COUNT(*) as count FROM cve
                WHERE published_date >= ?
            """, (cutoff,))
            stats["recent_cves_30d"] = cursor.fetchone()["count"]
            
            # Sync status
            cursor.execute("SELECT * FROM sync_metadata")
            stats["sync_status"] = {row["source"]: dict(row) for row in cursor.fetchall()}
            
            return stats
    
    def search_cves(
        self,
        keyword: str,
        min_cvss: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search CVEs by keyword in description.
        
        Args:
            keyword: Search keyword
            min_cvss: Minimum CVSS score filter
            limit: Maximum number of results
            
        Returns:
            List of matching CVE records
        """
        limit = min(limit, QUERY_LIMITS["max_limit"])
        
        with get_db_context(self.db_path) as conn:
            cursor = conn.cursor()
            
            if min_cvss is not None:
                query = """
                    SELECT * FROM cve
                    WHERE description LIKE ? AND cvss_v3_score >= ?
                    ORDER BY cvss_v3_score DESC, published_date DESC
                    LIMIT ?
                """
                cursor.execute(query, (f"%{keyword}%", min_cvss, limit))
            else:
                query = """
                    SELECT * FROM cve
                    WHERE description LIKE ?
                    ORDER BY cvss_v3_score DESC, published_date DESC
                    LIMIT ?
                """
                cursor.execute(query, (f"%{keyword}%", limit))
            
            cves = []
            for row in cursor.fetchall():
                cve = dict(row)
                if cve.get("affected_cpes"):
                    cve["affected_cpes"] = json.loads(cve["affected_cpes"])
                if cve.get("reference_urls"):
                    cve["reference_urls"] = json.loads(cve["reference_urls"])
                cves.append(cve)
            
            return cves

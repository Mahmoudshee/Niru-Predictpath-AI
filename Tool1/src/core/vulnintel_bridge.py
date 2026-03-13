"""
VulnIntel Bridge - Queries the VulnIntel SQLite database for CVE/CWE enrichment.
Fully production-safe: handles missing DB, closed connection, and empty results gracefully.
"""
import sqlite3
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Path to VulnIntel DB (relative to this file: Tool1/src/core/ -> ../../.. -> project root -> VulnIntel/data/db)
_VULN_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "VulnIntel" / "data" / "db" / "vuln.db"

# Simple in-process cache to avoid repeated DB hits for the same CVE
_cve_cache: Dict[str, Optional[Dict[str, Any]]] = {}
_kev_cache: Optional[set] = None
_db_available: Optional[bool] = None


def _check_db() -> bool:
    global _db_available
    if _db_available is not None:
        return _db_available
    _db_available = _VULN_DB_PATH.exists()
    if not _db_available:
        logger.warning(f"VulnIntel DB not found at {_VULN_DB_PATH}. CVE enrichment disabled.")
    else:
        logger.info(f"VulnIntel DB found: {_VULN_DB_PATH}")
    return _db_available


def _get_conn() -> Optional[sqlite3.Connection]:
    if not _check_db():
        return None
    try:
        conn = sqlite3.connect(f"file:{_VULN_DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to VulnIntel DB: {e}")
        return None


def extract_cve_ids(text: str) -> List[str]:
    """Extract all CVE-YYYY-NNNNN patterns from arbitrary text."""
    if not text:
        return []
    return list(set(re.findall(r"CVE-\d{4}-\d{1,7}", text, re.IGNORECASE)))


def extract_cwe_ids(text: str) -> List[str]:
    """Extract all CWE-NNN patterns from arbitrary text."""
    if not text:
        return []
    return list(set(re.findall(r"CWE-\d+", text, re.IGNORECASE)))


def get_cve_data(cve_id: str) -> Optional[Dict[str, Any]]:
    """Return CVE record from VulnIntel DB, or None if not found."""
    cve_id = cve_id.upper()
    if cve_id in _cve_cache:
        return _cve_cache[cve_id]

    conn = _get_conn()
    if conn is None:
        _cve_cache[cve_id] = None
        return None

    try:
        cur = conn.execute(
            "SELECT cve_id, description, cvss_v3_score, cvss_v3_severity, attack_vector, affected_cpes "
            "FROM cve WHERE cve_id = ? LIMIT 1",
            (cve_id,)
        )
        row = cur.fetchone()
        result = dict(row) if row else None
        _cve_cache[cve_id] = result
        return result
    except Exception as e:
        logger.debug(f"CVE lookup failed for {cve_id}: {e}")
        _cve_cache[cve_id] = None
        return None
    finally:
        conn.close()


def get_kev_ids() -> set:
    """Return the set of all KEV CVE IDs."""
    global _kev_cache
    if _kev_cache is not None:
        return _kev_cache

    conn = _get_conn()
    if conn is None:
        _kev_cache = set()
        return _kev_cache

    try:
        cur = conn.execute("SELECT cve_id FROM kev")
        _kev_cache = {row[0].upper() for row in cur.fetchall()}
        logger.info(f"Loaded {len(_kev_cache)} KEV entries from VulnIntel DB")
        return _kev_cache
    except Exception as e:
        logger.debug(f"KEV lookup failed: {e}")
        _kev_cache = set()
        return _kev_cache
    finally:
        conn.close()


def enrich_with_vulnintel(
    cve_ids: List[str],
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Given a list of CVE IDs, return:
      - max_cvss: highest CVSS score found
      - max_severity: severity label for that score (CRITICAL/HIGH/MEDIUM/LOW)
      - is_kev: True if any CVE is in CISA KEV catalog
    """
    if not cve_ids:
        return None, None, False

    kev_ids = get_kev_ids()
    is_kev = any(c.upper() in kev_ids for c in cve_ids)

    max_cvss: Optional[float] = None
    max_severity: Optional[str] = None

    for cve_id in cve_ids:
        data = get_cve_data(cve_id)
        if not data:
            continue
        score = data.get("cvss_v3_score")
        if score is not None:
            try:
                score = float(score)
                if max_cvss is None or score > max_cvss:
                    max_cvss = score
                    max_severity = data.get("cvss_v3_severity") or _score_to_severity(score)
            except (TypeError, ValueError):
                pass

    return max_cvss, max_severity, is_kev


def _score_to_severity(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    elif score >= 7.0:
        return "HIGH"
    elif score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"

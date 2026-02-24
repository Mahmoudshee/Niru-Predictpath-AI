"""CVE JSON 2.0 parser for NVD data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.validators import normalize_cve_id, sanitize_text, cvss_score_to_severity

logger = get_logger(__name__)


class CVEParser:
    """Parser for NVD CVE JSON 2.0 format."""
    
    def __init__(self) -> None:
        """Initialize CVE parser."""
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_file(self, file_path: Path, source_feed: str) -> List[Dict[str, Any]]:
        """
        Parse CVE JSON file.
        
        Args:
            file_path: Path to JSON file
            source_feed: Source feed identifier (e.g., "recent", "modified")
            
        Returns:
            List of parsed CVE records
        """
        logger.info(f"Parsing CVE file: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        vulnerabilities = data.get("vulnerabilities", [])
        logger.info(f"Found {len(vulnerabilities)} vulnerabilities")
        
        parsed_cves = []
        
        for item in vulnerabilities:
            try:
                cve_json = item.get("cve", {})
                cve_record = self.parse_cve_item(cve_json, source_feed)
                if cve_record:
                    parsed_cves.append(cve_record)
                    self.parsed_count += 1
            except Exception as e:
                self.error_count += 1
                cve_id = item.get("cve", {}).get("id", "UNKNOWN")
                logger.error(f"Error parsing CVE {cve_id}: {e}")
        
        logger.info(f"Parsed {self.parsed_count} CVEs, {self.error_count} errors")
        return parsed_cves
    
    def parse_cve_item(self, cve_json: Dict[str, Any], source_feed: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single CVE item from JSON 2.0 format.
        
        Args:
            cve_json: CVE dictionary from 'vulnerabilities' list
            source_feed: Source feed identifier
            
        Returns:
            Parsed CVE record or None if invalid
        """
        cve_id = cve_json.get("id")
        if not cve_id:
            return None
        
        cve_id = normalize_cve_id(cve_id)
        
        # Extract description
        descriptions = cve_json.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        
        # Extract published and modified dates
        published_date = cve_json.get("published", "")
        last_modified_date = cve_json.get("lastModified", "")
        
        # Extract CVSS metrics
        metrics = cve_json.get("metrics", {})
        
        cvss_v3_score = None
        cvss_v3_severity = None
        cvss_v3_vector = None
        attack_vector = None
        attack_complexity = None
        privileges_required = None
        user_interaction = None
        scope = None
        confidentiality_impact = None
        integrity_impact = None
        availability_impact = None
        
        # Try CVSS v3.1 first, then v3.0, then v2.0
        cvss_data = None
        
        if metrics.get("cvssMetricV31"):
            cvss_entry = metrics["cvssMetricV31"][0]
            cvss_data = cvss_entry.get("cvssData", {})
        elif metrics.get("cvssMetricV30"):
            cvss_entry = metrics["cvssMetricV30"][0]
            cvss_data = cvss_entry.get("cvssData", {})
        
        if cvss_data:
            cvss_v3_score = cvss_data.get("baseScore")
            cvss_v3_severity = cvss_data.get("baseSeverity")
            cvss_v3_vector = cvss_data.get("vectorString")
            attack_vector = cvss_data.get("attackVector")
            attack_complexity = cvss_data.get("attackComplexity")
            privileges_required = cvss_data.get("privilegesRequired")
            user_interaction = cvss_data.get("userInteraction")
            scope = cvss_data.get("scope")
            confidentiality_impact = cvss_data.get("confidentialityImpact")
            integrity_impact = cvss_data.get("integrityImpact")
            availability_impact = cvss_data.get("availabilityImpact")
        elif metrics.get("cvssMetricV2"):
            cvss_entry = metrics["cvssMetricV2"][0]
            cvss_data = cvss_entry.get("cvssData", {})
            cvss_v3_score = cvss_data.get("baseScore")
            if cvss_v3_score is not None:
                cvss_v3_severity = cvss_score_to_severity(cvss_v3_score)
        
        # Extract affected CPEs
        configurations = cve_json.get("configurations", [])
        cpes = self.extract_cpes(configurations)
        
        # Extract CWE IDs
        weaknesses = cve_json.get("weaknesses", [])
        cwe_ids = self.extract_cwe_ids(weaknesses)
        
        # Extract references
        references_list = cve_json.get("references", [])
        references = [{"url": ref.get("url"), "source": ref.get("source", "")} for ref in references_list if ref.get("url")]
        
        # Current timestamp
        now = datetime.utcnow().isoformat() + "Z"
        
        return {
            "cve_id": cve_id,
            "description": sanitize_text(description),
            "published_date": published_date,
            "last_modified_date": last_modified_date,
            "cvss_v3_score": cvss_v3_score,
            "cvss_v3_severity": cvss_v3_severity,
            "cvss_v3_vector": cvss_v3_vector,
            "attack_vector": attack_vector,
            "attack_complexity": attack_complexity,
            "privileges_required": privileges_required,
            "user_interaction": user_interaction,
            "scope": scope,
            "confidentiality_impact": confidentiality_impact,
            "integrity_impact": integrity_impact,
            "availability_impact": availability_impact,
            "affected_cpes": json.dumps(cpes),
            "reference_urls": json.dumps(references),
            "cwe_ids": cwe_ids,
            "source_feed": source_feed,
            "ingested_at": now,
            "updated_at": now,
        }
    
    def extract_cpes(self, configurations: List[Dict[str, Any]]) -> List[str]:
        """Extract CPE strings from configurations in JSON 2.0 format."""
        cpes = []
        
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    cpe_uri = cpe_match.get("criteria")
                    if cpe_uri:
                        cpes.append(cpe_uri)
        
        return list(set(cpes))  # Remove duplicates
    
    def extract_cwe_ids(self, weaknesses: List[Dict[str, Any]]) -> List[str]:
        """Extract CWE IDs from weaknesses in JSON 2.0 format."""
        cwe_ids = []
        
        for weakness in weaknesses:
            for description in weakness.get("description", []):
                value = description.get("value", "")
                if value.startswith("CWE-"):
                    cwe_ids.append(value.upper())
        
        return list(set(cwe_ids))  # Remove duplicates

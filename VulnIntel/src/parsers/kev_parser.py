"""KEV JSON parser for CISA data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.utils.logger import get_logger
from src.utils.validators import normalize_cve_id, sanitize_text

logger = get_logger(__name__)


class KEVParser:
    """Parser for CISA KEV JSON format."""
    
    def __init__(self) -> None:
        """Initialize KEV parser."""
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse KEV JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of parsed KEV records
        """
        logger.info(f"Parsing KEV file: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        vulnerabilities = data.get("vulnerabilities", [])
        logger.info(f"Found {len(vulnerabilities)} KEV entries")
        
        parsed_kevs = []
        
        for vuln in vulnerabilities:
            try:
                kev_record = self.parse_vulnerability(vuln)
                if kev_record:
                    parsed_kevs.append(kev_record)
                    self.parsed_count += 1
            except Exception as e:
                self.error_count += 1
                cve_id = vuln.get("cveID", "UNKNOWN")
                logger.error(f"Error parsing KEV {cve_id}: {e}")
        
        logger.info(f"Parsed {self.parsed_count} KEV entries, {self.error_count} errors")
        return parsed_kevs
    
    def parse_vulnerability(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single KEV vulnerability entry.
        
        Args:
            vuln: Vulnerability dictionary
            
        Returns:
            Parsed KEV record
        """
        cve_id = vuln.get("cveID")
        if not cve_id:
            return None
        
        cve_id = normalize_cve_id(cve_id)
        
        vendor_project = vuln.get("vendorProject", "")
        product = vuln.get("product", "")
        vulnerability_name = vuln.get("vulnerabilityName", "")
        date_added = vuln.get("dateAdded", "")
        short_description = vuln.get("shortDescription", "")
        required_action = vuln.get("requiredAction", "")
        due_date = vuln.get("dueDate", "")
        known_ransomware_use = vuln.get("knownRansomwareCampaignUse", "Unknown")
        notes = vuln.get("notes", "")
        
        # Current timestamp
        now = datetime.utcnow().isoformat() + "Z"
        
        return {
            "cve_id": cve_id,
            "vendor_project": sanitize_text(vendor_project),
            "product": sanitize_text(product),
            "vulnerability_name": sanitize_text(vulnerability_name),
            "date_added": date_added,
            "short_description": sanitize_text(short_description),
            "required_action": sanitize_text(required_action),
            "due_date": due_date,
            "known_ransomware_use": known_ransomware_use,
            "notes": sanitize_text(notes),
            "ingested_at": now,
            "updated_at": now,
        }

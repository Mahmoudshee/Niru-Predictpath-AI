"""CWE XML parser for MITRE data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

from src.utils.logger import get_logger
from src.utils.validators import normalize_cwe_id, sanitize_text

logger = get_logger(__name__)


class CWEParser:
    """Parser for MITRE CWE XML format."""
    
    # XML namespaces
    NS = {"cwe": "http://cwe.mitre.org/cwe-7"}
    
    def __init__(self) -> None:
        """Initialize CWE parser."""
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse CWE XML file.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            List of parsed CWE records
        """
        logger.info(f"Parsing CWE file: {file_path}")
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Parse weaknesses
        weaknesses = root.findall(".//cwe:Weakness", self.NS)
        logger.info(f"Found {len(weaknesses)} CWE weaknesses")
        
        parsed_cwes = []
        
        for weakness in weaknesses:
            try:
                cwe_record = self.parse_weakness(weakness)
                if cwe_record:
                    parsed_cwes.append(cwe_record)
                    self.parsed_count += 1
            except Exception as e:
                self.error_count += 1
                cwe_id = weakness.get("ID", "UNKNOWN")
                logger.error(f"Error parsing CWE-{cwe_id}: {e}")
        
        logger.info(f"Parsed {self.parsed_count} CWEs, {self.error_count} errors")
        return parsed_cwes
    
    def parse_weakness(self, weakness: ET.Element) -> Dict[str, Any]:
        """
        Parse a single CWE weakness element.
        
        Args:
            weakness: XML element for weakness
            
        Returns:
            Parsed CWE record
        """
        cwe_id = weakness.get("ID")
        if not cwe_id:
            return None
        
        cwe_id = normalize_cwe_id(f"CWE-{cwe_id}")
        
        name = weakness.get("Name", "")
        abstraction = weakness.get("Abstraction", "")
        status = weakness.get("Status", "")
        
        # Extract description
        description_elem = weakness.find("cwe:Description", self.NS)
        description = ""
        if description_elem is not None:
            description = self.get_element_text(description_elem)
        
        # Extract likelihood of exploit
        likelihood_elem = weakness.find("cwe:Likelihood_Of_Exploit", self.NS)
        likelihood_of_exploit = likelihood_elem.text if likelihood_elem is not None else None
        
        # Extract common consequences
        consequences = self.extract_consequences(weakness)
        
        # Extract applicable platforms
        platforms = self.extract_platforms(weakness)
        
        # Extract modes of introduction
        modes = self.extract_modes_of_introduction(weakness)
        
        # Extract detection methods
        detection_methods = self.extract_detection_methods(weakness)
        
        # Current timestamp
        now = datetime.utcnow().isoformat() + "Z"
        
        return {
            "cwe_id": cwe_id,
            "name": sanitize_text(name),
            "description": sanitize_text(description),
            "abstraction": abstraction,
            "status": status,
            "likelihood_of_exploit": likelihood_of_exploit,
            "common_consequences": json.dumps(consequences),
            "applicable_platforms": json.dumps(platforms),
            "modes_of_introduction": json.dumps(modes),
            "detection_methods": json.dumps(detection_methods),
            "ingested_at": now,
            "updated_at": now,
        }
    
    def get_element_text(self, element: ET.Element) -> str:
        """Extract all text from an element and its children."""
        return "".join(element.itertext()).strip()
    
    def extract_consequences(self, weakness: ET.Element) -> List[Dict[str, Any]]:
        """Extract common consequences."""
        consequences = []
        
        consequences_elem = weakness.find("cwe:Common_Consequences", self.NS)
        if consequences_elem is not None:
            for consequence in consequences_elem.findall("cwe:Consequence", self.NS):
                scope_elems = consequence.findall("cwe:Scope", self.NS)
                scopes = [s.text for s in scope_elems if s.text]
                
                impact_elems = consequence.findall("cwe:Impact", self.NS)
                impacts = [i.text for i in impact_elems if i.text]
                
                note_elem = consequence.find("cwe:Note", self.NS)
                note = note_elem.text if note_elem is not None else ""
                
                if scopes or impacts:
                    consequences.append({
                        "scopes": scopes,
                        "impacts": impacts,
                        "note": note,
                    })
        
        return consequences
    
    def extract_platforms(self, weakness: ET.Element) -> List[Dict[str, Any]]:
        """Extract applicable platforms."""
        platforms = []
        
        platforms_elem = weakness.find("cwe:Applicable_Platforms", self.NS)
        if platforms_elem is not None:
            # Languages
            for lang in platforms_elem.findall("cwe:Language", self.NS):
                name = lang.get("Name", "")
                prevalence = lang.get("Prevalence", "")
                if name:
                    platforms.append({
                        "type": "language",
                        "name": name,
                        "prevalence": prevalence,
                    })
            
            # Technologies
            for tech in platforms_elem.findall("cwe:Technology", self.NS):
                name = tech.get("Name", "")
                prevalence = tech.get("Prevalence", "")
                if name:
                    platforms.append({
                        "type": "technology",
                        "name": name,
                        "prevalence": prevalence,
                    })
            
            # Operating Systems
            for os_elem in platforms_elem.findall("cwe:Operating_System", self.NS):
                name = os_elem.get("Name", "")
                prevalence = os_elem.get("Prevalence", "")
                if name:
                    platforms.append({
                        "type": "os",
                        "name": name,
                        "prevalence": prevalence,
                    })
        
        return platforms
    
    def extract_modes_of_introduction(self, weakness: ET.Element) -> List[Dict[str, str]]:
        """Extract modes of introduction."""
        modes = []
        
        modes_elem = weakness.find("cwe:Modes_Of_Introduction", self.NS)
        if modes_elem is not None:
            for intro in modes_elem.findall("cwe:Introduction", self.NS):
                phase_elem = intro.find("cwe:Phase", self.NS)
                phase = phase_elem.text if phase_elem is not None else ""
                
                note_elem = intro.find("cwe:Note", self.NS)
                note = note_elem.text if note_elem is not None else ""
                
                if phase:
                    modes.append({
                        "phase": phase,
                        "note": note,
                    })
        
        return modes
    
    def extract_detection_methods(self, weakness: ET.Element) -> List[Dict[str, str]]:
        """Extract detection methods."""
        methods = []
        
        detection_elem = weakness.find("cwe:Detection_Methods", self.NS)
        if detection_elem is not None:
            for method in detection_elem.findall("cwe:Detection_Method", self.NS):
                method_type_elem = method.find("cwe:Method", self.NS)
                method_type = method_type_elem.text if method_type_elem is not None else ""
                
                description_elem = method.find("cwe:Description", self.NS)
                description = self.get_element_text(description_elem) if description_elem is not None else ""
                
                if method_type:
                    methods.append({
                        "method": method_type,
                        "description": description,
                    })
        
        return methods

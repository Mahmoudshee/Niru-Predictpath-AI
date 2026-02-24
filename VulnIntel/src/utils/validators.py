"""Data validation utilities for VulnIntel."""

import re
from typing import Optional


def validate_cve_id(cve_id: str) -> bool:
    """
    Validate CVE ID format.
    
    Args:
        cve_id: CVE identifier (e.g., "CVE-2024-1234")
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_cve_id("CVE-2024-1234")
        True
        >>> validate_cve_id("CVE-99-123")
        False
        >>> validate_cve_id("invalid")
        False
    """
    pattern = r"^CVE-\d{4}-\d{4,}$"
    return bool(re.match(pattern, cve_id, re.IGNORECASE))


def validate_cwe_id(cwe_id: str) -> bool:
    """
    Validate CWE ID format.
    
    Args:
        cwe_id: CWE identifier (e.g., "CWE-79")
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_cwe_id("CWE-79")
        True
        >>> validate_cwe_id("CWE-1234")
        True
        >>> validate_cwe_id("invalid")
        False
    """
    pattern = r"^CWE-\d+$"
    return bool(re.match(pattern, cwe_id, re.IGNORECASE))


def normalize_cve_id(cve_id: str) -> str:
    """
    Normalize CVE ID to uppercase.
    
    Args:
        cve_id: CVE identifier
        
    Returns:
        Normalized CVE ID
        
    Examples:
        >>> normalize_cve_id("cve-2024-1234")
        'CVE-2024-1234'
    """
    return cve_id.upper()


def normalize_cwe_id(cwe_id: str) -> str:
    """
    Normalize CWE ID to uppercase.
    
    Args:
        cwe_id: CWE identifier
        
    Returns:
        Normalized CWE ID
        
    Examples:
        >>> normalize_cwe_id("cwe-79")
        'CWE-79'
    """
    return cwe_id.upper()


def extract_cve_id(text: str) -> Optional[str]:
    """
    Extract CVE ID from text.
    
    Args:
        text: Text potentially containing CVE ID
        
    Returns:
        Normalized CVE ID if found, None otherwise
        
    Examples:
        >>> extract_cve_id("Found vulnerability CVE-2024-1234 in system")
        'CVE-2024-1234'
        >>> extract_cve_id("No CVE here")
        None
    """
    pattern = r"CVE-\d{4}-\d{4,}"
    match = re.search(pattern, text, re.IGNORECASE)
    return normalize_cve_id(match.group(0)) if match else None


def extract_cwe_id(text: str) -> Optional[str]:
    """
    Extract CWE ID from text.
    
    Args:
        text: Text potentially containing CWE ID
        
    Returns:
        Normalized CWE ID if found, None otherwise
        
    Examples:
        >>> extract_cwe_id("This is CWE-79 (XSS)")
        'CWE-79'
        >>> extract_cwe_id("No CWE here")
        None
    """
    pattern = r"CWE-\d+"
    match = re.search(pattern, text, re.IGNORECASE)
    return normalize_cwe_id(match.group(0)) if match else None


def validate_cvss_score(score: float) -> bool:
    """
    Validate CVSS score range.
    
    Args:
        score: CVSS score
        
    Returns:
        True if valid (0.0-10.0), False otherwise
        
    Examples:
        >>> validate_cvss_score(7.5)
        True
        >>> validate_cvss_score(10.0)
        True
        >>> validate_cvss_score(11.0)
        False
    """
    return 0.0 <= score <= 10.0


def cvss_score_to_severity(score: Optional[float]) -> str:
    """
    Convert CVSS score to severity rating.
    
    Args:
        score: CVSS score (0.0-10.0)
        
    Returns:
        Severity rating (NONE, LOW, MEDIUM, HIGH, CRITICAL)
        
    Examples:
        >>> cvss_score_to_severity(0.0)
        'NONE'
        >>> cvss_score_to_severity(3.5)
        'LOW'
        >>> cvss_score_to_severity(6.5)
        'MEDIUM'
        >>> cvss_score_to_severity(8.5)
        'HIGH'
        >>> cvss_score_to_severity(9.5)
        'CRITICAL'
    """
    if score is None:
        return "UNKNOWN"
    
    if score == 0.0:
        return "NONE"
    elif score < 4.0:
        return "LOW"
    elif score < 7.0:
        return "MEDIUM"
    elif score < 9.0:
        return "HIGH"
    else:
        return "CRITICAL"


def sanitize_text(text: Optional[str], max_length: Optional[int] = None) -> str:
    """
    Sanitize text for database storage.
    
    Args:
        text: Input text
        max_length: Maximum length (truncate if exceeded)
        
    Returns:
        Sanitized text
    """
    if text is None:
        return ""
    
    # Remove null bytes and excessive whitespace
    text = text.replace("\x00", "").strip()
    text = re.sub(r"\s+", " ", text)
    
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text

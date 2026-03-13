"""
CanonicalEvent Schema - Single Source of Truth for PredictPath AI.
Production-grade, fully serializable, no strict-mode conflicts.
"""
from datetime import datetime, timezone
from typing import Optional, List, Any
from dataclasses import dataclass, field, asdict
import hashlib
import json
import uuid


@dataclass
class CanonicalEvent:
    """
    The authoritative security event structure for PredictPath AI.
    Using dataclass instead of Pydantic strict-mode to avoid serialization
    headaches with complex nested types from real-world logs.
    """
    # Core Identifiers
    event_id: str
    timestamp: datetime
    ingest_timestamp: datetime

    # Semantic Classification
    event_type: str          # auth_success, auth_failure, network_connect, etc.
    severity: str            # critical, high, medium, low, info

    # Entities
    source_host: Optional[str]
    target_host: Optional[str]
    user: Optional[str]
    agent_name: Optional[str]

    # Network
    protocol: Optional[str]
    port: Optional[int]

    # MITRE ATT&CK Enrichment
    mitre_technique: Optional[str]      # e.g. T1059
    mitre_tactic: Optional[str]         # e.g. execution
    mitre_technique_name: Optional[str] # e.g. Command and Scripting Interpreter

    # Vulnerability Intelligence (from VulnIntel DB)
    observed_cve_ids: List[str]
    observed_cwe_ids: List[str]
    cve_max_cvss: Optional[float]       # Highest CVSS score among observed CVEs
    cve_severity: Optional[str]         # CRITICAL, HIGH, MEDIUM, LOW
    is_kev: bool                        # In CISA Known Exploited Vulnerabilities?

    # Scoring
    confidence_score: float             # 0.0 – 1.0
    data_quality_score: float           # 0.0 – 1.0
    risk_score: float                   # Composite: MITRE confidence + CVE score

    # Provenance
    source_file: str
    parser_version: str
    model_version: str
    log_category: str                   # wazuh, nmap, zap, syslog, generic, etc.

    # Raw Data (for audit trail)
    raw_source: str
    raw_hash: str                       # SHA256 of raw_source
    previous_event_hash: Optional[str]
    event_hash: Optional[str]           # SHA256 of canonical structure

    @classmethod
    def create(
        cls,
        event_type: str,
        timestamp: datetime,
        source_file: str,
        parser_version: str,
        raw_source: str,
        log_category: str = "generic",
        source_host: Optional[str] = None,
        target_host: Optional[str] = None,
        user: Optional[str] = None,
        agent_name: Optional[str] = None,
        protocol: Optional[str] = None,
        port: Optional[int] = None,
        mitre_technique: Optional[str] = None,
        mitre_tactic: Optional[str] = None,
        mitre_technique_name: Optional[str] = None,
        observed_cve_ids: Optional[List[str]] = None,
        observed_cwe_ids: Optional[List[str]] = None,
        cve_max_cvss: Optional[float] = None,
        cve_severity: Optional[str] = None,
        is_kev: bool = False,
        confidence_score: float = 0.0,
        data_quality_score: float = 0.0,
        risk_score: float = 0.0,
        severity: str = "info",
        model_version: str = "v1.0",
        previous_event_hash: Optional[str] = None,
    ) -> "CanonicalEvent":
        now = datetime.now(timezone.utc)
        raw_hash = hashlib.sha256(raw_source.encode("utf-8", errors="replace")).hexdigest()

        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            ingest_timestamp=now,
            event_type=event_type,
            severity=severity,
            source_host=source_host,
            target_host=target_host,
            user=user,
            agent_name=agent_name,
            protocol=protocol,
            port=port,
            mitre_technique=mitre_technique,
            mitre_tactic=mitre_tactic,
            mitre_technique_name=mitre_technique_name,
            observed_cve_ids=observed_cve_ids or [],
            observed_cwe_ids=observed_cwe_ids or [],
            cve_max_cvss=cve_max_cvss,
            cve_severity=cve_severity,
            is_kev=is_kev,
            confidence_score=confidence_score,
            data_quality_score=data_quality_score,
            risk_score=risk_score,
            source_file=source_file,
            parser_version=parser_version,
            model_version=model_version,
            log_category=log_category,
            raw_source=raw_source[:4000],  # Cap at 4KB to avoid huge Parquet rows
            raw_hash=raw_hash,
            previous_event_hash=previous_event_hash,
            event_hash=None,
        )

    def compute_event_hash(self, previous_hash: Optional[str] = None) -> "CanonicalEvent":
        """Compute the event chain hash and return a new instance."""
        d = self.to_dict()
        d.pop("event_hash", None)
        if previous_hash:
            d["previous_event_hash"] = previous_hash
        canonical_str = json.dumps(d, sort_keys=True, default=str)
        event_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        self.event_hash = event_hash
        self.previous_event_hash = previous_hash
        return self

    def to_dict(self) -> dict:
        """Serialize to plain dict, safe for Parquet/JSON storage."""
        d = asdict(self)
        # Convert datetimes to ISO strings for Parquet compatibility
        for k in ("timestamp", "ingest_timestamp"):
            if isinstance(d[k], datetime):
                d[k] = d[k].isoformat()
        # Convert lists to pipe-delimited strings for Parquet columnar storage
        d["observed_cve_ids"] = "|".join(d.get("observed_cve_ids") or [])
        d["observed_cwe_ids"] = "|".join(d.get("observed_cwe_ids") or [])
        return d

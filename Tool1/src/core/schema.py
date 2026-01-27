from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import hashlib
import json
import uuid
from enum import Enum
from .exceptions import SchemaValidationError

class RejectionReason(str, Enum):
    SCHEMA_VIOLATION = "SchemaViolation"
    PARSING_ERROR = "ParsingError"
    ENRICHMENT_FAILURE = "EnrichmentFailure"
    INTEGRITY_FAILURE = "IntegrityFailure"
    UNKNOWN = "Unknown"

class RejectionEvent(BaseModel):
    """
    Strict schema for rejected events (DLQ).
    Ensures every failure is accounted for.
    """
    model_config = ConfigDict(strict=True, frozen=True)

    rejection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rejection_reason: RejectionReason
    raw_source: str
    source_file: str
    ingest_timestamp: datetime = Field(default_factory=datetime.utcnow)
    parser_version: str
    error_message: str

class EventType(str, Enum):
    # Semantic Actions (Not Protocols)
    AuthSuccess = "auth_success"
    AuthFailure = "auth_failure"
    ProcessStart = "process_start"
    NetworkConnect = "network_connect"
    FileWrite = "file_write"
    PrivilegeUse = "privilege_use"
    Unknown = "unknown"

class CanonicalEvent(BaseModel):
    """
    The Single Source of Truth for Security Events in PredictPath AI.
    All raw events must be normalized to this schema.
    """
    model_config = ConfigDict(strict=True, frozen=True) # Immutable and strict

    # Core Identifiers
    event_id: str = Field(..., description="Unique UUID for the event")
    timestamp: datetime = Field(..., description="UTC Timestamp of the event occurrence")
    
    # Semantic Fields
    event_type: str = Field(..., description="High-level semantic event type (e.g. auth_success)")
    
    # Entities
    source_host: Optional[str] = None
    target_host: Optional[str] = None
    user: Optional[str] = None
    
    # Network Details
    protocol: Optional[str] = None
    port: Optional[int] = Field(None, ge=0, le=65535)
    
    # Enrichment
    mitre_technique: Optional[str] = Field(None, description="MITRE ATT&CK Technique ID (e.g., T1059)")
    mitre_tactic: Optional[str] = None
    
    # Scoring
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model certainty (0.0-1.0)")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Data integrity score (0.0-1.0)")
    
    # Provenance & Versioning
    ingest_timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_file: str = Field(..., description="Source filename or origin")
    parser_version: str = Field(..., description="Version of the parser used")
    model_version: str = Field(..., description="Version of the enrichment model used")
    
    # Raw Data
    raw_source: str = Field(..., description="Original raw log line for auditability")

    # Integrity (Hashing)
    raw_hash: str = Field(..., description="SHA256 of the raw_source")
    previous_event_hash: Optional[str] = Field(None, description="Hash of the previous event for chaining")
    event_hash: Optional[str] = Field(None, description="SHA256 of the canonical event (calculated post-init)")

    @field_validator('timestamp')
    @classmethod
    def validate_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise SchemaValidationError("Timestamp must be timezone-aware (UTC).")
        return v

    def compute_hashes(self, previous_hash: Optional[str] = None) -> 'CanonicalEvent':
        """
        Computes raw_hash and event_hash to ensure integrity.
        Returns a NEW instance since the model is frozen.
        """
        # 1. Compute Raw Hash
        raw_bytes = self.raw_source.encode('utf-8')
        computed_raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        
        # 2. Compute Event Hash (Canonical structure without the hash field itself)
        # We use a stable JSON representation of the model fields except event_hash
        model_dict = self.model_dump(exclude={'event_hash'})
        if previous_hash:
            model_dict['previous_event_hash'] = previous_hash
            
        # Sort keys for deterministic hashing
        # Handle datetime serialization for consistency
        canonical_str = json.dumps(model_dict, sort_keys=True, default=str)
        computed_event_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        
        # Return a new object with updated hashes (bypassing validation for the update)
        return self.model_copy(update={
            'raw_hash': computed_raw_hash,
            'event_hash': computed_event_hash,
            'previous_event_hash': previous_hash
        })

    def validate_integrity(self):
        """Re-computes hashes and verifies they match the stored values."""
        # Check raw hash
        computed_raw = hashlib.sha256(self.raw_source.encode('utf-8')).hexdigest()
        if computed_raw != self.raw_hash:
             raise SchemaValidationError(f"Integrity Mismatch! Raw hash {self.raw_hash} != {computed_raw}")
        
        # Check event hash
        model_dict = self.model_dump(exclude={'event_hash'})
        canonical_str = json.dumps(model_dict, sort_keys=True, default=str)
        computed_event = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        
        if computed_event != self.event_hash:
            raise SchemaValidationError(f"Integrity Mismatch! Event hash {self.event_hash} != {computed_event}")

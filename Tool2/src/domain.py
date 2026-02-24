from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class EnrichedEvent(BaseModel):
    """
    Represents a single event ingested from Tool 1's Parquet output.
    """
    event_id: str
    timestamp: datetime
    user: Optional[str] = "Unknown"
    source_host: Optional[str] = "Unknown"
    target_host: Optional[str] = None
    event_type: str
    protocol: Optional[str] = None
    mitre_technique: Optional[str] = None
    observed_cve_ids: List[str] = []
    observed_cwe_ids: List[str] = []
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_quality_score: float = Field(..., ge=0.0, le=1.0)
    raw_text: Optional[str] = None

class Session(BaseModel):
    """
    Represents a grouped set of events for an identity within a time window.
    """
    session_id: str
    user: Optional[str] = "Unknown"
    start_time: datetime
    end_time: datetime
    events: List[EnrichedEvent]
    is_high_priority: bool = False

class PathPrediction(BaseModel):
    """
    Prediction for the next likely steps in the attack path.
    """
    next_node: str
    probability: float

class PathReport(BaseModel):
    """
    Final JSON output report for the Behavioral Path Reconstruction.
    """
    session_id: str
    root_cause_node: str
    blast_radius: List[str]
    path_anomaly_score: float
    prediction_vector: List[PathPrediction]
    vulnerability_summary: List[str] = []
    observed_techniques: List[str] = []
    cwe_clusters: List[str] = []
    event_summary: Dict[str, int] = {}
    tactical_narrative: str = ""
    plain_language_summary: str = ""
    business_risk_level: str = "Informational"  # High, Medium, Low, Informational
    generated_at: datetime = Field(default_factory=datetime.utcnow)

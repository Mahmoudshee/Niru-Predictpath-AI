from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid

class CurrentState(BaseModel):
    observed_techniques: List[str]
    last_seen_timestamp: datetime
    graph_depth: int
    host_scope: List[str]
    observed_vulnerabilities: List[str] = []

class ReactionTimeWindow(BaseModel):
    min_seconds: float
    max_seconds: float

class TrajectoryExplainability(BaseModel):
    positive_evidence: List[str] = Field(..., description="Factors increasing likelihood")
    negative_evidence: List[str] = Field(..., description="Factors decreasing likelihood")
    uncertainty_factors: List[str] = Field(..., description="Why we are not 100% sure")

class PredictedScenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence: List[str] = Field(..., description="Ordered list of predicted MITRE technique IDs")
    human_readable_sequence: str = ""
    probability: float = Field(..., ge=0.0, le=1.0)
    reaction_time_window: ReactionTimeWindow
    time_window_text: str = ""
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    scenario_type: Optional[Literal["Primary", "Secondary", "Opportunistic"]] = Field(None, description="Ranking classification")
    explainability: TrajectoryExplainability

class PredictionSummary(BaseModel):
    """
    Final Output Artifact for Tool 3 (Strict Contract).
    """
    model_config = ConfigDict(strict=True)

    session_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    current_state: CurrentState
    aggregate_confidence: float = Field(..., ge=0.0, le=1.0)
    predicted_scenarios: List[PredictedScenario]
    mentor_narrative: str = ""
    model_version: str
    evidence_summary: Dict[str, Any]
    suppression_reason: Optional[str] = None

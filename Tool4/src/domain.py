from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal, Any, Union
from pydantic import BaseModel, Field, ConfigDict
import uuid

class ActionTarget(BaseModel):
    type: Literal["User", "Host", "Network Segment"]
    identifier: str

class ConfidenceAlignment(BaseModel):
    tool3_confidence: float
    decision_confidence: float
    threshold_applied: float

class RiskReduction(BaseModel):
    absolute: float = Field(..., description="Numeric reduction in probability (0.0-1.0)")
    relative: str = Field(..., description="Description of improved state")

class ActionJustification(BaseModel):
    predicted_scenarios: List[str]
    risk_reduction: RiskReduction
    time_to_impact_seconds: Optional[int]
    confidence_alignment: ConfidenceAlignment
    signal_gap_closed: str

class RecommendedAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str # More granular string now
    action_class: Literal["Containment", "Disruptive"] = "Containment"
    requires_approval: bool = False
    target: ActionTarget
    vulnerability_details: Dict[str, Any] = Field(default_factory=dict, description="Metadata like max_cvss and is_kev")
    mitigation_guidelines: List[str] = Field(default_factory=list, description="Step-by-step guidance for the user")
    justification: ActionJustification
    recommended_within_seconds: int

class RejectedAction(BaseModel):
    candidate_action: str
    rejection_reasons: List[str]

class DecisionExplainability(BaseModel):
    why_now: str
    why_not_later: str
    what_happens_if_ignored: str
    correlation_context: Optional[str] = None

class ResponseDecision(BaseModel):
    """
    Final Decision Object per session.
    """
    model_config = ConfigDict(strict=True)

    session_id: str
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_confidence: float
    priority_rank: int
    urgency_level: Literal["Low", "Medium", "High", "Critical"]
    recommended_actions: List[RecommendedAction]
    rejected_actions: List[RejectedAction]
    model_version: str
    mentor_summary: str = ""
    decision_explainability: DecisionExplainability

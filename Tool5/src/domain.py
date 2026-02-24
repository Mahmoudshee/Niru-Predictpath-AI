from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid
import hashlib

# --- Enums & Constants ---

class ActionCategory(str):
    OBSERVATIONAL = "Observational"
    CONTAINMENT = "Containment"
    DISRUPTIVE = "Disruptive"
    IRREVERSIBLE = "Irreversible"

class ExecutionMode(str):
    AUTO = "auto"
    STAGED = "staged"
    REJECTED = "rejected"
    SKIPPED = "skipped" # If action already active

class ExecutionStatus(str):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    ROLLED_BACK = "rolled_back"

# --- Input Models (Mapping from Tool 4 output) ---

# We only need partial mapping of Tool 4's ResponseDecision to ingest it
class Tool4Target(BaseModel):
    type: str # User, Host
    identifier: str

class Tool4Action(BaseModel):
    action_type: str
    target: Tool4Target
    requires_approval: bool = False
    vulnerability_details: Dict[str, Any] = {}
    justification: Dict[str, Any]

class Tool4Decision(BaseModel):
    session_id: str
    decision_confidence: float
    urgency_level: str
    recommended_actions: List[Tool4Action]

# --- Tool 5 Internal Models ---

class RollbackToken(BaseModel):
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_action_id: str
    rollback_command: str
    parameters: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExecutionMetadata(BaseModel):
    category: str # ActionCategory
    blast_radius_score: float
    risk_check_passed: bool
    policy_check_passed: bool
    requires_approval: bool

class ExecutionResult(BaseModel):
    action_id: str
    session_id: str
    target: str
    action_name: str
    execution_mode: str # ExecutionMode
    final_status: str # ExecutionStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executor: str # system / human
    message: str
    action_narrative: str = ""
    dry_run_output: Optional[str] = None
    rollback_token: Optional[RollbackToken] = None
    audit_hash: Optional[str] = None

class ExecutionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executions: List[ExecutionResult]
    summary_stats: Dict[str, int]

# --- Audit Logging ---

class AuditLogEntry(BaseModel):
    timestamp: str
    action_id: str
    action_type: str
    target: str
    executor: str
    status: str
    prev_hash: str
    entry_hash: str # Hash of (timestamp + action_id + ... + prev_hash)

    def compute_hash(self) -> str:
        payload = f"{self.timestamp}{self.action_id}{self.action_type}{self.target}{self.executor}{self.status}{self.prev_hash}"
        return hashlib.sha256(payload.encode()).hexdigest()

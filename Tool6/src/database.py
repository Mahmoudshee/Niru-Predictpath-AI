from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import uuid
import os

# --- Pydantic Domain Models ---

class ParameterUpdate(BaseModel):
    param_name: str
    old_value: float
    new_value: float
    reason: str

class LearningEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_execution_id: str
    outcome: str
    adjustments: List[ParameterUpdate]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OversightDecision(BaseModel):
    decision_id: str
    action_id: str
    decision: str
    annotator: str
    notes: Optional[str] = None
    timestamp: datetime

# --- SQLAlchemy ORM Models ---

Base = declarative_base()

class TrustLedgerEntry(Base):
    __tablename__ = 'trust_ledger'

    hash_id = Column(String, primary_key=True)
    previous_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    actor = Column(String, nullable=False)

class ModelConfiguration(Base):
    __tablename__ = 'model_config'

    version_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Integer, default=0)

    # Core Parameters
    containment_threshold = Column(Float, default=0.6)
    disruptive_threshold = Column(Float, default=0.85)

    # Memory / Momentum State
    success_streak = Column(Integer, default=0)
    failure_streak = Column(Integer, default=0)
    trust_momentum = Column(Float, default=0.0)  # -1.0 to 1.0

    risk_weights = Column(JSON, default=dict)

class DriftSample(Base):
    __tablename__ = 'drift_samples'

    sample_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metric_name = Column(String)
    metric_value = Column(Float)
    alert_triggered = Column(Integer, default=0)

# --- Database Setup ---

# Resolve DB path relative to this file so it always lands in Tool6/data/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL6_DIR = os.path.dirname(_THIS_DIR)
_DATA_DIR = os.path.join(_TOOL6_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)

DB_URL = f"sqlite:///{os.path.join(_DATA_DIR, 'governance.db')}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

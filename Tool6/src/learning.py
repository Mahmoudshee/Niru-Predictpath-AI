import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from .database import ModelConfiguration
from .ledger import TrustLedgerSystem

class LearningEngine:
    def __init__(self, db: Session, ledger: TrustLedgerSystem):
        self.db = db
        self.ledger = ledger

    def get_active_config(self) -> ModelConfiguration:
        config = self.db.query(ModelConfiguration).filter_by(is_active=1).first()
        if not config:
            config = ModelConfiguration(
                version_id="v1.0-genesis",
                is_active=1,
                containment_threshold=0.6,
                disruptive_threshold=0.85,
                trust_momentum=0.0,
                success_streak=0,
                failure_streak=0,
                risk_weights={"T1021": 0.8, "T1046": 0.4}
            )
            self.db.add(config)
            self.db.commit()
        return config

    def process_execution_feedback(self, execution_report: Dict[str, Any]):
        current_config = self.get_active_config()
        
        # Stats
        rollbacks = 0
        successes = 0
        for ex in execution_report.get("executions", []):
            status = ex.get("final_status")
            if status == "rolled_back" or status == "failed":
                rollbacks += 1
            elif status == "success":
                successes += 1

        # --- NEW LOGIC START ---
        
        ALPHA = 0.1  # Strong Penalty
        BETA = 0.01  # Weak Reward
        DECAY = 0.85
        MIN_STREAK = 3
        
        # 1. Decay Old Momentum
        momentum = current_config.trust_momentum * DECAY
        
        # 2. Calculate Raw Delta & Streak
        raw_delta = 0.0
        new_success_streak = current_config.success_streak
        new_failure_streak = current_config.failure_streak
        
        if rollbacks > 0:
            # FAILURE DOMINANCE:
            # Reset success streak. Increase failure streak.
            new_success_streak = 0
            new_failure_streak += 1
            
            # Delta is Pure Penalty
            raw_delta = -(rollbacks * ALPHA)
            
            # Force Momentum Negative if it was positive
            if momentum > 0:
                momentum = 0 # Kill the optimism
                
        elif successes > 0:
            # SUCCESS:
            new_success_streak += 1
            new_failure_streak = 0
            
            # Dampening: If streak < MIN, reward is slashed
            effective_beta = BETA
            if new_success_streak < MIN_STREAK:
                effective_beta = BETA * 0.1 # Very slow start
            
            raw_delta = (successes * effective_beta)
            
        else:
            # Neutral / Empty report
            # Decay only
            pass

        # 3. Apply Delta
        new_momentum = momentum + raw_delta
        
        # Clamp Momentum
        new_momentum = max(-0.25, min(0.25, new_momentum))
        
        # 4. Apply to Thresholds
        # Momentum > 0 means Trust High -> Thresholds Low
        # Momentum < 0 means Trust Low -> Thresholds High
        
        new_contain = current_config.containment_threshold - new_momentum
        new_disrupt = current_config.disruptive_threshold - (new_momentum * 0.5) 
        
        # Hard Bounds
        new_contain = max(0.50, min(0.95, new_contain))
        new_disrupt = max(0.70, min(1.00, new_disrupt))
        
        # --- NEW LOGIC END ---

        # ALWAYS Generate new Version
        new_version = f"v{uuid.uuid4().hex[:8]}"
        
        # Explainability (Feedback Fix)
        human_reason = "Natural trust momentum decay."
        if rollbacks > 0: 
            human_reason = f"Trust penalty triggered by {rollbacks} execution failures/rollbacks. Security posture tightened."
        elif successes > 0: 
            human_reason = f"Trust reinforced by {successes} successful actions. Confidence thresholds relaxed."
        
        reason = f"{human_reason} (Delta={raw_delta:.4f}, Momentum={new_momentum:.4f})"
        
        new_config = ModelConfiguration(
            version_id=new_version,
            is_active=0,
            containment_threshold=round(new_contain, 4),
            disruptive_threshold=round(new_disrupt, 4),
            trust_momentum=new_momentum,
            success_streak=new_success_streak,
            failure_streak=new_failure_streak,
            risk_weights=current_config.risk_weights
        )
        
        self.db.add(new_config)
        
        self.ledger.log_event(
            event_type="LEARNING_UPDATE",
            payload={
                "old_ver": current_config.version_id,
                "new_ver": new_version,
                "changes": {
                    "containment": f"{current_config.containment_threshold} -> {new_contain}",
                },
                "reason": reason
            },
            actor="LearningEngine"
        )
        
        current_config.is_active = 0
        new_config.is_active = 1
        self.db.commit()
        return new_config

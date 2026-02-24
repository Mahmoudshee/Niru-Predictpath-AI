import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from .database import ModelConfiguration, DriftSample
from .ledger import TrustLedgerSystem

from .vuln import VulnManager


class LearningEngine:
    def __init__(self, db: Session, ledger: TrustLedgerSystem):
        self.db = db
        self.ledger = ledger
        self.vuln_manager = VulnManager()

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

    def _parse_actions(self, execution_report: Dict[str, Any]) -> List[Dict]:
        """
        Supports both:
        - Old format: report["executions"] with final_status field
        - New Tool 5 script-gen format: report["actions_included"] with domain/urgency fields
        """
        # New script-gen format
        if "actions_included" in execution_report:
            actions = []
            for act in execution_report["actions_included"]:
                # Map script-gen fields to learning fields
                actions.append({
                    "final_status": "success",  # Script was generated = success
                    "action_type": act.get("action_type", "Unknown"),
                    "domain": act.get("domain", "Unknown"),
                    "urgency": act.get("urgency", "Low"),
                    "requires_approval": act.get("requires_approval", False),
                    "confidence": act.get("confidence", 0.5),
                    "target": act.get("target", "Unknown"),
                    "session_id": act.get("session_id", ""),
                    "vulnerability_details": act.get("vulnerability_details", {}),
                    "is_script_gen": True,
                })
            return actions

        # Old execution format
        return execution_report.get("executions", [])

    def _record_drift_sample(self, metric_name: str, metric_value: float, alert: bool = False):
        """Persist a drift sample to the database for trend analysis."""
        sample = DriftSample(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            metric_value=metric_value,
            alert_triggered=1 if alert else 0,
        )
        self.db.add(sample)
        # Don't commit here — caller will commit after all changes

    def process_execution_feedback(self, execution_report: Dict[str, Any]) -> ModelConfiguration:
        current_config = self.get_active_config()

        actions = self._parse_actions(execution_report)
        is_script_gen = execution_report.get("script_filename") is not None

        rollbacks = 0
        successes = 0
        kev_successes = 0
        kev_failures = 0
        high_urgency_count = 0
        approval_required_count = 0
        domains_covered = set()
        action_types = []

        for ex in actions:
            status = ex.get("final_status")
            v_details = ex.get("vulnerability_details", {})
            is_kev = v_details.get("is_kev", False)
            urgency = ex.get("urgency", "Low")
            domain = ex.get("domain", "Unknown")

            if domain:
                domains_covered.add(domain)
            if ex.get("action_type"):
                action_types.append(ex["action_type"])
            if ex.get("requires_approval"):
                approval_required_count += 1
            if urgency in ("Critical", "High"):
                high_urgency_count += 1

            if status in ("rolled_back", "failed"):
                rollbacks += 1
                if is_kev:
                    kev_failures += 1
            elif status == "success":
                successes += 1
                if is_kev:
                    kev_successes += 1

        # For script-gen reports, treat all actions as successes
        if is_script_gen and successes == 0:
            successes = len(actions)

        ALPHA = 0.1
        BETA = 0.01

        raw_delta = 0.0
        new_success_streak = current_config.success_streak
        new_failure_streak = current_config.failure_streak

        if rollbacks > 0:
            new_success_streak = 0
            new_failure_streak += 1
            penalty_mult = 1.0 + (1.0 * kev_failures)
            raw_delta = -(rollbacks * ALPHA * penalty_mult)

        elif successes > 0:
            new_success_streak += 1
            new_failure_streak = 0
            reward_bonus = 1.0 + (0.5 * kev_successes)
            # Boost reward for high-urgency actions handled
            if high_urgency_count > 0:
                reward_bonus += 0.1 * high_urgency_count
            raw_delta = (successes * BETA * reward_bonus)

        new_momentum = (current_config.trust_momentum * 0.85) + raw_delta
        new_momentum = max(-0.35, min(0.35, new_momentum))

        new_contain = current_config.containment_threshold - new_momentum
        new_disrupt = current_config.disruptive_threshold - (new_momentum * 0.5)

        new_contain = max(0.40, min(0.95, new_contain))
        new_disrupt = max(0.60, min(1.00, new_disrupt))

        new_version = f"v{uuid.uuid4().hex[:8]}"

        # Build human-readable narrative
        if is_script_gen:
            human_reason = (
                f"Script generated for {len(actions)} action(s) across "
                f"{', '.join(domains_covered) if domains_covered else 'unknown'} domain(s). "
            )
            if approval_required_count > 0:
                human_reason += f"{approval_required_count} action(s) flagged for manual approval. "
            if high_urgency_count > 0:
                human_reason += f"{high_urgency_count} high/critical urgency threat(s) addressed. "
            human_reason += "Trust posture updated based on script coverage."
        elif rollbacks > 0:
            human_reason = f"Penalty: {rollbacks} failure(s). Posture tightened."
            if kev_failures:
                human_reason += " (WARNING: KEV-related failure detected)"
        elif successes > 0:
            human_reason = f"Trust: {successes} success(es). Posture relaxed."
            if kev_successes:
                human_reason += " (SUCCESS: KEV vulnerability mitigated)"
        else:
            human_reason = "Natural trust momentum decay — no significant events."

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

        # ── Record drift samples for trend analysis ────────────────────
        momentum_alert = abs(new_momentum) >= 0.25
        threshold_alert = new_contain >= 0.90 or new_contain <= 0.45
        self._record_drift_sample("trust_momentum", new_momentum, alert=momentum_alert)
        self._record_drift_sample("containment_threshold", new_contain, alert=threshold_alert)
        self._record_drift_sample("disruptive_threshold", new_disrupt, alert=False)

        self.ledger.log_event(
            event_type="LEARNING_UPDATE",
            payload={
                "old_ver": current_config.version_id,
                "new_ver": new_version,
                "source": "script_gen" if is_script_gen else "execution",
                "actions_processed": len(actions),
                "domains_covered": list(domains_covered),
                "high_urgency_count": high_urgency_count,
                "approval_required": approval_required_count,
                "kev_context": {"successes": kev_successes, "failures": kev_failures},
                "reason": f"{human_reason} (Momentum={new_momentum:.4f})"
            },
            actor="LearningEngine"
        )

        current_config.is_active = 0
        new_config.is_active = 1
        self.db.commit()

        # Attach narrative to config object for display
        new_config._narrative = human_reason
        new_config._actions_processed = len(actions)
        new_config._domains_covered = list(domains_covered)
        new_config._high_urgency_count = high_urgency_count
        new_config._approval_required = approval_required_count
        new_config._action_types = action_types
        new_config._is_script_gen = is_script_gen

        return new_config

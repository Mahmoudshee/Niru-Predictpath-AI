import logging
import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from collections import defaultdict
from .domain import ResponseDecision, RecommendedAction, RejectedAction, ActionTarget, ActionJustification, RiskReduction, ConfidenceAlignment, DecisionExplainability
from .knowledge_base import ACTION_COSTS, CONFIDENCE_THRESHOLDS, TECHNIQUE_RESPONSE_MAP, RISK_REDUCTION_MAP

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Transforms probabilistic forecasts into ranked decision objects with SOC-grade logic.
    """
    def __init__(self):
        self.model_version = "v3.0-Multi-Strategy"

    def analyze_correlations(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        user_counts = defaultdict(int)
        for f in forecasts:
            sid = f.get("session_id", "")
            user_part = sid.split('_')[0] if "_" in sid else sid
            user_counts[user_part] += 1
            
        modifiers = {}
        for f in forecasts:
            sid = f.get("session_id", "")
            user_part = sid.split('_')[0] if "_" in sid else sid
            
            boost = 1.0
            reasons = []
            
            unique_count = user_counts[user_part]
            if unique_count > 1:
                boost = 1.0 + (unique_count * 0.1) 
                reasons.append(f"Principal '{user_part}' active in {unique_count} concurrent sessions")
                
            modifiers[sid] = {
                "confidence_boost": min(boost, 1.5), 
                "correlation_reason": "; ".join(reasons) if reasons else None,
                "principal_id": user_part,
                "session_count": unique_count
            }
            
        return modifiers

    def evaluate_session(self, forecast_data: Dict[str, Any], correlation_ctx: Dict[str, Any]) -> ResponseDecision:
        session_id = forecast_data.get("session_id")
        base_conf = forecast_data.get("aggregate_confidence", 0.0)
        
        # Apply Correlation Boost
        boost_mult = correlation_ctx.get("confidence_boost", 1.0)
        decision_conf = min(base_conf * boost_mult, 1.0)
        
        scenarios = forecast_data.get("predicted_scenarios", [])
        current_state = forecast_data.get("current_state", {})
        
        # 1. Identify "Threat Mass"
        primary_scenario = scenarios[0] if scenarios else None
        
        if not primary_scenario:
            return self._build_monitor_only(session_id, decision_conf, "No predicted threats found.")
            
        predicted_techs = primary_scenario.get("sequence", [])
        probability = primary_scenario.get("probability", 0.0)
        time_window = primary_scenario.get("reaction_time_window", {})
        min_time = time_window.get("min_seconds", 9999)
        
        # 2. Select Candidate Strategy (Iterative)
        target_tech = predicted_techs[0]
        strategies = TECHNIQUE_RESPONSE_MAP.get(target_tech, ["Monitor User Behavior"])
        
        final_action_type = "Monitor User Behavior"
        rejections = []
        selected_strategy = None
        
        for strat in strategies:
            required_conf = CONFIDENCE_THRESHOLDS.get(strat, 1.0)
            cost = ACTION_COSTS.get(strat, 0.0)
            rejection_reasons = []
            
            # Check Confidence
            if decision_conf < required_conf:
                rejection_reasons.append(f"Confidence ({decision_conf:.2f}) < Threshold ({required_conf})")
            
            # Check Cost/Risk Benefit
            # If Probability is low (< 30%) and Cost is high (> 0.5)
            if probability < 0.3 and cost > 0.5:
                rejection_reasons.append(f"Risk Prob ({probability:.2f}) too low for High Cost ({cost})")
                
            if not rejection_reasons:
                # We found a valid strategy!
                selected_strategy = strat
                break
            else:
                # Log rejection and try next
                rejections.append(RejectedAction(
                    candidate_action=strat,
                    rejection_reasons=rejection_reasons
                ))
        
        evaluated_action = selected_strategy if selected_strategy else "Monitor User Behavior"
        
        # 4. Determine Urgency
        urgency = "Low"
        if min_time < 300: urgency = "Critical" 
        elif min_time < 3600: urgency = "High"
        elif min_time < 14400: urgency = "Medium"
        if decision_conf < 0.35: urgency = "Low"
            
        # 5. Build Recommendation
        target_entity = "User"
        hosts = current_state.get("host_scope", [])
        
        if "Isolate" in evaluated_action or "Block" in evaluated_action:
            target_entity = "Host"
            target_id = hosts[-1] if hosts else "Unknown"
        else:
            target_entity = "User"
            target_id = correlation_ctx.get("principal_id", session_id)

        # 6. Risk Reduction
        reduction_val = RISK_REDUCTION_MAP.get(evaluated_action, 0.1)
        abs_reduction = min(probability * reduction_val, probability)
        rel_desc = f"Mitigates {reduction_val:.0%} of {target_tech} risk"

        ctx_note = correlation_ctx.get("correlation_reason")
        why_now = f"High probability ({probability:.0%}) of {target_tech} within {min_time}s."
        
        # Append correlation note to Why Now if relevant
        if ctx_note:
            why_now += f" (Escalated: {ctx_note})"

        # Logic for Action Class & Approval (Feedback Fix)
        act_class = "Containment"
        act_approval = False
        
        disruptive_keywords = ["Block", "Isolate", "Disable", "Reset", "Terminate"]
        if any(k in evaluated_action for k in disruptive_keywords):
            act_class = "Disruptive"
            act_approval = True
        
        # Also require approval if confidence is borderline (within 10% of threshold) despite passing
        # This adds an extra safety layer
        threshold = CONFIDENCE_THRESHOLDS.get(evaluated_action, 0.0)
        if threshold > 0 and (decision_conf - threshold) < 0.1:
             act_approval = True

        rec_action = RecommendedAction(
            action_type=evaluated_action,
            action_class=act_class,
            requires_approval=act_approval,
            target=ActionTarget(type=target_entity, identifier=target_id),
            recommended_within_seconds=min_time,
            justification=ActionJustification(
                predicted_scenarios=[f"{'->'.join(predicted_techs)}"],
                risk_reduction=RiskReduction(absolute=round(abs_reduction, 2), relative=rel_desc),
                time_to_impact_seconds=min_time,
                confidence_alignment=ConfidenceAlignment(
                    tool3_confidence=base_conf,
                    decision_confidence=decision_conf,
                    threshold_applied=threshold
                ),
                signal_gap_closed=f"Controls {target_tech}"
            )
        )
        
        rank_score = (decision_conf * 100) + (probability * 100) + (1000 if urgency == "Critical" else 0)
        
        return ResponseDecision(
            session_id=session_id,
            decision_confidence=round(decision_conf, 2),
            priority_rank=int(rank_score),
            urgency_level=urgency,
            recommended_actions=[rec_action],
            rejected_actions=rejections,
            model_version=self.model_version,
            decision_explainability=DecisionExplainability(
                why_now=why_now,
                why_not_later="Delay increases lateral movement window.",
                what_happens_if_ignored=f"Unmitigated Risk: {probability:.0%} chance of {target_tech} execution.",
                correlation_context=correlation_ctx.get("correlation_reason")
            )
        )

    def _build_monitor_only(self, session_id: str, conf: float, reason: str) -> ResponseDecision:
         # Same logic as before
        return ResponseDecision(
            session_id=session_id,
            decision_confidence=conf,
            priority_rank=0,
            urgency_level="Low",
            recommended_actions=[
                RecommendedAction(
                    action_type="Monitor User Behavior",
                    target=ActionTarget(type="User", identifier=session_id),
                    recommended_within_seconds=0,
                    justification=ActionJustification(
                        predicted_scenarios=[],
                        risk_reduction=RiskReduction(absolute=0.0, relative="None"),
                        confidence_alignment=ConfidenceAlignment(tool3_confidence=conf, decision_confidence=conf, threshold_applied=0.0),
                        signal_gap_closed="Baseline monitoring"
                    )
                )
            ],
            rejected_actions=[],
            model_version=self.model_version,
            decision_explainability=DecisionExplainability(
                why_now=reason,
                why_not_later="N/A",
                what_happens_if_ignored="Unknown"
            )
        )

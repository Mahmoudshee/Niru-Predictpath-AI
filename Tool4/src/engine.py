import logging
import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from collections import defaultdict
from .domain import ResponseDecision, RecommendedAction, RejectedAction, ActionTarget, ActionJustification, RiskReduction, ConfidenceAlignment, DecisionExplainability
from .knowledge_base import ACTION_COSTS, CONFIDENCE_THRESHOLDS, TECHNIQUE_RESPONSE_MAP, RISK_REDUCTION_MAP, MITIGATION_GUIDELINES
from .vuln import VulnManager

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Transforms probabilistic forecasts into ranked decision objects with SOC-grade logic.
    """
    def __init__(self):
        self.model_version = "v4.1-Vuln-Driven"
        self.vuln_manager = VulnManager()

    def analyze_correlations(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        import re
        
        # 1. Smarter Principal Extraction (Handles URLs and standard IDs)
        def get_principal(sid):
            # Extract common root from "Activity on https://domain.com/path"
            url_match = re.search(r"https?://([^/]+)", sid)
            if url_match:
                return url_match.group(1)
            return sid.split('_')[0] if "_" in sid else sid

        principal_map = defaultdict(list)
        for f in forecasts:
            sid = f.get("session_id", "")
            p_id = get_principal(sid)
            principal_map[p_id].append(f)
            
        modifiers = {}
        for p_id, p_forecasts in principal_map.items():
            session_count = len(p_forecasts)
            # Velocity Multiplier: Aggressive boost for high-frequency hits
            boost = min(1.0 + (session_count * 0.15), 1.6) 
            
            # Identify Worst-Case attributes for the group
            group_max_cvss = 0.0
            group_is_kev = False
            for f in p_forecasts:
                state = f.get("current_state", {})
                vulns = state.get("observed_vulnerabilities", [])
                v_data = self.vuln_manager.batch_lookup_cves(vulns)
                group_max_cvss = max(group_max_cvss, *[v['cvss'] for v in v_data.values()] + [0.0])
                if any(v['is_kev'] for v in v_data.values()): group_is_kev = True

            reason = f"Aggregated Campaign: {session_count} correlated sessions hit '{p_id}'"
            if group_is_kev: reason += " [Group contains KEV exploits]"

            for f in p_forecasts:
                modifiers[f.get("session_id")] = {
                    "confidence_boost": boost, 
                    "correlation_reason": reason,
                    "principal_id": p_id,
                    "session_count": session_count,
                    "group_is_kev": group_is_kev,
                    "group_max_cvss": group_max_cvss
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
        
        # --- VULNERABILITY CONTEXT (Heuristic Severity for CWEs) ---
        vulnerabilities = current_state.get("observed_vulnerabilities", [])
        vuln_data = self.vuln_manager.batch_lookup_cves(vulnerabilities)
        
        cwe_heuristic_scores = {
            "CWE-78": 9.8,  # Command Injection
            "CWE-89": 9.8,  # SQLi
            "CWE-434": 8.5, # File Upload
            "CWE-94": 9.8,  # Code Injection
            "CWE-287": 7.5, # Auth Bypass
            "CWE-20": 7.0,  # Input Validation
            "CWE-79": 6.1,  # XSS
        }
        
        cvss_list = [v['cvss'] for v in vuln_data.values()]
        for v_id in vulnerabilities:
            if v_id in cwe_heuristic_scores:
                cvss_list.append(cwe_heuristic_scores[v_id])
                
        # CORE FIX: Use Group-wide intelligence for decision making
        is_kev = correlation_ctx.get("group_is_kev", any(v['is_kev'] for v in vuln_data.values()))
        max_cvss = max(cvss_list + [correlation_ctx.get("group_max_cvss", 0.0), 0.0])
        
        # 1. Identify "Threat Mass" by evaluating ALL scenarios
        # We search for the first scenario that we can actually mitigate with sufficient confidence
        selected_strategy = None
        target_scenario = None
        rejections = []
        
        for scenario in scenarios:
            predicted_techs = scenario.get("sequence", [])
            if not predicted_techs: continue
            
            target_tech = predicted_techs[0]
            probability = scenario.get("probability", 0.0)
            strategies = TECHNIQUE_RESPONSE_MAP.get(target_tech, ["Monitor User Behavior"])
            
            for strat in strategies:
                required_conf = CONFIDENCE_THRESHOLDS.get(strat, 1.0)
                cost = ACTION_COSTS.get(strat, 0.0)
                rejection_reasons = []
                
                # URGENCY OVERRIDE: If urgency factors are high, we lower the threshold for non-disruptive containment
                is_urgent_session = is_kev or max_cvss >= 9.0
                effective_conf_threshold = required_conf
                if is_urgent_session and strat != "Monitor User Behavior":
                    effective_conf_threshold = max(0.1, required_conf - 0.2) # Be more aggressive
                
                # Apply Correlation Multiplier to Probability for evaluation
                eval_prob = probability * (1.0 + (correlation_ctx.get("session_count", 1) - 1) * 0.1)
                
                # Check Confidence
                if decision_conf < effective_conf_threshold:
                    rejection_reasons.append(f"Confidence ({decision_conf:.2f}) < Eff. Threshold ({effective_conf_threshold})")
                
                # Check Cost/Risk Benefit
                if eval_prob < 0.2 and cost > 0.6: 
                    rejection_reasons.append(f"Aggregated Risk ({eval_prob:.2f}) too low for High Cost ({cost})")
                    
                if not rejection_reasons:
                    selected_strategy = strat
                    target_scenario = scenario
                    break
                else:
                    rejections.append(RejectedAction(
                        candidate_action=strat,
                        rejection_reasons=rejection_reasons
                    ))
            
            if selected_strategy:
                break
        
        evaluated_action = selected_strategy if selected_strategy else "Monitor User Behavior"
        # Use the best scenario we found for metadata, or fall back to primary
        primary_scenario = target_scenario if target_scenario else (scenarios[0] if scenarios else None)
        
        if not primary_scenario:
             return self._build_monitor_only(session_id, decision_conf, "No predicted threats found.")

        predicted_techs = primary_scenario.get("sequence", [])
        probability = primary_scenario.get("probability", 0.0)
        target_tech = predicted_techs[0]
        time_window = primary_scenario.get("reaction_time_window", {})
        min_time = time_window.get("min_seconds", 9999)
        
        # 4. Determine Urgency
        urgency = "Low"
        if min_time < 300 or is_kev or max_cvss >= 9.0: urgency = "Critical" 
        elif min_time < 3600 or max_cvss >= 7.0: urgency = "High"
        elif min_time < 14400: urgency = "Medium"
        if decision_conf < 0.35 and not is_kev: urgency = "Low"
            
        # 5. Build Recommendation
        target_entity = "User"
        hosts = current_state.get("host_scope", [])
        
        import re
        def normalize_target(t):
            url_match = re.search(r"https?://([^/]+)", t)
            if url_match: return url_match.group(1)
            return t

        if "Isolate" in evaluated_action or "Block" in evaluated_action:
            target_entity = "Host"
            raw_target = hosts[-1] if hosts else "Unknown"
            target_id = normalize_target(raw_target)
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
        
        # KEV Auto-Action Eligibility Rule
        if is_kev and act_class == "Containment":
            act_approval = False # Force AUTO for critical KEV containment
        
        if threshold > 0 and (decision_conf - threshold) < 0.05:
             act_approval = True

        kev_reason = " [KEV ACTIVE]" if is_kev else ""
        what_ignored = f"Unmitigated Risk: {probability:.0%} chance of {target_tech} exploiting {max_cvss} CVSS vuln."

        rec_action = RecommendedAction(
            action_type=evaluated_action,
            action_class=act_class,
            requires_approval=act_approval,
            target=ActionTarget(type=target_entity, identifier=target_id),
            vulnerability_details={"is_kev": is_kev, "max_cvss": max_cvss},
            mitigation_guidelines=MITIGATION_GUIDELINES.get(evaluated_action, []),
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
                signal_gap_closed=f"Controls {target_tech}{kev_reason}"
            )
        )
        
        rank_score = (decision_conf * 100) + (probability * 100) + (2000 if is_kev else (1000 if urgency == "Critical" else 0))

        # 7. Generate Data-Driven Response Summary
        urgency_note = ""
        if is_kev:
            urgency_note = f"due to the detection of high-risk exploits (Max CVSS {max_cvss})."
        elif probability > 0.4:
            urgency_note = f"as a countermeasure to a {probability:.0%} probability threat."
        else:
            urgency_note = "to ensure defensive depth."

        decision_logic = "Automated containment" if not act_approval else "Disruptive mitigation"
        
        mentor_summ = f"{decision_logic} strategy for {session_id} has been initiated {urgency_note} "
        mentor_summ += f"The selected action, '{evaluated_action}', targets {target_entity} '{target_id}' "
        mentor_summ += f"with an estimated risk reduction of {abs_reduction:.1%} across the predicted trajectory."

        if act_approval:
            mentor_summ += " Manual authorization is required before execution due to potential service disruption."

        return ResponseDecision(
            session_id=session_id,
            decision_confidence=round(decision_conf, 2),
            priority_rank=int(rank_score),
            urgency_level=urgency,
            recommended_actions=[rec_action],
            rejected_actions=rejections,
            model_version=self.model_version,
            mentor_summary=mentor_summ,
            decision_explainability=DecisionExplainability(
                why_now=f"Vulnerability Context: Max CVSS {max_cvss}{kev_reason}. Prob ({probability:.0%}) within {min_time}s.",
                why_not_later="Delay increases lateral movement window.",
                what_happens_if_ignored=what_ignored,
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
            mentor_summary="No immediate threat detected. Continuing baseline monitoring.",
            decision_explainability=DecisionExplainability(
                why_now=reason,
                why_not_later="N/A",
                what_happens_if_ignored="Unknown"
            )
        )

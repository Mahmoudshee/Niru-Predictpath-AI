from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone
from .domain import PredictedScenario, ReactionTimeWindow, TrajectoryExplainability, PredictionSummary, CurrentState
from .knowledge_base import TRANSITION_MATRIX, TIME_PRIORS, PREREQUISITES, get_technique_name
from .vuln import VulnManager

logger = logging.getLogger(__name__)

# CWE-to-Technique progression mapping hints
CWE_MAP = {
    "CWE-798": ["T1078"],          # Hardcoded Credentials -> Valid Accounts
    "CWE-287": ["T1078", "T1110"], # Improper Authentication -> Valid Accounts / Brute Force
    "CWE-306": ["T1078"],          # Missing Authentication -> Valid Accounts
    "CWE-94":  ["T1059", "T1190"], # Injection -> Command Execution / Exploit Public Facing
    "CWE-89":  ["T1190", "T1059"], # SQL Injection -> Exploit Public Facing
    "CWE-78":  ["T1059", "T1190"], # OS Command Injection -> Command Execution
    "CWE-434": ["T1505", "T1190"], # Unrestricted File Upload -> Web Shell / Exploit
    "CWE-22":  ["T1083"],          # Path Traversal -> File/Dir Discovery
    "CWE-20":  ["T1190"],          # Improper Input Validation -> Exploit Public Facing
    "CWE-79":  ["T1190"],          # XSS -> Exploit Public Facing
    "CWE-264": ["T1078"],          # Permissions Issue -> Valid Accounts
    "CWE-693": ["T1562"],          # Protection Mechanism Failure -> Impair Defenses
    "CWE-525": ["T1046"],          # Cache Leak -> Discovery
    "CWE-615": ["T1592"],          # Comments Leak -> Information Gathering
    "CWE-1021": ["T1204"],         # Clickjacking -> User Execution
    "CWE-209": ["T1592", "T1046"], # Error Message Leak -> Discovery
    "CWE-307": ["T1110"],          # Brute Force Attempts
}

class TrajectoryEngine:
    def __init__(self):
        self.model_version = "v4.0-Vuln-Aware"
        self.vuln_manager = VulnManager()

    def predict(self, session_id: str, current_state: CurrentState, current_risk: float) -> PredictionSummary:
        # Fetch Vuln Data
        vuln_data = self.vuln_manager.batch_lookup_cves(current_state.observed_vulnerabilities)
        
        # GROUNDING: Identify techniques specifically enabled by the captured vulnerabilities
        vuln_enabled_techniques = []
        for cwe_id in current_state.observed_vulnerabilities:
            if cwe_id in CWE_MAP:
                vuln_enabled_techniques.extend(CWE_MAP[cwe_id])
        
        # Determine the "Deepest" Captured State
        # We walk the seeds, but if one seed is a prerequisite of another captured seed, we start from the deeper one.
        all_potential_seeds = list(set(current_state.observed_techniques + vuln_enabled_techniques))
        if not all_potential_seeds:
            all_potential_seeds = ["T1595"] 
            
        seeds = []
        for s in all_potential_seeds:
            is_superseded = False
            for other in all_potential_seeds:
                if s != other:
                    # If 's' is a prerequisite of 'other', 's' is superseded by deeper knowledge
                    if s in PREREQUISITES.get(other, []):
                        is_superseded = True
                        break
            if not is_superseded:
                seeds.append(s)

        # Run Traversal for each vulnerability-driven seed
        all_raw_scenarios = []
        for seed in seeds:
            # We use max_depth=3 to keep it focused on the immediate future
            scenarios = self._bfs_probabilistic_traversal(seed, current_state, vuln_data, max_depth=3)
            all_raw_scenarios.extend(scenarios)
            
        # Deduplicate by sequence to avoid "Command Interpreter" appearing twice
        unique_scenarios = {}
        for sc in all_raw_scenarios:
            seq_key = "->".join(sc.sequence)
            if seq_key not in unique_scenarios or sc.probability > unique_scenarios[seq_key].probability:
                unique_scenarios[seq_key] = sc
        
        # Sort and limit
        final_scenarios = sorted(unique_scenarios.values(), key=lambda x: x.probability, reverse=True)[:5]
        for i, s in enumerate(final_scenarios):
            s.scenario_type = "Primary" if i == 0 else ("Secondary" if i < 3 else "Opportunistic")

        # Aggregate Confidence Adjustments
        vuln_match_count = len(list(set(current_state.observed_vulnerabilities) & set(CWE_MAP.keys())))
        vuln_grounding_factor = min(vuln_match_count * 0.15, 0.45) # Max 45% based on evidence
        
        max_prob = max([p.probability for p in final_scenarios]) if final_scenarios else 0.4
        kev_count = sum(1 for v in vuln_data.values() if v['is_kev'])
        kev_boost = min(kev_count * 0.2, 0.4)
        
        # Ensure verified exploits (current_risk > 15) have a high confidence floor
        risk_floor = 0.4 if current_risk > 50 else (0.2 if current_risk > 15 else 0.0)
        
        aggregate_confidence = (max_prob * 0.25) + vuln_grounding_factor + kev_boost + risk_floor
        aggregate_confidence = round(min(aggregate_confidence, 1.0), 2)

        suppression_reason = None
        
        # DYNAMIC NARRATIVE GENERATION (High Fidelity / Data Driven)
        # Check against techniques that imply successful exploitation or high risk
        is_exploitation = any(t in ["T1190", "T1059", "T1505", "T1110"] for t in current_state.observed_techniques) or current_risk > 15
        is_recon = any(t in ["T1595", "T1592", "T1046", "T1083"] for t in current_state.observed_techniques)
        
        if aggregate_confidence > 0.7:
            prefix = f"CRITICAL ALERT: Session '{session_id}' shows a high-velocity, confirmed attack sequence. "
        elif is_exploitation:
            prefix = f"URGENT: Verified exploit patterns identified on {session_id}. Attacker has likely bypassed initial defenses. "
        elif is_recon:
            prefix = f"RECONNAISSANCE: Systematic scanning and information gathering detected on {session_id}. "
        elif aggregate_confidence > 0.3:
            prefix = f"ANOMALY: Heuristic patterns on {session_id} suggest emerging adversarial intent. "
        else:
            prefix = f"Baseline activity observed for {session_id}. "

        narrative = prefix
        # EXPLICIT LINKING: Tell user what these specific vulns enable
        enabling_vulns = [v for v in current_state.observed_vulnerabilities if v in CWE_MAP]
        if enabling_vulns:
            v_str = ", ".join(enabling_vulns[:3])
            narrative += f"The specific weaknesses identified ({v_str}) provide the technical logical bridges for the projected trajectory. "

        if kev_count > 0:
            v_list = ", ".join(current_state.observed_vulnerabilities[:2])
            narrative += f"The presence of documented exploits ({v_list}) has triggered an urgent reaction-window compression. "
        
        if final_scenarios:
            top_scenario = final_scenarios[0]
            action_name = get_technique_name(top_scenario.sequence[0])
            prob_percent = int(top_scenario.probability * 100)
            narrative += f"An attacker exploiting these vulnerabilities is projected to pivot to '{action_name}' next ({prob_percent}% probability)."
        elif not final_scenarios and aggregate_confidence > 0.2:
            narrative += "While activity is anomalous, it does not currently align with known lateral movement matrices."

        return PredictionSummary(
            session_id=session_id,
            current_state=current_state,
            predicted_scenarios=final_scenarios, 
            mentor_narrative=narrative,
            model_version=self.model_version,
            aggregate_confidence=aggregate_confidence,
            evidence_summary={"grounding": vuln_grounding_factor, "max_path_prob": max_prob, "kev_boost": kev_boost},
            suppression_reason=suppression_reason
        )

    def _bfs_probabilistic_traversal(self, start_node: str, state: CurrentState, vuln_data: Dict[str, Any], max_depth: int) -> List[PredictedScenario]:
        scenarios = []
        queue = [(start_node, [], 1.0, 0.0, 0.0)] 
        visited_paths = set()

        # Identify observed CWE abstractions for progression hints
        all_cwes = []
        for v in vuln_data.values(): all_cwes.extend(v['cwe_ids'])
        cwe_details = self.vuln_manager.batch_lookup_cwes(all_cwes)
        abstractions = [d['abstraction'] for d in cwe_details.values()]

        while queue:
            curr, path, prob, t_min, t_max = queue.pop(0)
            if len(path) > 0:
                scenarios.append(self._build_scenario(path, prob, t_min, t_max, state, vuln_data))
            if len(path) >= max_depth: continue

            for next_tech, trans_prob in TRANSITION_MATRIX.get(curr, []):
                modifier = 1.0
                dwell_mult = 1.0
                
                # --- VULNERABILITY MODIFIERS ---
                # Check if next_tech correlates to observed CWEs
                for cwe_id, techs in CWE_MAP.items():
                    if next_tech in techs and cwe_id in all_cwes:
                        modifier *= 1.4 # Boost prob if weakness matches path
                
                # KEV Impact
                if any(v['is_kev'] for v in vuln_data.values()):
                    modifier *= 1.2 # Global boost
                    dwell_mult *= 0.6 # Compress reaction window

                # Logic modifiers
                if next_tech == "T1021" and len(state.host_scope) < 2: modifier = 0.0
                if next_tech == "T1041" and "T1560" in state.observed_techniques: modifier *= 1.5

                new_prob = prob * trans_prob * modifier
                if new_prob < 0.1: continue
                
                dwell = TIME_PRIORS.get(next_tech, (60, 3600))
                new_min = t_min + (dwell[0] * dwell_mult)
                new_max = t_max + (dwell[1] * dwell_mult)
                
                new_path = path + [next_tech]
                if "-".join(new_path) not in visited_paths:
                    visited_paths.add("-".join(new_path))
                    queue.append((next_tech, new_path, new_prob, new_min, new_max))
        
        scenarios.sort(key=lambda x: x.probability, reverse=True)
        final_scenarios = scenarios[:5]
        for i, s in enumerate(final_scenarios):
            s.scenario_type = "Primary" if i == 0 else ("Secondary" if i < 3 else "Opportunistic")
        return final_scenarios

    def _build_scenario(self, sequence: List[str], prob: float, t_min: float, t_max: float, state: CurrentState, vuln_data: Dict[str, Any]) -> PredictedScenario:
        risk = "Medium"
        last_tech = sequence[-1]
        if last_tech in ["T1041", "T1486"]: risk = "Critical"
        elif last_tech in ["T1003", "T1021"]: risk = "High"
        
        pos_evidence = []
        if any(v['is_kev'] for v in vuln_data.values()):
            pos_evidence.append("Active KEV exploit detected; compressing reaction window by 40%")
        
        trigger = state.observed_techniques[-1] if state.observed_techniques else "Initial Access"
        
        # VULNERABILITY CORRELATION EVIDENCE (THE CORE "WHY")
        next_step = sequence[0]
        # Use a set to avoid duplicate evidence for multiple CWEs mapping to same tech
        matching_cwes = [cwe_id for cwe_id, techs in CWE_MAP.items() if (next_step in techs or trigger in techs) and cwe_id in state.observed_vulnerabilities]
        
        if matching_cwes:
            v_ref = ", ".join(list(set(matching_cwes))[:2])
            pos_evidence.append(f"Captured weakness {v_ref} allows an attacker to achieve {get_technique_name(next_step)}")
        else:
            pos_evidence.append(f"Causal path from {get_technique_name(trigger)}")

        if any(v['is_kev'] for v in vuln_data.values()):
            pos_evidence.append("Active KEV exploit detected; compressing reaction window by 40%")

        # HUMANIZATION
        human_seq = " -> ".join([get_technique_name(t) for t in sequence])
        
        def format_time(seconds):
            if seconds < 60: return f"{int(seconds)}s"
            return f"{int(seconds/60)}m"

        time_text = f"Window: {format_time(t_min)} to {format_time(t_max)}"

        return PredictedScenario(
            sequence=sequence,
            human_readable_sequence=human_seq,
            probability=round(min(prob, 1.0), 3),
            reaction_time_window=ReactionTimeWindow(min_seconds=int(t_min), max_seconds=int(t_max)),
            time_window_text=time_text,
            explainability=TrajectoryExplainability(
                positive_evidence=pos_evidence,
                negative_evidence=[],
                uncertainty_factors=[]
            ),
            risk_level=risk
        )

from typing import List, Optional, Dict, Any
import networkx as nx
import logging
from datetime import datetime, timezone
from .domain import PredictedScenario, ReactionTimeWindow, TrajectoryExplainability, PredictionSummary, CurrentState
from .knowledge_base import TRANSITION_MATRIX, TIME_PRIORS, PREREQUISITES, get_technique_name

logger = logging.getLogger(__name__)

class TrajectoryEngine:
    """
    Computes probabilistic future attack paths using a Markov-based approach 
    constrained by Time Priors, Session Scope, and Graph Topology.
    """
    
    def __init__(self):
        self.model_version = "v3.0-Session-Differentiated"

    def predict(self, session_id: str, current_state: CurrentState, current_risk: float) -> PredictionSummary:
        """
        Main entry point for generating forecasts.
        """
        # 1. Determine Start Node (Latest Technique)
        start_node = current_state.observed_techniques[-1] if current_state.observed_techniques else "T1078"
        
        # 2. Run Probabilistic BFS
        # We pass the full history to condition the BFS
        raw_scenarios = self._bfs_probabilistic_traversal(start_node, current_state, max_depth=3)
        
        # 3. Calculate Aggregate Confidence (Dynamic)
        # Factor 1: Data Volume (Richness)
        # 1-2 events = low confidence, 3-5 = medium, >5 = high
        vol_factor = min(len(current_state.observed_techniques) / 5.0, 1.0)
        
        # Factor 2: Graph Depth/Complexity
        depth_factor = min(current_state.graph_depth / 3.0, 1.0)
        
        # Factor 3: Max Probability Found (Certainty of outcome)
        max_prob = max([p.probability for p in raw_scenarios]) if raw_scenarios else 0.0
        
        # Weighted Score
        aggregate_confidence = (vol_factor * 0.3) + (depth_factor * 0.2) + (max_prob * 0.5)
        aggregate_confidence = round(aggregate_confidence, 2)

        # 4. Suppression Logic
        suppression_reason = None
        final_scenarios = raw_scenarios
        
        if aggregate_confidence < 0.15:
            final_scenarios = []
            suppression_reason = f"Insufficient confidence ({aggregate_confidence:.2f}). Require more events or clearer signal."
        elif not raw_scenarios:
            suppression_reason = "No known attack vectors match current state."

        return PredictionSummary(
            session_id=session_id,
            current_state=current_state,
            predicted_scenarios=final_scenarios, 
            model_version=self.model_version,
            aggregate_confidence=aggregate_confidence,
            evidence_summary={"depth_factor": depth_factor, "volume_factor": vol_factor, "top_prob": max_prob},
            suppression_reason=suppression_reason
        )

    def _bfs_probabilistic_traversal(self, start_node: str, state: CurrentState, max_depth: int) -> List[PredictedScenario]:
        scenarios = []
        queue = [(start_node, [], 1.0, 0.0, 0.0)] # curr, path, prob, t_min, t_max
        visited_paths = set()

        while queue:
            curr, path, prob, t_min, t_max = queue.pop(0)
            
            if len(path) > 0:
                scenarios.append(self._build_scenario(path, prob, t_min, t_max, state))
            
            if len(path) >= max_depth:
                continue

            transitions = TRANSITION_MATRIX.get(curr, [])
            
            for next_tech, trans_prob in transitions:
                # --- CONTEXTUAL MODIFIERS ---
                modifier = 1.0
                
                # Constraint 1: Lateral Movement (T1021)
                # Boost if multiple hosts are reachable. Penalize if stuck on one.
                if next_tech == "T1021":
                    if len(state.host_scope) < 2:
                        modifier = 0.0 # Impossible to move laterally if only 1 host is known/reachable
                    else:
                        modifier = 1.2 # Boost if multihost
                        
                # Constraint 2: Exfiltration (T1041)
                # If we have seen Data Staging (T1560) in history, boost Exfil probability
                if next_tech == "T1041":
                    if "T1560" in state.observed_techniques:
                         modifier = 1.5
                    elif "T1560" not in path:
                         modifier = 0.5

                new_prob = prob * trans_prob * modifier
                
                if new_prob < 0.1: # Prune weak paths
                    continue
                
                dwell = TIME_PRIORS.get(next_tech, (0, 3600))
                new_min = t_min + dwell[0]
                new_max = t_max + dwell[1]
                
                new_path = path + [next_tech]
                path_sig = "-".join(new_path)
                
                if path_sig not in visited_paths:
                    visited_paths.add(path_sig)
                    queue.append((next_tech, new_path, new_prob, new_min, new_max))
        
        scenarios.sort(key=lambda x: x.probability, reverse=True)
        final_scenarios = scenarios[:5]
        
        # Feedback Fix: Label Scenario Types to clarify probability distribution
        for i, s in enumerate(final_scenarios):
            if i == 0: s.scenario_type = "Primary"
            elif i < 3: s.scenario_type = "Secondary"
            else: s.scenario_type = "Opportunistic"
            
        return final_scenarios

    def _build_scenario(self, sequence: List[str], prob: float, t_min: float, t_max: float, state: CurrentState) -> PredictedScenario:
        risk = "Medium"
        last_tech = sequence[-1]
        if last_tech in ["T1041", "T1486"]: risk = "Critical"
        elif last_tech in ["T1003", "T1021"]: risk = "High"
        
        # --- CAUSAL EXPLAINABILITY ---
        pos_evidence = []
        neg_evidence = []
        uncertainties = []
        
        # 1. Historical Trigger
        trigger = state.observed_techniques[-1] if state.observed_techniques else "Initial Access"
        pos_evidence.append(f"Sequence initiated by observed {get_technique_name(trigger)} ({trigger})")
        
        # 2. History Reinforcement
        # If we predict T1046, and they already did T1078, mention it.
        # Check for Lateral Movement enablement
        if "T1021" in sequence and len(state.host_scope) > 1:
            pos_evidence.append(f"Lateral Movement (T1021) enabled by reachable hosts: {state.host_scope}")
        
        # Check for Exfil support
        if "T1041" in sequence and "T1560" in state.observed_techniques:
            pos_evidence.append("Observed Data Archiving (T1560) strongly supports imminent Exfiltration")

        return PredictedScenario(
            sequence=sequence,
            probability=round(prob, 3),
            reaction_time_window=ReactionTimeWindow(min_seconds=int(t_min), max_seconds=int(t_max)),
            explainability=TrajectoryExplainability(
                positive_evidence=pos_evidence,
                negative_evidence=neg_evidence,
                uncertainty_factors=uncertainties
            ),
            risk_level=risk
        )

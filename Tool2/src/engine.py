import networkx as nx
import logging
from typing import List, Dict, Optional
from datetime import datetime
from .domain import Session, EnrichedEvent, PathReport, PathPrediction

logger = logging.getLogger(__name__)

# Simplified Kill Chain Mapping for Anomaly Detection
KILL_CHAIN_ORDER = {
    "Reconnaissance": 1,
    "Resource Development": 2,
    "Initial Access": 3,
    "Execution": 4,
    "Persistence": 5,
    "Privilege Escalation": 6,
    "Defense Evasion": 7,
    "Credential Access": 8,
    "Discovery": 9,
    "Lateral Movement": 10,
    "Collection": 11,
    "Command and Control": 12,
    "Exfiltration": 13,
    "Impact": 14
}

MITRE_PHASE_MAP = {
    "T1078": "Initial Access", 
    "T1110": "Credential Access", 
    "T1046": "Discovery", 
    "T1021": "Lateral Movement",
    "T1003": "Credential Access", 
    "T1560": "Collection", 
    "T1041": "Exfiltration",
    "T1558": "Credential Access",
    "T1550": "Defense Evasion",
    "T1059": "Execution",
    "T1190": "Initial Access"
}

MITRE_SEVERITY_WEIGHTS = {
    "T1078": 2.0, # Valid account usage (could be normal)
    "T1110": 4.0, # Brute force
    "T1558": 8.0, # Ticket Stealing (High)
    "T1550": 8.0, # Pass the hash (High)
    "T1041": 10.0, # Exfiltration (Critical)
    "T1059": 5.0, # Command exec
    "Unknown": 1.0 
}

class GraphEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
    
    def build_and_analyze(self, session: Session) -> Optional[PathReport]:
        """
        Constructs a Directed Temporal Graph for the session and analyzes it.
        """
        self.graph.clear()
        events = sorted(session.events, key=lambda x: x.timestamp)
        
        if not events:
            return None

        # Build Graph
        for i, event in enumerate(events):
            technique = event.mitre_technique or "Unknown"
            phase = MITRE_PHASE_MAP.get(technique, "Unknown")
            
            self.graph.add_node(
                event.event_id,
                timestamp=event.timestamp,
                host=event.source_host,
                technique=technique,
                phase=phase
            )
            
            if i > 0:
                prev_event = events[i-1]
                delta_t = (event.timestamp - prev_event.timestamp).total_seconds()
                self.graph.add_edge(prev_event.event_id, event.event_id, delta_t=delta_t)

        if self.graph.number_of_edges() > 10000:
            logger.critical(f"Graph Explosion detected for session {session.session_id}! Pruning...")
            return None

        return self._compute_metrics(session)

    def _compute_metrics(self, session: Session) -> PathReport:
        # --- RISK SCORING LENS (Conditioned, not flat) ---
        base_risk = 0.0
        events = session.events
        
        # 1. MITRE Severity Accumulation
        for e in events:
            tech = e.mitre_technique or "Unknown"
            weight = MITRE_SEVERITY_WEIGHTS.get(tech, 1.0)
            
            # Weighted by Confidence
            # If AI is 90% sure it's T1558, add full weight. If 0.1, ignore.
            if e.confidence_score > 0.0:
                base_risk += weight * e.confidence_score
            else:
                # Fallback for baseline noise (min 0.5 if technique present)
                base_risk += weight * 0.1

        # 2. Velocity Multiplier (Superhuman speed)
        velocity_mult = 1.0
        if len(events) > 1:
            total_duration = (events[-1].timestamp - events[0].timestamp).total_seconds()
            avg_delta = total_duration / (len(events) - 1)
            time_span_minutes = total_duration / 60
            
            if avg_delta < 0.2: # Machine speed
                velocity_mult = 1.5
            elif time_span_minutes > 600: # Low and slow (Advanced Persist)
                velocity_mult = 1.2
        
        # 3. Blast Radius Additive
        touched_hosts = set()
        for e in events:
            if e.source_host: touched_hosts.add(e.source_host)
            if e.target_host: touched_hosts.add(e.target_host)
        
        blast_penalty = max(0, len(touched_hosts) - 2) * 1.5 # Start penalizing after 2 hosts
        
        final_score = (base_risk * velocity_mult) + blast_penalty
        
        # --- FORECASTING LENS ---
        # Get the last meaningful state
        phases = [MITRE_PHASE_MAP.get(e.mitre_technique, "Unknown") for e in events if e.mitre_technique]
        last_phase = phases[-1] if phases else "Unknown"
        
        # Probability Matrix
        next_steps_map = {
            "Initial Access": [("Discovery", 0.5), ("Execution", 0.3), ("Persistence", 0.2)],
            "Execution": [("Privilege Escalation", 0.4), ("Persistence", 0.4), ("Defense Evasion", 0.2)],
            "Credential Access": [("Lateral Movement", 0.5), ("Discovery", 0.3), ("Collection", 0.2)],
            "Discovery": [("Lateral Movement", 0.6), ("Collection", 0.3), ("Command and Control", 0.1)],
            "Lateral Movement": [("Collection", 0.5), ("Exfiltration", 0.3), ("Command and Control", 0.2)],
            "Command and Control": [("Exfiltration", 0.9), ("Impact", 0.1)],
            "Exfiltration": [("Impact", 0.9)],
            "Unknown": [("Discovery", 0.3), ("Credential Access", 0.2), ("Standard User Activity", 0.5)]
        }
        
        predictions = []
        potential_next = next_steps_map.get(last_phase, next_steps_map["Unknown"])
        
        for name, prob in potential_next:
            predictions.append(PathPrediction(next_node=name, probability=prob))
            
        return PathReport(
            session_id=session.session_id,
            root_cause_node=events[0].event_id,
            blast_radius=list(touched_hosts),
            path_anomaly_score=min(final_score, 100.0), # Normalize 0-100? Or 0-10? Let's assume 0-100 for granularity
            prediction_vector=predictions
        )

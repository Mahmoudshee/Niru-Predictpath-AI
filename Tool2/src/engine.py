import networkx as nx
import logging
from typing import List, Dict, Optional
from datetime import datetime
from .domain import Session, EnrichedEvent, PathReport, PathPrediction
from .vuln import VulnManager

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
    "T1190": "Initial Access",
    "T1562.001": "Defense Evasion",
    "T1083": "Discovery",
    "T1505": "Persistence"
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

# Heuristic Mapping: MITRE Techniques to likely CWEs
MITRE_CWE_HEURISTICS = {
    "T1190": ["CWE-20", "CWE-78", "CWE-89", "CWE-434"], # Injection / Upload
    "T1059": ["CWE-94", "CWE-77"], # Scripting / Command Injection
    "T1110": ["CWE-307", "CWE-521"], # Brute Force / Weak Password
    "T1078": ["CWE-287", "CWE-284"], # Broken Auth / Access Control
    "T1046": ["CWE-200"], # Information Exposure
    "T1021": ["CWE-285", "CWE-306"], # Auth Bypass
    "T1550": ["CWE-287"], # Use of Alt Auth Material
    "T1558": ["CWE-312", "CWE-287"], # Cleartext storage / Auth
    "T1112": ["CWE-284"], # Registry modification
}

# Heuristic Mapping: CWE to likely MITRE Techniques (for Tool 3 context)
CWE_TECH_MAP = {
    "CWE-798": "T1078",
    "CWE-287": "T1078",  # Authentication Bypass -> Valid Accounts
    "CWE-306": "T1078",  # Missing Authentication -> Valid Accounts
    "CWE-94":  "T1059",  # Code Injection -> Execution
    "CWE-89":  "T1190",  # SQLi -> Exploit
    "CWE-78":  "T1059",  # Command Injection -> Execution
    "CWE-434": "T1505",  # File Upload -> Persistence (Web Shell)
    "CWE-22":  "T1083",  # Path Traversal -> Discovery
    "CWE-20":  "T1190",  # Input Validation -> Exploit
    "CWE-79":  "T1190",  # XSS -> Exploit
    "CWE-264": "T1078",  # Permissions issue -> Valid Accounts/Access
    "CWE-693": "T1562",  # Protection Mechanism Failure -> Impair Defenses
    "CWE-525": "T1046",  # Information Leak -> Discovery
    "CWE-615": "T1592",  # Info in Comments -> Recon
    "CWE-1021": "T1204", # Clickjacking -> User Execution
    "CWE-200": "T1046",  # General Info Exposure -> Discovery
}

class GraphEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.vuln_manager = VulnManager()
    
    def build_and_analyze(self, session: Session) -> Optional[PathReport]:
        # ... (implementation remains same until _compute_metrics call) ...
        self.graph.clear()
        events = sorted(session.events, key=lambda x: x.timestamp)
        
        if not events:
            return None

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

        return self._compute_metrics(session)

    def _compute_metrics(self, session: Session) -> PathReport:
        base_risk = 0.0
        events = session.events
        
        for e in events:
            tech = e.mitre_technique or "Unknown"
            weight = MITRE_SEVERITY_WEIGHTS.get(tech, 1.0)
            if e.confidence_score > 0.0:
                base_risk += weight * e.confidence_score
            else:
                base_risk += weight * 0.1

        velocity_mult = 1.0
        if len(events) > 1:
            total_duration = (events[-1].timestamp - events[0].timestamp).total_seconds()
            avg_delta = total_duration / (len(events) - 1)
            if avg_delta < 0.2: velocity_mult = 1.5
        
        touched_hosts = set()
        for e in events:
            if e.source_host: touched_hosts.add(e.source_host)
            if e.target_host: touched_hosts.add(e.target_host)
        
        blast_penalty = max(0, len(touched_hosts) - 2) * 1.5
        final_score = (base_risk * velocity_mult) + blast_penalty

        # --- VULNERABILITY INTELLIGENCE DISCOVERY (Responsibility moved from Tool 1) ---
        all_cves = []
        discovered_explicit_cwes = []
        
        for e in events:
            # Deep Scan raw log source if available
            scan_text = e.raw_text or f"{e.event_type} {e.mitre_technique}"
            cves, cwes = self._discover_vulnerabilities(scan_text)
            
            # Enrich Event: If no technique found by Tool 1, infer it from the CWE
            if e.mitre_technique in [None, "Unknown", ""]:
                for cwe in cwes:
                    if cwe in CWE_TECH_MAP:
                        e.mitre_technique = CWE_TECH_MAP[cwe]
                        break
            
            all_cves.extend(cves)
            discovered_explicit_cwes.extend(cwes)
            
            # Incorporate any pre-discovered IDs (if any)
            all_cves.extend(e.observed_cve_ids)
            discovered_explicit_cwes.extend(e.observed_cwe_ids)
        
        vuln_data = self.vuln_manager.batch_lookup_cves(list(set(all_cves)))
        
        kev_count = sum(1 for c in vuln_data.values() if c['is_kev'])
        highest_cvss = max([c['cvss'] for c in vuln_data.values()] + [0.0])
        
        # Rule: Weight paths higher if CVE ∈ KEV or High CVSS
        if kev_count > 0:
            final_score *= (1.3 + (0.1 * kev_count))
        elif highest_cvss >= 9.0:
            final_score *= 1.2

        # Cluster by CWE Abstraction
        all_cwes = []
        for v in vuln_data.values():
            all_cwes.extend(v['cwe_ids'])
        
        # Explicit CWEs found in logs
        explicit_cwes = list(set(discovered_explicit_cwes))
        
        # PROACTIVE: Add likely CWEs based on MITRE technique
        for e in events:
            if e.mitre_technique in MITRE_CWE_HEURISTICS:
                heuristics = MITRE_CWE_HEURISTICS[e.mitre_technique]
                all_cwes.extend(heuristics)
                explicit_cwes.extend(heuristics)
        
        cwe_details = self.vuln_manager.batch_lookup_cwes(list(set(all_cwes)))
        cwe_clusters = list(set([d['abstraction'] for d in cwe_details.values() if d['abstraction'] != 'Unknown']))
        
        # Prepare Unique Techniques for Tool 3 (Preserving order for temporal pivots)
        unique_techniques = []
        seen_t = set()
        for e in events:
            if e.mitre_technique and e.mitre_technique != "Unknown" and e.mitre_technique not in seen_t:
                unique_techniques.append(e.mitre_technique)
                seen_t.add(e.mitre_technique)

        vuln_summary = []
        for cid, v in vuln_data.items():
            kb = " [KEV]" if v['is_kev'] else ""
            
            # Prioritize KEV name if available
            attack_name = v.get('kev_name')
            
            # Map CWEs to techniques for Tool 3
            for cwe_id in v.get('cwe_ids', []):
                if cwe_id in CWE_TECH_MAP:
                    t = CWE_TECH_MAP[cwe_id]
                    if t not in unique_techniques:
                        unique_techniques.append(t)

            # Fallback to CWE names
            if not attack_name and v.get('cwe_ids'):
                cwe_names = [cwe_details.get(c, {}).get('name') for c in v['cwe_ids'] if c in cwe_details]
                attack_name = ", ".join(filter(None, cwe_names))
            
            # Fallback to short description
            if not attack_name and v.get('description'):
                attack_name = v['description'].split('.')[0]
            
            # FINAL FALLBACK
            if not attack_name:
                attack_name = "Vulnerability Match"

            vuln_summary.append(f"{cid}: {attack_name} (CVSS: {v['cvss']}){kb}")

        # Add pure CWE detections (not tied to a CVE)
        cves_covered_cwes = set()
        for v in vuln_data.values():
            cves_covered_cwes.update(v.get('cwe_ids', []))
            
        for cwe_id in set(explicit_cwes):
            # Map CWEs to techniques for Tool 3
            if cwe_id in CWE_TECH_MAP:
                t = CWE_TECH_MAP[cwe_id]
                if t not in unique_techniques:
                    unique_techniques.append(t)

            if cwe_id not in cves_covered_cwes:
                cwe_info = cwe_details.get(cwe_id, {"name": "Security Policy Weakness"})
                display_name = cwe_info['name']
                if display_name == "Unknown": display_name = "Security Weakness (Research Required)"
                # USER REQUESTED FORMAT: CWE-ID: Name
                vuln_summary.append(f"{cwe_id}: {display_name}")

        # --- FALLBACK: If no explicit IDs found, use MITRE intelligence as the "Attack Pattern" ---
        if not vuln_summary:
            for tech in unique_techniques:
                tech_name = self.vuln_manager.get_mitre_name(tech)
                vuln_summary.append(f"Behavioral Detection: {tech_name} ({tech})")

        # --- FORECASTING LENS: Select DEEPEST phase reached for more realistic prediction ---
        discovered_phases = [MITRE_PHASE_MAP.get(t, "Unknown") for t in unique_techniques]
        # Sort by Kill Chain Order to find the "deepest" penetration
        last_phase = "Unknown"
        max_rank = -1
        for p in discovered_phases:
            rank = KILL_CHAIN_ORDER.get(p, 0)
            if rank > max_rank:
                max_rank = rank
                last_phase = p
        
        next_steps_map = {
            "Initial Access": [("Discovery", 0.5), ("Execution", 0.3), ("Persistence", 0.2)],
            "Execution": [("Privilege Escalation", 0.4), ("Persistence", 0.4), ("Defense Evasion", 0.2)],
            "Persistence": [("Privilege Escalation", 0.4), ("Credential Access", 0.4), ("Lateral Movement", 0.2)],
            "Privilege Escalation": [("Defense Evasion", 0.5), ("Credential Access", 0.3), ("Discovery", 0.2)],
            "Defense Evasion": [("Credential Access", 0.4), ("Discovery", 0.4), ("Lateral Movement", 0.2)],
            "Credential Access": [("Lateral Movement", 0.5), ("Discovery", 0.3), ("Collection", 0.2)],
            "Discovery": [("Lateral Movement", 0.6), ("Collection", 0.3), ("Command and Control", 0.1)],
            "Lateral Movement": [("Collection", 0.5), ("Exfiltration", 0.3), ("Command and Control", 0.2)],
            "Collection": [("Exfiltration", 0.8), ("Command and Control", 0.2)],
            "Command and Control": [("Exfiltration", 0.9), ("Impact", 0.1)],
            "Exfiltration": [("Impact", 0.9)],
            "Impact": [("Re-infection", 0.5), ("Persistence", 0.5)],
            "Unknown": [("Discovery", 0.3), ("Credential Access", 0.2), ("Standard User Activity", 0.5)]
        }
        
        predictions = []
        potential_next = next_steps_map.get(last_phase, next_steps_map["Unknown"])
        for name, prob in potential_next:
            predictions.append(PathPrediction(next_node=name, probability=prob))
            
        # Build event summary (Group counts by type for large volume handling)
        evt_counts = {}
        for e in events:
            evt_counts[e.event_type] = evt_counts.get(e.event_type, 0) + 1

        # Build tactical narrative for the analyst (Mentor Grade)
        narrative = f"Detected {len(events)} correlated events in this behavioral session. "
        if kev_count > 0:
            narrative += f"CRITICAL: Found {kev_count} vulnerabilities from the CISA Known Exploited Vulnerabilities (KEV) catalog! "
        elif highest_cvss >= 9.0:
            narrative += "ALERT: High-severity vulnerabilities detected. "
            
        if evt_counts.get("security_alert"):
            narrative += f"Analysis reveals {evt_counts['security_alert']} explicit security alerts. "
        if evt_counts.get("auth_failure"):
            narrative += f"Detected {evt_counts['auth_failure']} authentication failures suggesting brute-force attempts. "
        if evt_counts.get("system_audit"):
            narrative += "Integrity monitoring has flagged unauthorized system modifications. "
            
        # Refine Anomaly Score: Balance Technique Diversity vs Volume
        # Diversity score (Unique techniques, Max 70)
        tech_count = len(unique_techniques)
        diversity_score = min(tech_count * 10.0, 70.0)
        
        # Volume score (Logarithmic, Max 30) - prevents 15,000 events from blowing up the score
        import math
        volume_score = min(math.log(len(events) + 1, 10) * 10, 30.0)
        
        # Final Scoring (Logarithmic/Diversity)
        final_score = diversity_score + volume_score
        
        # Rule: Impact-driven escalation (KEV presence or High CVSS)
        if kev_count > 0:
            final_score = min(final_score * 1.5, 100.0)
        elif highest_cvss >= 9.0:
            final_score = min(final_score * 1.25, 95.0)

        # --- MENTOR GRADE PLAIN LANGUAGE SUMMARY ---
        business_risk = "Informational"
        if final_score > 70 or kev_count > 0: business_risk = "High"
        elif final_score > 30 or highest_cvss >= 9.0: business_risk = "Medium"
        elif final_score > 10: business_risk = "Low"

        # Simplified "Plain Answer" for non-technical users
        if kev_count > 0:
            top_attack = vuln_summary[0].split(":")[1].strip() if ":" in vuln_summary[0] else "critical vulnerabilities"
            plain_ans = f"CRITICAL: Identified known exploit attempts involving {top_attack}. Immediate containment recommended."
        elif max_rank >= 5: # Persistence or higher
            plain_ans = "URGENT: Attacker has successfully achieved persistence or internal lateral movement. Data access is likely imminent."
        elif max_rank >= 4: # Execution
            plain_ans = "ALERT: Unauthorized code execution detected. The attacker is actively running commands on your assets."
        elif evt_counts.get("security_alert"):
            plain_ans = "Unusual security patterns detected. System behavior matches known attacker techniques."
        elif final_score > 50:
            plain_ans = "Highly suspicious movement identified. Multiple high-risk vulnerabilities are being probed."
        else:
            plain_ans = "Routine system activity or reconnaissance. No immediate compromise of core logic detected."

        return PathReport(
            session_id=session.session_id,
            root_cause_node=events[0].event_id,
            blast_radius=list(touched_hosts),
            path_anomaly_score=round(min(final_score, 100.0), 2),
            prediction_vector=predictions,
            vulnerability_summary=vuln_summary,
            observed_techniques=list(unique_techniques),
            cwe_clusters=cwe_clusters,
            event_summary=evt_counts,
            tactical_narrative=narrative,
            plain_language_summary=plain_ans,
            business_risk_level=business_risk
        )

    def _discover_vulnerabilities(self, text: str) -> tuple[list[str], list[str]]:
        import re
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        cwe_pattern = r'CWE-\d{1,5}'
        
        cves = list(set(re.findall(cve_pattern, text, re.I)))
        cwes = list(set(re.findall(cwe_pattern, text, re.I)))
        
        # Structural Discovery: Find "cweid": "693" or "cwe_id": 693 in stringified logs
        # This is critical for ZAP/Burp/Wazuh JSON data
        structural_cwe_pattern = r'[\'"]cwe_?id[\'"]:\s*[\'"]?(\d+)[\'"]?'
        struct_matches = re.findall(structural_cwe_pattern, text, re.I)
        for m in struct_matches:
            cwe_id = f"CWE-{m}"
            if cwe_id not in cwes:
                cwes.append(cwe_id)
        
        return cves, cwes

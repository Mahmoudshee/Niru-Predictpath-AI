"""
Tool 6 - Full-Chain Audit Report Generator
Consolidates REAL data from Tools 1-5 into a professional PDF.
Zero mock / static data - every section is sourced from actual pipeline output.
"""
import os
from datetime import datetime
from fpdf import FPDF
from typing import List, Dict, Any, Optional


class AuditReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(self,
                     tool3_data: List[Dict],
                     tool4_data: List[Dict],
                     tool5_data: Dict,
                     tool6_config: Any,
                     tool1_data: Optional[Dict] = None,
                     tool2_data: Optional[List[Dict]] = None) -> str:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = "PredictPath_Audit_Report_{}.pdf".format(timestamp)
        filepath  = os.path.join(self.output_dir, filename)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Cover
        pdf.add_page()
        pdf.set_fill_color(10, 25, 41)
        pdf.rect(0, 0, 210, 70, "F")
        pdf.set_y(12)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(0, 195, 255)
        pdf.cell(0, 12, "PREDICTPATH AI", align="C", ln=True)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, "Full-Chain Cyber Security Audit Report", align="C", ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 6, "Generated: {}".format(datetime.now().strftime('%B %d, %Y %H:%M:%S UTC')), align="C", ln=True)
        pdf.set_y(57)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, "CONFIDENTIAL - SOC AUDIT DOCUMENTATION", align="C", ln=True)

        # Pull Tool 1 data
        t1       = tool1_data or {}
        intel    = t1.get("intelligence", {})
        src_file = os.path.basename(t1.get("source_file", "Unknown"))
        t1_ev    = t1.get("success", 0)
        t1_fail  = t1.get("failed", 0)
        t1_mitre = intel.get("mitre_breakdown", {})
        t1_sev   = intel.get("severity_breakdown", {})
        t1_cvss  = intel.get("cve_ids_observed", [])
        t2       = tool2_data or []
        act_list = tool5_data.get("actions_included", [])
        script_fn= self._s(str(tool5_data.get("script_filename", "N/A")))
        guide_fn = self._s(str(tool5_data.get("guideline_filename", "N/A")))

        t3_cnt   = len(tool3_data)
        t4_cnt   = sum(len(d.get("recommended_actions", [])) for d in tool4_data)

        # Section 1: Executive Summary
        pdf.set_y(75)
        pdf.set_text_color(0, 0, 0)
        self._sec(pdf, "1. EXECUTIVE SUMMARY")
        pdf.set_font("Helvetica", "", 10)
        self._mc(pdf, 6,
            "Full threat detection and response lifecycle against log source '{}'. "
            "Tool 1 ingested {} events ({} rejected), identifying {} MITRE ATT&CK technique(s). "
            "Tool 2 reconstructed {} behavioral session(s). "
            "Tool 3 generated {} attack trajectory forecast(s). "
            "Tool 4 derived {} targeted remediation action(s). "
            "Tool 6 updated the governance trust model and audit ledger.".format(
                self._s(src_file), t1_ev, t1_fail, len(t1_mitre),
                len(t2), t3_cnt, t4_cnt
            )
        )

        # Section 2: Tool 1
        self._sec(pdf, "2. TOOL 1 - EVENT INGESTION & INTELLIGENCE")
        self._kv(pdf, "Log Source",     self._s(src_file))
        self._kv(pdf, "Ingested",       str(t1_ev))
        self._kv(pdf, "Rejected",       str(t1_fail))
        self._kv(pdf, "Timestamp",      self._s(str(t1.get("timestamp", "N/A"))))
        self._kv(pdf, "Output Dir",     self._s(str(t1.get("output_dir", "N/A"))))

        if t1_mitre:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "MITRE ATT&CK Techniques Detected:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for tech, cnt in t1_mitre.items():
                pdf.cell(0, 5, "  {}  -  {} event(s)".format(self._s(tech), cnt), ln=True)

        if t1_sev:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "Severity Distribution:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for sev, cnt in t1_sev.items():
                pdf.cell(0, 5, "  {:<12}  {} event(s)".format(sev.upper(), cnt), ln=True)

        top_hosts = intel.get("top_hosts", {})
        if top_hosts:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "Top Observed Hosts:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for host, cnt in list(top_hosts.items())[:5]:
                pdf.cell(0, 5, "  {}  -  {} event(s)".format(self._s(host), cnt), ln=True)

        if t1_cvss:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "CVE IDs Observed:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            self._mc(pdf, 5, "  " + self._s(", ".join(t1_cvss[:20])))

        # Section 3: Tool 2
        self._pg(pdf, 60)
        self._sec(pdf, "3. TOOL 2 - BEHAVIORAL SESSION RECONSTRUCTION")
        if not t2:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, "No sessions produced by Tool 2.", ln=True)
        else:
            self._kv(pdf, "Total Sessions", str(len(t2)))
            for i, sess in enumerate(t2[:10], 1):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 9)
                s_id  = self._s(str(sess.get("session_id", "Session-{}".format(i))))
                score = sess.get("path_anomaly_score", 0.0)
                risk  = self._s(sess.get("business_risk_level", "Unknown"))
                blast = [self._s(b) for b in sess.get("blast_radius", [])]
                summ  = self._s(sess.get("plain_language_summary", ""))
                pdf.cell(0, 6, "  Session: {}".format(s_id), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, "    Risk: {}   Anomaly Score: {:.2f}".format(risk, score), ln=True)
                if blast:
                    pdf.cell(0, 5, "    Blast Radius: {}".format(", ".join(blast[:5])), ln=True)
                if summ:
                    self._mc(pdf, 5, "    Summary: {}".format(summ))

        # Section 4: Tool 3
        self._pg(pdf, 60)
        self._sec(pdf, "4. TOOL 3 - PREDICTIVE ATTACK TRAJECTORY")
        if not tool3_data:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, "No forecasts produced by Tool 3.", ln=True)
        else:
            for sess in tool3_data:
                s_id  = self._s(str(sess.get("session_id", "Unknown")))
                state = sess.get("current_state", {})
                techs = [self._s(t) for t in state.get("observed_techniques", [])]
                vulns = [self._s(v) for v in state.get("observed_vulnerabilities", [])]
                hosts = [self._s(h) for h in state.get("host_scope", [])]
                conf  = sess.get("aggregate_confidence", 0.0)
                narr  = self._s(sess.get("mentor_narrative", ""))
                scens = sess.get("predicted_scenarios", [])
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 6, "  Session: {}".format(s_id), ln=True)
                pdf.set_font("Helvetica", "", 9)
                self._mc(pdf, 5, "    Techniques: {}".format(", ".join(techs) or "None"))
                self._mc(pdf, 5, "    Host Scope: {}".format(", ".join(hosts) or "None"))
                self._mc(pdf, 5, "    Vulnerabilities: {}".format(", ".join(vulns) or "None identified"))
                self._mc(pdf, 5, "    Model Confidence: {:.0%}".format(conf))
                if narr:
                    self._mc(pdf, 5, "    Narrative: {}".format(narr))
                if scens:
                    pdf.ln(1)
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(0, 5, "    Projected Attack Scenarios:", ln=True)
                    pdf.set_font("Helvetica", "", 8)
                    for sc in scens[:3]:
                        prob = sc.get("probability", 0.0)
                        rl   = self._s(str(sc.get("risk_level", "Unknown")))
                        seq  = sc.get("human_readable_sequence", sc.get("sequence", []))
                        if isinstance(seq, list):
                            seq = " -> ".join([self._s(s) for s in seq])
                        else:
                            seq = self._s(str(seq))
                        self._mc(pdf, 4, "      [{}] {:.0%} probability - {}".format(rl, prob, seq))
                pdf.ln(3)

        # Section 5: Tool 4
        self._pg(pdf, 60)
        self._sec(pdf, "5. TOOL 4 - ADAPTIVE RESPONSE DECISIONS")
        if not tool4_data:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, "No response decisions produced by Tool 4.", ln=True)
        else:
            for i, dec in enumerate(tool4_data, 1):
                s_id = self._s(str(dec.get("session_id", "Unknown")))
                urg  = self._s(str(dec.get("urgency_level", "N/A")))
                conf = dec.get("decision_confidence", 0.0)
                ment = self._s(dec.get("mentor_summary", ""))
                acts = dec.get("recommended_actions", [])
                rejs = dec.get("rejected_actions", [])
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 6, "  Decision {}: {}".format(i, s_id), ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, "    Urgency: {}   Confidence: {:.0%}".format(urg, conf), ln=True)
                if ment:
                    self._mc(pdf, 5, "    Strategy: {}".format(ment))
                for act in acts:
                    at  = self._s(act.get("action_type", "Unknown"))
                    tgt = self._s(act.get("target", {}).get("identifier", "Unknown"))
                    rap = act.get("requires_approval", False)
                    gs  = act.get("mitigation_guidelines", [])
                    rr  = act.get("justification", {}).get("risk_reduction", {}).get("absolute", 0.0)
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(0, 5, "    -> {} on [{}]".format(at, tgt), ln=True)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(0, 4, "       Risk Reduction: -{:.0%}   Approval: {}".format(rr, "YES" if rap else "No"), ln=True)
                    for g in gs[:3]:
                        self._mc(pdf, 4, "       * {}".format(self._s(g)))
                for r in rejs[:2]:
                    pdf.set_font("Helvetica", "I", 8)
                    ca  = self._s(str(r.get("candidate_action", "")))
                    rea = self._s(str((r.get("rejection_reasons") or [""])[0]))
                    pdf.cell(0, 4, "    X Rejected: {} - {}".format(ca, rea), ln=True)
                pdf.ln(3)

        # Section 6: Tool 5
        self._pg(pdf, 60)
        self._sec(pdf, "6. TOOL 5 - REMEDIATION PACKAGE")
        self._kv(pdf, "Script File",       script_fn)
        self._kv(pdf, "Guideline File",    guide_fn)
        self._kv(pdf, "Generated At",      self._s(str(tool5_data.get("generated_at", "N/A"))))
        self._kv(pdf, "Total Actions",     str(tool5_data.get("total_actions", 0)))
        self._kv(pdf, "Requires Approval", str(tool5_data.get("staged_count", 0)))
        if act_list:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "Actions Embedded in Script:", ln=True)
            for act in act_list:
                at  = self._s(str(act.get("action_type", "Unknown")))
                tgt = self._s(str(act.get("target", "Unknown")))
                dom = self._s(str(act.get("domain", "General")))
                urg = self._s(str(act.get("urgency", "N/A")))
                sid = self._s(str(act.get("session_id", "Unknown")))
                gs  = act.get("mitigation_guidelines", [])
                pdf.set_font("Helvetica", "", 9)
                self._mc(pdf, 5, "  [{}] {}  ->  Target: {}  Session: {}  Urgency: {}".format(
                    dom, at, tgt, sid, urg))
                for g in gs[:2]:
                    pdf.set_font("Helvetica", "I", 8)
                    self._mc(pdf, 4, "    * {}".format(self._s(g)))

        # Section 7: Tool 6
        self._pg(pdf, 70)
        self._sec(pdf, "7. TOOL 6 - GOVERNANCE & TRUST POSTURE")
        self._kv(pdf, "Active Model Version",  self._s(tool6_config.version_id))
        self._kv(pdf, "Containment Threshold",
                 "{:.4f} ({:.1f}%)".format(tool6_config.containment_threshold,
                                            tool6_config.containment_threshold * 100))
        self._kv(pdf, "Disruptive Threshold",
                 "{:.4f} ({:.1f}%)".format(tool6_config.disruptive_threshold,
                                            tool6_config.disruptive_threshold * 100))
        self._kv(pdf, "Trust Momentum",  "{:+.4f}".format(tool6_config.trust_momentum))
        self._kv(pdf, "Success Streak",  str(tool6_config.success_streak))
        self._kv(pdf, "Failure Streak",  str(tool6_config.failure_streak))
        trend = ("Relaxing (Adapting)"    if tool6_config.trust_momentum >  0.001 else
                 "Tightening (Hardening)" if tool6_config.trust_momentum < -0.001 else
                 "Stable")
        self._kv(pdf, "Trust Trend", trend)

        # Section 8: Key Takeaways
        self._pg(pdf, 60)
        self._sec(pdf, "8. KEY SECURITY TAKEAWAYS")
        mitre_str = self._s(", ".join(t1_mitre.keys()) if t1_mitre else "None")
        high_ev   = t1_sev.get("high", 0) + t1_sev.get("critical", 0)
        cve_cnt   = len(t1_cvss)
        act_types = list(set(self._s(str(a.get("action_type", ""))) for a in act_list))
        takeaways = [
            "1. LOG ANALYSIS: '{}' yielded {} events. {} high/critical severity detected.".format(
                self._s(src_file), t1_ev, high_ev),
            "2. ATTACK TECHNIQUES: {} MITRE ATT&CK technique(s) identified - {}.".format(
                len(t1_mitre), mitre_str),
            "3. CVE INTELLIGENCE: {} CVE identifier(s) observed from the VulnIntel database.".format(cve_cnt),
            "4. SESSION ANALYSIS: {} session(s) reconstructed by Tool 2. {} trajectory forecast(s) by Tool 3.".format(
                len(t2), t3_cnt),
            "5. RESPONSE ACTIONS: {} targeted action(s) issued. Actions: {}.".format(
                t4_cnt, self._s(", ".join(act_types[:4]) or "None")),
            "6. REMEDIATION: Script '{}' generated - {} action(s), {} require approval.".format(
                script_fn, tool5_data.get("total_actions", 0), tool5_data.get("staged_count", 0)),
            "7. TRUST STATE: '{}' - success streak {}, containment at {:.1f}%.".format(
                trend, tool6_config.success_streak, tool6_config.containment_threshold * 100),
        ]
        pdf.set_font("Helvetica", "", 9)
        for t in takeaways:
            self._mc(pdf, 6, t)
            pdf.ln(1)

        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "End of Report - PredictPath AI Full-Chain Audit - CONFIDENTIAL", align="R")

        pdf.output(filepath)
        return filepath

    # Helpers
    def _mc(self, pdf, h: int, txt: str):
        """Safe multi_cell wrapper that ensures cursor sits at left margin before and after."""
        # Force X back to margin just in case. FPDF's LMARGIN is 10 unless margin set differently.
        # We set margin=15 in setup.
        pdf.set_x(15)
        pdf.multi_cell(0, h, txt)
        pdf.set_x(15)

    def _sec(self, pdf, title: str):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(10, 25, 41)
        pdf.set_text_color(0, 195, 255)
        pdf.cell(0, 9, "  " + self._s(title), ln=True, fill=True)
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)

    def _kv(self, pdf, key: str, value: str):
        safe_val = self._s(str(value or "N/A"))
        if len(safe_val) > 70 and " " not in safe_val:
            safe_val = safe_val[:35] + "... " + safe_val[-30:]
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "  {}:".format(key), ln=True, border=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(15)
        pdf.multi_cell(0, 5, safe_val)

    def _pg(self, pdf, min_space: int):
        if pdf.get_y() > 297 - min_space:
            pdf.add_page()

    def _add_page_if_needed(self, pdf, min_space: int):
        self._pg(pdf, min_space)

    @staticmethod
    def _s(text) -> str:
        """Sanitize text to Latin-1 safe string for FPDF Helvetica."""
        if not isinstance(text, str):
            text = str(text)
        subs = {
            '\u2014': '-', '\u2013': '-', '\u2012': '-',
            '\u2192': '->', '\u2190': '<-', '\u21d2': '=>',
            '\u2714': 'v',  '\u2718': 'x', '\u2713': 'v',
            '\u26a0': '!',  '\u2705': 'OK', '\u274c': 'X',
            '\u2265': '>=', '\u2264': '<=', '\u2260': '!=',
            '\u25cf': '*',  '\u2022': '*',  '\u00b7': '*',
            '\u2019': "'",  '\u2018': "'",  '\u201c': '"', '\u201d': '"',
        }
        for src, dst in subs.items():
            text = text.replace(src, dst)
        return text.encode('latin-1', errors='replace').decode('latin-1')

import os
import json
from datetime import datetime
from fpdf import FPDF
from typing import List, Dict, Any

class AuditReportGenerator:
    """
    Tool 6 — Strategic Audit & Compliance Report Generator.
    Consolidates data from Tools 2-6 into a professional PDF document.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(self, 
                     tool3_data: List[Dict], 
                     tool4_data: List[Dict], 
                     tool5_data: Dict, 
                     tool6_config: Any) -> str:
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PredictPath_Audit_Report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- PAGE 1: HEADER BANNER (Compact) ---
        pdf.add_page()
        
        # Dark Blue Header Background
        pdf.set_fill_color(10, 25, 41)
        pdf.rect(0, 0, 210, 60, 'F') # Compact 60mm header banner
        
        pdf.set_y(10)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(0, 195, 255) # Cyan
        pdf.cell(0, 10, "PREDICTPATH AI", align="C", ln=True)
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "Cyber Security Strategic Audit Report", align="C", ln=True)
        
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M:%S UTC')}", align="C", ln=True)
        
        pdf.set_y(45)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, "CONFIDENTIAL - SOC AUDIT DOCUMENTATION", align="C", ln=True)

        # --- CONTENT STARTS IMMEDIATELY ---
        pdf.set_y(65)
        pdf.set_text_color(0, 0, 0) # Reset content to black
        self._add_header(pdf, "1. EXECUTIVE SUMMARY")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, (
            "This report summarizes a comprehensive cyber defense lifecycle conducted by the PredictPath AI suite. "
            "The analysis covers threat identification (Tool 2/3), strategic response planning (Tool 4), "
            "automated remediation generation (Tool 5), and governance oversight (Tool 6). "
            "All identified high-probability threats have been processed through the mitigation engine."
        ))
        
        # --- THREAT ANALYSIS (TOOL 2/3) ---
        self._add_header(pdf, "2. THREAT ANALYSIS & FORECASTING")
        for session in tool3_data:
            sid = session.get("session_id", "Unknown")
            state = session.get("current_state", {})
            vulns = state.get("observed_vulnerabilities", [])
            scenarios = session.get("scenarios", [])
            
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"Analysis Target: {sid}", ln=True)
            
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, f"Captured Weaknesses: {', '.join(vulns) if vulns else 'None Identified'}", ln=True)
            
            if scenarios:
                pdf.set_font("Helvetica", "I", 9)
                primary = scenarios[0]
                prob = primary.get("probability", 0.0)
                techs = primary.get("sequence", [])
                pdf.multi_cell(0, 5, f"PROJECTED TRAJECTORY: {prob*100:.0%}-Confidence path reaching {', '.join(techs[:3])}...")
            
            pdf.ln(3)

        # --- MITIGATION STRATEGY (TOOL 4) ---
        self._add_header(pdf, "3. RECOMMENDED MITIGATION STRATEGIES")
        for decision in tool4_data:
            actions = decision.get("recommended_actions", [])
            for act in actions:
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(25, 6, f"ACTION:", border=0)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 6, f"{act.get('action_type')} on {act.get('target', {}).get('identifier')}", ln=True)
                
                pdf.set_font("Helvetica", "I", 8)
                guidelines = act.get("mitigation_guidelines", [])
                if guidelines:
                    pdf.cell(10, 4, "")
                    pdf.multi_cell(0, 4, f"Tactical Steps: " + " | ".join(guidelines))
                pdf.ln(1)

        # --- IMPLEMENTATION & REMEDIATION (TOOL 5) ---
        self._add_header(pdf, "4. REMEDIATION IMPLEMENTATION")
        script_file = tool5_data.get("script_filename", "N/A")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, f"Generated Remediation Package:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"Final Artifact: {script_file}", ln=True)
        pdf.cell(0, 6, f"Status: Context-Aware PowerShell Script & Tactical Guideline Generated.", ln=True)

        # --- GOVERNANCE & KEY TAKEAWAYS (TOOL 6) ---
        self._add_page_if_needed(pdf, 60)
        self._add_header(pdf, "5. GOVERNANCE POSTURE & TAKEAWAYS")
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "System Trust State:", ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, f"Active Model Version: {tool6_config.version_id}", ln=True)
        pdf.cell(0, 6, f"Containment Threshold: {tool6_config.containment_threshold*100:.1f}%", ln=True)
        
        # Calculate dynamic stats for takeaways
        total_vulns = sum([len(s.get("current_state", {}).get("observed_vulnerabilities", [])) for s in tool3_data])
        total_actions = len(tool5_data.get("actions_included", [])) or len(tool5_data.get("executions", []))
        action_types = list(set([a.get("action_type") for a in (tool5_data.get("actions_included", []) + tool5_data.get("executions", []))]))
        
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Key Security Takeaways:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        
        takeaways = [
            f"1. Attack Surface: Identified {total_vulns} distinct vulnerability matches across the analysis targets.",
            f"2. Defense Response: Generated {total_actions} validated remediation actions covering {', '.join(action_types[:3])}." if action_types else "2. Defense Response: No active remediation actions were required for this session.",
            f"3. Operational Status: Remediation package '{os.path.basename(script_file)}' is staged for SOC deployment.",
            f"4. Continuous Monitoring: System trust is {'relaxing' if tool6_config.trust_momentum > 0 else 'tightening'} based on a success streak of {tool6_config.success_streak} sessions."
        ]
        
        for take in takeaways:
            pdf.multi_cell(0, 5, take)
            pdf.ln(1)

        # --- FOOTER ---
        pdf.set_y(-25)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "End of Strategic Audit Report - PredictPath AI Governance Engine", align="R")

        pdf.output(filepath)
        return filepath

    def _add_header(self, pdf, title):
        pdf.ln(5) # Reduced from 10
        pdf.set_font("Helvetica", "B", 11) # Reduced from 14
        pdf.set_fill_color(230, 245, 255) # Light Blue Background
        pdf.set_text_color(10, 25, 41) # Dark Blue Text
        pdf.cell(0, 8, f"  {title}", ln=True, fill=True) # Reduced height from 10 to 8
        pdf.ln(3) # Reduced from 5
        pdf.set_text_color(0, 0, 0) # Reset to black

    def _add_page_if_needed(self, pdf, min_space):
        if pdf.get_y() > 297 - min_space:
            pdf.add_page()

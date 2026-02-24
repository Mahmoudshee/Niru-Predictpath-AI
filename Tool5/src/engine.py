import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from .adapters import build_script_block, classify_domain, NETWORK_ACTIONS, ENDPOINT_ACTIONS

logger = logging.getLogger(__name__)

DEPLOYMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "deployments")


class ScriptGeneratorEngine:
    """
    Tool 5 — Remediation Script Generator.
    Reads Tool 4's response_plan.json and produces a single, downloadable
    PowerShell (.ps1) remediation script. No commands are executed automatically.
    """

    def __init__(self):
        os.makedirs(DEPLOYMENTS_DIR, exist_ok=True)

    def generate(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entry point. Returns a report dict with:
          - script_path: absolute path to the generated .ps1 file
          - actions_included: list of action summaries
          - network_count / endpoint_count: domain breakdown
          - staged_count: actions requiring manual approval (included but flagged)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        script_filename = f"PredictPath_Remediation_{timestamp}.ps1"
        script_path = os.path.abspath(os.path.join(DEPLOYMENTS_DIR, script_filename))

        network_blocks: List[str] = []
        endpoint_blocks: List[str] = []
        web_blocks: List[str] = []
        general_blocks: List[str] = []
        guideline_markdown: List[str] = self._build_guideline_header(timestamp)
        actions_included = []
        staged_count = 0

        for decision in decisions:
            session_id = decision.get("session_id", "unknown")
            confidence = decision.get("decision_confidence", 0.0)
            urgency = decision.get("urgency_level", "Unknown")
            mentor_summary = decision.get("mentor_summary", "")

            for action in decision.get("recommended_actions", []):
                action_type = action.get("action_type", "")
                target_info = action.get("target", {})
                target_id = target_info.get("identifier", "unknown")
                requires_approval = action.get("requires_approval", False)
                vuln_details = action.get("vulnerability_details", {})
                guidelines = action.get("mitigation_guidelines", [])
                domain = classify_domain(action_type)

                if requires_approval:
                    staged_count += 1

                # Build the script block lines
                lines = build_script_block(action_type, target_id, session_id, vuln_details, guidelines)

                # Add approval warning header if needed
                if requires_approval:
                    lines = [
                        f"# ⚠️  APPROVAL REQUIRED — This action was flagged by Tool 4 as potentially disruptive.",
                        f"# Review carefully before running. Confidence: {confidence:.0%} | Urgency: {urgency}",
                    ] + lines

                # Populate Markdown Guideline
                guideline_markdown.extend(self._build_action_markdown(action, session_id, urgency))

                # Route to correct section
                if domain == "Network":
                    network_blocks.extend(lines)
                elif domain == "Endpoint":
                    endpoint_blocks.extend(lines)
                elif domain == "Web":
                    web_blocks.extend(lines)
                else:
                    general_blocks.extend(lines)

                actions_included.append({
                    "session_id": session_id,
                    "action_type": action_type,
                    "target": target_id,
                    "domain": domain,
                    "requires_approval": requires_approval,
                    "urgency": urgency,
                    "confidence": confidence,
                    "mentor_context": mentor_summary,
                    "mitigation_guidelines": guidelines,
                })

        # ── Assemble the master script ──────────────────────────────────────
        script_lines = self._build_header(timestamp, len(actions_included), staged_count)

        if network_blocks:
            script_lines += ["", "#" + "=" * 70, "# SECTION 1: NETWORK SECURITY MITIGATIONS", "#" + "=" * 70, ""] + network_blocks

        if endpoint_blocks:
            script_lines += ["", "#" + "=" * 70, "# SECTION 2: ENDPOINT SECURITY MITIGATIONS", "#" + "=" * 70, ""] + endpoint_blocks

        if web_blocks:
            script_lines += [
                "",
                "#" + "=" * 70,
                "# SECTION 3: WEB & CLOUD SECURITY MITIGATIONS",
                "# NOTE: These actions require manual console steps.",
                "# See Tactical_Remediation_Guideline.md for details.",
                "#" + "=" * 70,
                "",
            ] + web_blocks

        if general_blocks:
            script_lines += ["", "#" + "=" * 70, "# SECTION 4: GENERAL / MANUAL REVIEW", "#" + "=" * 70, ""] + general_blocks

        script_lines += self._build_footer()

        # ── Write to disk ────────────────────────────────────────────────────
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script_lines))

        guideline_filename = f"Tactical_Remediation_Guideline_{timestamp}.md"
        guideline_path = os.path.abspath(os.path.join(DEPLOYMENTS_DIR, guideline_filename))
        with open(guideline_path, "w", encoding="utf-8") as f:
            f.write("\n".join(guideline_markdown))

        logger.info(f"Remediation script written to: {script_path}")
        logger.info(f"Remediation guideline written to: {guideline_path}")

        return {
            "script_path": script_path,
            "script_filename": script_filename,
            "guideline_path": guideline_path,
            "guideline_filename": guideline_filename,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_actions": len(actions_included),
            "network_count": len(network_blocks) > 0,
            "endpoint_count": len(endpoint_blocks) > 0,
            "web_count": len(web_blocks) > 0,
            "staged_count": staged_count,
            "actions_included": actions_included,
        }

    # ── Private helpers ──────────────────────────────────────────────────────

    def _build_guideline_header(self, timestamp: str) -> List[str]:
        return [
            f"# 🛡️ Tactical Remediation Guideline",
            f"*Generated by PredictPath AI on {timestamp} UTC*",
            "",
            "## Executive Summary",
            "This document provides step-by-step manual remediation instructions for security threats that cannot be fully automated via script (e.g., Web App vulnerabilities, Cloud misconfigurations, and complex forensic tasks).",
            "",
            "---",
            ""
        ]

    def _build_action_markdown(self, action: Dict[str, Any], session_id: str, urgency: str) -> List[str]:
        action_type = action.get("action_type")
        target = action.get("target", {}).get("identifier")
        guidelines = action.get("mitigation_guidelines", [])
        urg_color = "🔴" if urgency == "Critical" else ("🟠" if urgency == "High" else "🟡")
        
        md = [
            f"### {urg_color} Action: {action_type}",
            f"**Target:** `{target}`  ",
            f"**Urgency:** {urgency} | **Session:** `{session_id}`",
            "",
            "#### 📋 Mitigation Steps"
        ]
        
        if guidelines:
            for g in guidelines:
                md.append(f"- [ ] {g}")
        else:
            md.append("*No specific guidelines available. Please consult the Security Operations Center (SOC).*")
            
        md.append("")
        md.append("---")
        md.append("")
        return md

    def _build_header(self, timestamp: str, total: int, staged: int) -> List[str]:
        return [
            "#" + "=" * 70,
            "# PredictPath AI — Automated Remediation Script",
            f"# Generated: {timestamp} UTC",
            f"# Total Actions: {total}  |  Requires Approval: {staged}",
            "#",
            "# HOW TO USE THIS SCRIPT:",
            "#   1. Review every command carefully before running.",
            "#   2. Open PowerShell as Administrator.",
            "#   3. Run: .\\<this_filename>.ps1",
            "#   4. Commands marked '# ROLLBACK:' can undo the change if needed.",
            "#",
            "# WARNING: Some commands modify firewall rules and user accounts.",
            "# Do NOT run on production systems without change-management approval.",
            "#" + "=" * 70,
            "",
            "# Ensure running as Administrator",
            "$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()",
            "if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {",
            "    Write-Host '[ERROR] Please run this script as Administrator.' -ForegroundColor Red",
            "    exit 1",
            "}",
            "",
            "Write-Host '=== PredictPath AI Remediation Script Starting ===' -ForegroundColor Cyan",
            "",
        ]

    def _build_footer(self) -> List[str]:
        return [
            "",
            "#" + "=" * 70,
            "# END OF SCRIPT",
            "Write-Host '' ",
            "Write-Host '=== All remediation commands completed. ===' -ForegroundColor Cyan",
            "Write-Host 'Review the output above for any errors.' -ForegroundColor Yellow",
            "#" + "=" * 70,
        ]

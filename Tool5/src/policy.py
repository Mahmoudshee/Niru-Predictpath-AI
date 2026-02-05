from typing import Tuple
from .domain import ActionCategory, ExecutionMode, Tool4Action

# Action Catalog Configuration
ACTION_CATALOG = {
    # Observational
    "Enable Process Auditing": ActionCategory.OBSERVATIONAL,
    "Enable Logon Failure Auditing": ActionCategory.OBSERVATIONAL,
    "Monitor User Behavior": ActionCategory.OBSERVATIONAL,
    "Increase Logging": ActionCategory.OBSERVATIONAL,
    
    # Containment
    "Block Inbound SMB": ActionCategory.CONTAINMENT,
    "Rate Limit User": ActionCategory.CONTAINMENT,
    "Terminate Process": ActionCategory.CONTAINMENT,
    
    # Disruptive
    "Isolate Host": ActionCategory.DISRUPTIVE,
    "Disable Account": ActionCategory.DISRUPTIVE,
    "Reset Password": ActionCategory.DISRUPTIVE,
    
    # Irreversible
    "Delete Account": ActionCategory.IRREVERSIBLE,
    "Wipe Host": ActionCategory.IRREVERSIBLE
}

class PolicyEngine:
    def classify_action(self, action_name: str) -> str:
        return ACTION_CATALOG.get(action_name, ActionCategory.DISRUPTIVE) # Default to potentially dangerous if unknown

    def validate_execution_policy(self, action: Tool4Action, confidence: float, blast_radius: int) -> Tuple[str, str]:
        """
        Returns (ExecutionMode, Reason)
        """
        category = self.classify_action(action.action_type)
        
        # 1. Check Irreversible
        if category == ActionCategory.IRREVERSIBLE:
            return ExecutionMode.REJECTED, "Action is classified IRREVERSIBLE - Manual intervention only."

        # 2. Check Blast Radius
        # Hard limit: > 10 hosts cannot serve auto-execution
        if blast_radius > 10 and category != ActionCategory.OBSERVATIONAL:
            return ExecutionMode.STAGED, f"Blast radius ({blast_radius}) exceeds auto-execution limit."

        # 3. Confidence Policies
        if category == ActionCategory.OBSERVATIONAL:
            return ExecutionMode.AUTO, "Observational action safe for auto-execution."
            
        if category == ActionCategory.CONTAINMENT:
            if confidence >= 0.6:
                return ExecutionMode.AUTO, f"Confidence ({confidence:.2f}) meets Containment threshold (0.6)."
            else:
                return ExecutionMode.STAGED, f"Confidence ({confidence:.2f}) below Containment auto-threshold (0.6)."
                
        if category == ActionCategory.DISRUPTIVE:
            # Disruptive always staged unless policy explicitly allows high-conf auto
            # For this strict tool: Always Stage Disruptive
            if confidence < 0.7:
                 return ExecutionMode.REJECTED, f"Confidence ({confidence:.2f}) too low to even stage Disruptive action."
            return ExecutionMode.STAGED, "Disruptive action requires Human-in-the-Loop approval."

        return ExecutionMode.REJECTED, "Unknown action category."

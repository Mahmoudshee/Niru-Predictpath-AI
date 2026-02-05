import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from .domain import Tool4Decision, ExecutionReport, ExecutionResult, ExecutionMode, ExecutionStatus, Tool4Action
from .policy import PolicyEngine, ActionCategory
from .adapters import AdapterFactory
from .logger import AuditLogger

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger()

    def process_plan(self, decisions: List[Dict[str, Any]]) -> ExecutionReport:
        results = []
        stats = {"success": 0, "failed": 0, "pending": 0, "blocked": 0, "total": 0}
        seen_hashes = set()
        
        for d_raw in decisions:
            # Parse Decision (Loose validation to accept dict)
            # We treat everything as single actions
            actions = d_raw.get("recommended_actions", [])
            confidence = d_raw.get("decision_confidence", 0.0)
            session_id = d_raw.get("session_id", "unknown")
            
            for act_raw in actions:
                stats["total"] += 1
                
                # Convert to internal model
                action = Tool4Action(
                    action_type=act_raw["action_type"],
                    target=act_raw["target"],
                    justification=act_raw.get("justification", {})
                )
                
                # 1. Blast Radius Calculation (Heuristic based on Target Type)
                blast_radius = 1
                if action.target.type == "Network Segment":
                    blast_radius = 50 # Assumption
                if action.target.type == "Host":
                    blast_radius = 1

                # FIX: Idempotency / Deduplication
                action_hash = f"{action.action_type}:{action.target.identifier}"
                if action_hash in seen_hashes:
                    logger.warning(f"Duplicate action skipped: {action_hash}")
                    # We can record a skipped result or just skipping. 
                    # Critique says "You executed... twice".
                    # Recording it as skipped is better for audit.
                    # reusing BLOCKED as 'SKIPPED' requires domain change?
                    # Let's just create a result marked as BLOCKED (Deduplicated)
                    # Use a placeholder ID or the previous one if we tracked it?
                    # Simpler to just skip execution logic but log it.
                    
                    result = ExecutionResult(
                        action_id=str(uuid.uuid4()),
                        session_id=session_id,
                        target=f"{action.target.type}:{action.target.identifier}",
                        action_name=action.action_type,
                        execution_mode=ExecutionMode.SKIPPED, # Deduplicated action
                        final_status=ExecutionStatus.BLOCKED,
                        executor="System",
                        message="Duplicate Action: Deduplicated to prevent rule spam."
                    )
                    stats["blocked"] += 1
                    results.append(result)
                    continue
                
                seen_hashes.add(action_hash)
                
                # 2. Policy Check
                mode, reason = self.policy_engine.validate_execution_policy(
                    action, confidence, blast_radius
                )
                
                result = ExecutionResult(
                    action_id=str(uuid.uuid4()),
                    session_id=session_id,
                    target=f"{action.target.type}:{action.target.identifier}",
                    action_name=action.action_type,
                    execution_mode=mode,
                    final_status=ExecutionStatus.PENDING,
                    executor="System",
                    message=reason
                )
                
                # 3. Execution Logic
                if mode == ExecutionMode.AUTO:
                    adapter = AdapterFactory.get_adapter(action.action_type)
                    
                    # Generate Rollback FIRST
                    rb_token = adapter.generate_rollback(
                        action.target.identifier, action.action_type, {}
                    )
                    result.rollback_token = rb_token
                    
                    # Execute
                    success, msg = adapter.execute(
                        action.target.identifier, action.action_type, {}
                    )
                    
                    if success:
                        result.final_status = ExecutionStatus.SUCCESS
                        result.message = f"Executed: {msg}"
                        stats["success"] += 1
                    else:
                        result.final_status = ExecutionStatus.FAILED
                        result.message = f"Execution Failed: {msg}"
                        stats["failed"] += 1
                        
                elif mode == ExecutionMode.STAGED:
                    result.final_status = ExecutionStatus.PENDING
                    result.message = f"Staged for Approval: {reason}"
                    stats["pending"] += 1
                    # Generate Dry Run for Approver
                    adapter = AdapterFactory.get_adapter(action.action_type)
                    result.dry_run_output = f"[DRY RUN] Would execute on {action.target.identifier}: {action.action_type}"
                    
                else: # Rejected
                    result.final_status = ExecutionStatus.BLOCKED
                    stats["blocked"] += 1
                
                # 4. Audit Log
                self.audit_logger.log_execution(
                    result.action_id,
                    result.action_name,
                    result.target,
                    result.executor,
                    result.final_status
                )
                if result.rollback_token:
                    result.audit_hash = f"RB:{result.rollback_token.token_id}" # Simple reference for report
                
                results.append(result)
                
        return ExecutionReport(
            executions=results,
            summary_stats=stats
        )

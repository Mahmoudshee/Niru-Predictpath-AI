import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional
from .domain import AuditLogEntry

class AuditLogger:
    def __init__(self, log_path: str = "execution_audit.log"):
        self.log_path = log_path
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                # Genesis Block
                genesis = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action_id": "GENESIS",
                    "entry_hash": "0000000000000000000000000000000000000000000000000000000000000000"
                }
                f.write(json.dumps(genesis) + "\n")

    def _get_last_hash(self) -> str:
        last_line = ""
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    if line.strip():
                        last_line = line
            if not last_line:
                return "0000000000000000000000000000000000000000000000000000000000000000"
            
            entry = json.loads(last_line)
            return entry.get("entry_hash", "")
        except Exception:
             return "ERROR_READING_CHAIN"

    def log_execution(self, action_id: str, action_type: str, target: str, executor: str, status: str):
        prev_hash = self._get_last_hash()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        entry = AuditLogEntry(
            timestamp=timestamp,
            action_id=action_id,
            action_type=action_type,
            target=target,
            executor=executor,
            status=status,
            prev_hash=prev_hash,
            entry_hash="" # Computed below
        )
        
        # Compute Hash
        entry.entry_hash = entry.compute_hash()
        
        # Write
        with open(self.log_path, "a") as f:
            f.write(entry.model_dump_json() + "\n")

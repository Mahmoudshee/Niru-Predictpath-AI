import unittest
import os
import json
import hashlib
from src.logger import AuditLogger
from src.domain import AuditLogEntry

class TestAuditIntegrity(unittest.TestCase):
    def setUp(self):
        self.test_log = "test_audit.log"
        if os.path.exists(self.test_log):
            os.remove(self.test_log)
        self.logger = AuditLogger(self.test_log)

    def tearDown(self):
        if os.path.exists(self.test_log):
            os.remove(self.test_log)

    def verify_chain(self):
        entries = []
        with open(self.test_log, "r") as f:
            for line in f:
                entries.append(json.loads(line))
        
        # Check Genesis
        self.assertEqual(entries[0]["action_id"], "GENESIS")
        self.assertEqual(entries[0]["entry_hash"], "0" * 64)
        
        # Check specific entries
        for i in range(1, len(entries)):
            curr = entries[i]
            prev = entries[i-1]
            
            # 1. Check Link (Prev Hash matches actual prev entry hash)
            self.assertEqual(curr["prev_hash"], prev["entry_hash"], f"Broken Chain at index {i}")
            
            # 2. Check Integrity (Recompute hash matches stored hash)
            # Reconstruct object
            obj = AuditLogEntry(
                timestamp=curr["timestamp"],
                action_id=curr["action_id"],
                action_type=curr["action_type"],
                target=curr["target"],
                executor=curr["executor"],
                status=curr["status"],
                prev_hash=curr["prev_hash"],
                entry_hash=""
            )
            computed = obj.compute_hash()
            self.assertEqual(computed, curr["entry_hash"], f"Tamper detected at index {i}")

    def test_audit_chain_validity(self):
        # Write 3 entries
        self.logger.log_execution("id1", "Action1", "Target1", "Sys", "Success")
        self.logger.log_execution("id2", "Action2", "Target2", "Sys", "Pending")
        self.logger.log_execution("id3", "Action3", "Target3", "Sys", "Failed")
        
        # Verify
        self.verify_chain()

    def test_tamper_detection(self):
        # Write entries
        self.logger.log_execution("id1", "Action1", "Target1", "Sys", "Success")
        self.logger.log_execution("id2", "Action2", "Target2", "Sys", "Success")
        
        # TAMPER: Modify the file directly
        lines = []
        with open(self.test_log, "r") as f:
            lines = f.readlines()
            
        # Modify the 2nd line (First real entry)
        tampered_entry = json.loads(lines[1])
        tampered_entry["target"] = "TargetHACKED" # Subtle change
        lines[1] = json.dumps(tampered_entry) + "\n"
        
        with open(self.test_log, "w") as f:
            f.writelines(lines)
            
        # Verify should FAIL
        try:
            self.verify_chain()
            self.fail("Tampering was not detected!")
        except AssertionError as e:
            self.assertIn("Tamper detected", str(e))

if __name__ == '__main__':
    unittest.main()

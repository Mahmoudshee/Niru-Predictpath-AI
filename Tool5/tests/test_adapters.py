import unittest
from src.adapters import AdapterFactory, IAMExecutor, FirewallExecutor, AuditExecutor

class TestExecutionSafety(unittest.TestCase):
    
    def test_iam_rollback_inversion(self):
        adapter = IAMExecutor()
        
        # Action: Disable Account
        success, msg = adapter.execute("u101", "Disable Account", {})
        self.assertTrue(success)
        self.assertIn("net user u101 /active:no", msg)
        
        # Rollback: Should be Enable
        token = adapter.generate_rollback("u101", "Disable Account", {})
        self.assertEqual(token.rollback_command, "net user u101 /active:yes")
        
    def test_firewall_rollback_inversion(self):
        adapter = FirewallExecutor()
        
        # Action: Block SMB
        success, msg = adapter.execute("1.2.3.4", "Block Inbound SMB", {})
        self.assertTrue(success)
        self.assertIn("action=block", msg)
        
        # Rollback: Should be Delete Rule
        token = adapter.generate_rollback("1.2.3.4", "Block Inbound SMB", {})
        self.assertIn("delete rule", token.rollback_command)
        
    def test_audit_rollback_inversion(self):
        adapter = AuditExecutor()
        
        # Action: Enable Auditing
        success, msg = adapter.execute("u1", "Enable Process Auditing", {})
        self.assertTrue(success)
        self.assertIn("/success:enable", msg)
        
        # Rollback: Should be Disable
        token = adapter.generate_rollback("u1", "Enable Process Auditing", {})
        self.assertIn("/success:disable", token.rollback_command)

    def test_unsupported_action_safety(self):
        # Ensure we don't execute or crash on unknown actions
        adapter = IAMExecutor()
        success, msg = adapter.execute("u1", "Launch Missiles", {})
        self.assertFalse(success)
        self.assertIn("Unknown", msg)

if __name__ == '__main__':
    unittest.main()

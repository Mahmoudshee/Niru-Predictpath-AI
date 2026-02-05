import unittest
from src.policy import PolicyEngine, ActionCategory, ExecutionMode
from src.domain import Tool4Action, Tool4Target

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def create_action(self, action_type, target_type="User", target_id="u1"):
        return Tool4Action(
            action_type=action_type,
            target=Tool4Target(type=target_type, identifier=target_id),
            justification={}
        )

    def test_observational_always_auto(self):
        # Observational actions should always be AUTO
        act = self.create_action("Enable Process Auditing")
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.01, blast_radius=100)
        self.assertEqual(mode, ExecutionMode.AUTO)

    def test_containment_confidence_threshold(self):
        # Containment requires > 0.6 confidence
        act = self.create_action("Block Inbound SMB")
        
        # Case 1: Low Confidence -> STAGED
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.5, blast_radius=1)
        self.assertEqual(mode, ExecutionMode.STAGED)
        
        # Case 2: High Confidence -> AUTO
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.7, blast_radius=1)
        self.assertEqual(mode, ExecutionMode.AUTO)

    def test_disruptive_is_staged(self):
        # Disruptive actions (Isolate Host) should be STAGED even with high confidence
        # (Assuming policy is strict: Disruptive -> Human in Loop)
        act = self.create_action("Isolate Host")
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.9, blast_radius=1)
        self.assertEqual(mode, ExecutionMode.STAGED)
        
        # And REJECTED if confidence is too low
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.5, blast_radius=1)
        self.assertEqual(mode, ExecutionMode.REJECTED)

    def test_irreversible_is_rejected(self):
        act = self.create_action("Delete Account")
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.99, blast_radius=1)
        self.assertEqual(mode, ExecutionMode.REJECTED)

    def test_blast_radius_limit(self):
        # Containment action with huge blast radius -> STAGED
        act = self.create_action("Block Inbound SMB")
        mode, reason = self.engine.validate_execution_policy(act, confidence=0.9, blast_radius=50)
        self.assertEqual(mode, ExecutionMode.STAGED)

if __name__ == '__main__':
    unittest.main()

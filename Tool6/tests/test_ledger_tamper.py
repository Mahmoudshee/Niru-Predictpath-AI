import unittest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database import Base, TrustLedgerEntry
from src.ledger import TrustLedgerSystem

class TestLedgerTamper(unittest.TestCase):
    def setUp(self):
        self.db_url = "sqlite:///test_tamper.db"
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.ledger = TrustLedgerSystem(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists("test_tamper.db"):
            os.remove("test_tamper.db")

    def test_tamper_detection(self):
        # 1. Create Valid Chain
        self.ledger.log_event("TEST_EVENT", {"data": "valid"}, "Tester")
        self.ledger.log_event("TEST_EVENT_2", {"data": "valid2"}, "Tester")
        
        # Verify valid
        self.assertTrue(self.ledger.verify_ledger_integrity())
        
        # 2. Tamper: Modify the first entry's payload in DB
        # We use raw SQL to bypass ORM safety if needed, or just update object
        entry = self.db.query(TrustLedgerEntry).first()
        entry.previous_hash = "DEADBEEF" * 8 # Break the link
        self.db.commit()
        
        # 3. Verify Invalid
        self.assertFalse(self.ledger.verify_ledger_integrity())

if __name__ == '__main__':
    unittest.main()

import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .database import TrustLedgerEntry


class TrustLedgerSystem:
    def __init__(self, db: Session):
        self.db = db

    def _get_last_hash(self) -> str:
        last_entry = (
            self.db.query(TrustLedgerEntry)
            .order_by(TrustLedgerEntry.timestamp.desc())
            .first()
        )
        if last_entry:
            return last_entry.hash_id
        return "0" * 64  # Genesis Hash

    def _compute_hash(
        self, prev_hash: str, timestamp: str, event_type: str, payload: dict, actor: str
    ) -> str:
        string_payload = json.dumps(payload, sort_keys=True)
        raw = f"{prev_hash}{timestamp}{event_type}{string_payload}{actor}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def log_event(self, event_type: str, payload: dict, actor: str = "System") -> str:
        prev_hash = self._get_last_hash()
        timestamp = datetime.now(timezone.utc)
        ts_str = timestamp.isoformat()

        new_hash = self._compute_hash(prev_hash, ts_str, event_type, payload, actor)

        entry = TrustLedgerEntry(
            hash_id=new_hash,
            previous_hash=prev_hash,
            timestamp=timestamp,
            event_type=event_type,
            payload=payload,
            actor=actor,
        )

        self.db.add(entry)
        self.db.commit()
        return new_hash

    def verify_ledger_integrity(self) -> bool:
        """
        Full cryptographic verification:
        1. Checks that each entry's previous_hash links correctly to the prior entry.
        2. Recomputes each entry's hash from its stored fields and confirms it matches.
        Returns True only if both checks pass for every entry.
        """
        entries = (
            self.db.query(TrustLedgerEntry)
            .order_by(TrustLedgerEntry.timestamp.asc())
            .all()
        )
        if not entries:
            return True

        prev_hash = "0" * 64
        for entry in entries:
            # 1. Check chain link
            if entry.previous_hash != prev_hash:
                return False

            # 2. Recompute hash and compare
            ts_str = entry.timestamp.isoformat() if entry.timestamp else ""
            payload = entry.payload if isinstance(entry.payload, dict) else {}
            expected_hash = self._compute_hash(
                prev_hash, ts_str, entry.event_type, payload, entry.actor
            )
            if entry.hash_id != expected_hash:
                return False

            prev_hash = entry.hash_id

        return True

    def get_entry_count(self) -> int:
        """Return total number of ledger entries."""
        return self.db.query(TrustLedgerEntry).count()

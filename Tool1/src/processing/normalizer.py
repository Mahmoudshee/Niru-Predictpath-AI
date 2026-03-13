from datetime import datetime, timezone
from typing import Dict, Any, Optional
import dateutil.parser

class Normalizer:
    """
    Stateful normalizer to convert raw fields into Canonical Schema format.
    Handles timestamp conversion (to UTC), host canonicalization, etc.
    """

    @staticmethod
    def normalize_timestamp(raw_ts: Any) -> datetime:
        """
        Convert various timestamp formats to Strict UTC datetime.
        """
        if isinstance(raw_ts, datetime):
             if raw_ts.tzinfo is None:
                 return raw_ts.replace(tzinfo=timezone.utc)
             return raw_ts.astimezone(timezone.utc)
        
        try:
            # Attempt integer/float timestamp (seconds)
            if isinstance(raw_ts, (int, float)):
                return datetime.fromtimestamp(raw_ts, tz=timezone.utc)
            
            # Attempt ISO/String parsing
            dt = dateutil.parser.parse(str(raw_ts))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            raise ValueError(f"Could not normalize timestamp: {raw_ts}")

    @staticmethod
    def normalize_host(host: Optional[str]) -> Optional[str]:
        """
        Canonicalize hostnames: lowercase, strip FQDN if needed, etc.
        For now: simple lowercase and trim.
        """
        if not host or host == "?":
            return None
        return host.strip().lower()

    @staticmethod
    def normalize_user(user: Optional[str]) -> Optional[str]:
        """
        Canonicalize users: 'DOMAIN\\user' -> 'user@domain' or similar.
        """
        if not user or user == "?":
            return None
        return user.strip().lower()

"""Base ingester class for VulnIntel."""

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.database.connection import get_db_context
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseIngester(ABC):
    """Base class for data ingestors."""
    
    def __init__(self, source_name: str) -> None:
        """
        Initialize base ingester.
        
        Args:
            source_name: Name of the data source (e.g., "cve", "cwe", "kev")
        """
        self.source_name = source_name
        self.records_processed = 0
        self.errors_encountered = 0
    
    @abstractmethod
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize data from source.
        
        Args:
            force: Force sync even if not due
            
        Returns:
            True if sync successful, False otherwise
        """
        pass
    
    def should_sync(self, max_age_seconds: int) -> bool:
        """
        Check if sync is needed based on last sync time.
        
        Args:
            max_age_seconds: Maximum age before sync is needed
            
        Returns:
            True if sync is needed, False otherwise
        """
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_sync_time FROM sync_metadata WHERE source = ?",
                (self.source_name,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.info(f"No sync metadata for {self.source_name}, sync needed")
                return True
            
            last_sync_str = row["last_sync_time"]
            last_sync = datetime.fromisoformat(last_sync_str.replace("Z", "+00:00"))
            age = (datetime.now(last_sync.tzinfo) - last_sync).total_seconds()
            
            if age >= max_age_seconds:
                logger.info(f"{self.source_name} sync needed (age: {age:.0f}s)")
                return True
            else:
                logger.info(f"{self.source_name} sync not needed (age: {age:.0f}s)")
                return False
    
    def update_sync_metadata(self, status: str, next_sync_seconds: Optional[int] = None) -> None:
        """
        Update sync metadata in database.
        
        Args:
            status: Sync status ("success" or "failed")
            next_sync_seconds: Seconds until next sync is due
        """
        now = datetime.utcnow().isoformat() + "Z"
        
        next_sync_due = None
        if next_sync_seconds:
            next_sync = datetime.utcnow() + timedelta(seconds=next_sync_seconds)
            next_sync_due = next_sync.isoformat() + "Z"
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sync_metadata 
                (source, last_sync_time, last_sync_status, records_processed, errors_encountered, next_sync_due)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    last_sync_time = excluded.last_sync_time,
                    last_sync_status = excluded.last_sync_status,
                    records_processed = excluded.records_processed,
                    errors_encountered = excluded.errors_encountered,
                    next_sync_due = excluded.next_sync_due
                """,
                (
                    self.source_name,
                    now,
                    status,
                    self.records_processed,
                    self.errors_encountered,
                    next_sync_due,
                )
            )
        
        logger.info(f"Updated sync metadata for {self.source_name}: {status}")
    
    def get_sync_status(self) -> dict:
        """
        Get current sync status.
        
        Returns:
            Dictionary with sync status information
        """
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sync_metadata WHERE source = ?",
                (self.source_name,)
            )
            row = cursor.fetchone()
            
            if not row:
                return {
                    "source": self.source_name,
                    "status": "never_synced",
                }
            
            return dict(row)

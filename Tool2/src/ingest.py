import polars as pl
from typing import List, Dict, Any
from datetime import timedelta
import logging
from .domain import EnrichedEvent, Session

logger = logging.getLogger(__name__)

class DataIngester:
    def __init__(self, parquet_path: str):
        self.parquet_path = parquet_path

    def verify_integrity(self) -> bool:
        """
        Placeholder for cryptographic chain verification.
        In a real scenario, this would re-hash the event chain to ensure no tampering.
        For now, we verify the file exists and is readable.
        """
        try:
            pl.scan_parquet(self.parquet_path).collect()
            logger.info(f"Integrity check passed for {self.parquet_path}")
            return True
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False

    def load_sessions(self, time_window_params: str = "60m") -> List[Session]:
        """
        Loads data, groups by user, and creates session windows.
        """
        logger.info("Loading Parquet data...")
        try:
            df = pl.read_parquet(self.parquet_path)
        except Exception as e:
            logger.error(f"Failed to load parquet file: {e}")
            return []

        # Ensure timestamp is datetime
        if "timestamp" not in df.columns:
            # Fallback if timestamp is missing or named differently (e.g. parsed from ID?)
            # Tool 1 logs implied timestamp exists. Let's assume 'timestamp' column.
            # If not, we might need to derive it.
            logger.warning("Column 'timestamp' not found, attempting detection...")
            # For now, return empty if crucial data missing
            return []

        df = df.sort("timestamp")
        
        # State-Aware Sessionization
        # We define a session as: Same user, events within 60 min gap
        # Polars dynamic grouping can handle this.
        
        # However, for strict detailed control and mapping to our domain objects, 
        # iterating might be safer for complex logic, but Polars is faster.
        # Let's use Polars to assign session IDs.
        
        # 1. Sort by user, timestamp
        df = df.sort(["user", "timestamp"])
        
        # 2. Calculate time difference between consecutive events for each user
        df = df.with_columns([
            pl.col("timestamp").diff().over("user").alias("time_diff")
        ])
        
        # 3. Mark start of new session if time_diff > window
        window_delta = timedelta(minutes=60) # simplistic check, Polars uses durations
        
        # Convert duration to us/ms for comparison if needed, or use Polars dynamic
        df = df.with_columns(
            (pl.col("time_diff").fill_null(pl.duration(days=365)) > pl.duration(minutes=60)).cum_sum().over("user").alias("session_group_id")
        )
        
        # Create unique session ID
        df = df.with_columns(
            pl.format("{}_{}", pl.col("user"), pl.col("session_group_id")).alias("unique_session_id")
        )

        # Convert to Domain Objects
        sessions: List[Session] = []
        
        # Group by unique_session_id and extract data
        # This part effectively effectively "materializes" the sessions
        grouped = df.partition_by("unique_session_id", as_dict=True)
        
        for s_id, group_df in grouped.items():
            events = []
            priority = False
            
            rows = group_df.to_dicts()
            if not rows:
                continue

            start_t = rows[0]["timestamp"]
            end_t = rows[-1]["timestamp"]
            
            # Check for IP switching (source_host variance)
            unique_ips = group_df["source_host"].n_unique()
            if unique_ips > 1:
                priority = True
                
            # Check for high confidence scores
            if group_df["confidence_score"].max() > 0.8: # Arbitrary threshold for "high"
                priority = True

            for row in rows:
                events.append(EnrichedEvent(
                    event_id=str(row.get("event_id", "")),
                    timestamp=row["timestamp"],
                    user=row["user"],
                    source_host=row["source_host"],
                    target_host=row.get("target_host"),
                    event_type=row["event_type"],
                    protocol=row.get("protocol"),
                    mitre_technique=row.get("mitre_technique"),
                    confidence_score=row["confidence_score"],
                    data_quality_score=row["data_quality_score"]
                ))
            
            sessions.append(Session(
                session_id=str(s_id),
                user=rows[0]["user"],
                start_time=start_t,
                end_time=end_t,
                events=events,
                is_high_priority=priority
            ))
            
        return sessions

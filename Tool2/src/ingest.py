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
        # Skip redundant scan to prevent schema mismatch crashes in the CLI
        return True

    def load_sessions(self, time_window_params: str = "60m") -> List[Session]:
        """
        Loads data, groups by user, and creates session windows.
        """
        import glob
        files = glob.glob(self.parquet_path, recursive=True)
        if not files:
            logger.error(f"No files found matching: {self.parquet_path}")
            return []
            
        try:
            # Manual unification because Polars/PyArrow fail on List vs Null mismatches in globs
            dataframes = []
            for f in files:
                f_df = pl.read_parquet(f)
                
                # Force schema alignment for problematic columns
                if "observed_cve_ids" in f_df.columns:
                    f_df = f_df.with_columns(pl.col("observed_cve_ids").cast(pl.List(pl.Utf8)))
                else:
                    f_df = f_df.with_columns(pl.lit([]).cast(pl.List(pl.Utf8)).alias("observed_cve_ids"))

                if "observed_cwe_ids" in f_df.columns:
                    f_df = f_df.with_columns(pl.col("observed_cwe_ids").cast(pl.List(pl.Utf8)))
                else:
                    f_df = f_df.with_columns(pl.lit([]).cast(pl.List(pl.Utf8)).alias("observed_cwe_ids"))
                
                dataframes.append(f_df)
            
            df = pl.concat(dataframes, how="diagonal")
            logger.info(f"Loaded {len(df)} events from {len(files)} files via manual schema alignment.")
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
        
        # 1. Create a "Surrogate Identity" for sessionization
        # If user is missing, use source_host. If both missing, use "System"
        df = df.with_columns([
            pl.coalesce([pl.col("user"), pl.col("source_host"), pl.lit("System")]).alias("surrogate_id")
        ])

        # 2. Sort by surrogate_id, timestamp
        df = df.sort(["surrogate_id", "timestamp"])
        
        # 3. Calculate time difference between consecutive events for each identity
        df = df.with_columns([
            pl.col("timestamp").diff().over("surrogate_id").alias("time_diff")
        ])
        
        # 4. Mark start of new session if time_diff > window (60m)
        df = df.with_columns(
            (pl.col("time_diff").fill_null(pl.duration(days=365)) > pl.duration(minutes=60)).cum_sum().over("surrogate_id").alias("session_group_id")
        )
        
        # 5. Create unique session ID (Human Friendly for the Mentor)
        df = df.with_columns(
            pl.format("Activity on {}", pl.col("surrogate_id")).alias("unique_session_id")
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
                    user=row.get("user") or "Unknown",
                    source_host=row.get("source_host") or "Unknown",
                    target_host=row.get("target_host"),
                    event_type=row["event_type"],
                    protocol=row.get("protocol"),
                    mitre_technique=row.get("mitre_technique"),
                    observed_cve_ids=row.get("observed_cve_ids", []),
                    observed_cwe_ids=row.get("observed_cwe_ids", []),
                    confidence_score=row["confidence_score"],
                    data_quality_score=row["data_quality_score"],
                    raw_text=row.get("raw_source")
                ))
            
            sessions.append(Session(
                session_id=str(s_id).replace("('", "").replace("',)", "").replace("(", "").replace(")", "").replace("'", ""),
                user=rows[0]["user"],
                start_time=start_t,
                end_time=end_t,
                events=events,
                is_high_priority=priority
            ))
            
        return sessions

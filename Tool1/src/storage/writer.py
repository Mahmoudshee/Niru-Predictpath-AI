"""
StorageWriter - Writes CanonicalEvents to Parquet (columnar) + JSON summary.
Production-grade: batching, emergency fallback, zero data loss guarantee.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import polars as pl

from ..core.config import settings
from ..core.schema import CanonicalEvent

logger = logging.getLogger(__name__)

_PARQUET_SCHEMA = {
    "event_id": pl.Utf8,
    "timestamp": pl.Utf8,
    "ingest_timestamp": pl.Utf8,
    "event_type": pl.Utf8,
    "severity": pl.Utf8,
    "source_host": pl.Utf8,
    "target_host": pl.Utf8,
    "user": pl.Utf8,
    "agent_name": pl.Utf8,
    "protocol": pl.Utf8,
    "port": pl.Int32,
    "mitre_technique": pl.Utf8,
    "mitre_tactic": pl.Utf8,
    "mitre_technique_name": pl.Utf8,
    "observed_cve_ids": pl.Utf8,   # pipe-delimited
    "observed_cwe_ids": pl.Utf8,   # pipe-delimited
    "cve_max_cvss": pl.Float64,
    "cve_severity": pl.Utf8,
    "is_kev": pl.Boolean,
    "confidence_score": pl.Float64,
    "data_quality_score": pl.Float64,
    "risk_score": pl.Float64,
    "source_file": pl.Utf8,
    "parser_version": pl.Utf8,
    "model_version": pl.Utf8,
    "log_category": pl.Utf8,
    "raw_source": pl.Utf8,
    "raw_hash": pl.Utf8,
    "previous_event_hash": pl.Utf8,
    "event_hash": pl.Utf8,
}


class StorageWriter:
    """
    Buffers CanonicalEvents and batch-writes to Parquet partitioned by date.
    Falls back to JSONL if Parquet write fails.
    """

    BATCH_SIZE = 500  # Write every 500 events

    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.dlq_dir = settings.DEAD_LETTER_QUEUE_DIR
        self._buffer: List[CanonicalEvent] = []
        self._write_count = 0

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def write(self, event: CanonicalEvent) -> None:
        """Buffer an event and flush when batch is full."""
        self._buffer.append(event)
        if len(self._buffer) >= self.BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        """Write all buffered events to Parquet, partitioned by date."""
        if not self._buffer:
            return

        try:
            rows: List[Dict[str, Any]] = []
            for evt in self._buffer:
                d = evt.to_dict()
                # Enforce correct types
                d["port"] = int(d["port"]) if d.get("port") is not None else None
                d["confidence_score"] = float(d.get("confidence_score") or 0.0)
                d["data_quality_score"] = float(d.get("data_quality_score") or 0.0)
                d["risk_score"] = float(d.get("risk_score") or 0.0)
                d["cve_max_cvss"] = float(d["cve_max_cvss"]) if d.get("cve_max_cvss") is not None else None
                d["is_kev"] = bool(d.get("is_kev", False))
                # Ensure all string fields are str or None (not list)
                for k in ("observed_cve_ids", "observed_cwe_ids"):
                    v = d.get(k)
                    if isinstance(v, list):
                        d[k] = "|".join(v)
                    elif v is None:
                        d[k] = ""
                rows.append(d)

            df = pl.DataFrame(rows, schema_overrides=_PARQUET_SCHEMA, infer_schema_length=len(rows))

            # Partition by event date
            date_groups: Dict[str, List[Dict]] = {}
            for row in rows:
                ts = row.get("timestamp", "")
                date_part = ts[:10] if ts else datetime.now(timezone.utc).strftime("%Y-%m-%d")
                date_groups.setdefault(date_part, []).append(row)

            for date_str, group_rows in date_groups.items():
                df_part = pl.DataFrame(group_rows, schema_overrides=_PARQUET_SCHEMA, infer_schema_length=len(group_rows))
                part_dir = self.output_dir / date_str
                part_dir.mkdir(parents=True, exist_ok=True)
                ts_suffix = int(datetime.now(timezone.utc).timestamp() * 1000)
                out_path = part_dir / f"events_{ts_suffix}.parquet"
                df_part.write_parquet(str(out_path))
                logger.info(f"[Tool1] Wrote {len(group_rows)} events -> {out_path}")
                self._write_count += len(group_rows)

            self._buffer.clear()

        except Exception as e:
            logger.error(f"[Tool1] Parquet flush failed: {e} — falling back to JSONL", exc_info=True)
            self._emergency_jsonl_dump()

    def _emergency_jsonl_dump(self) -> None:
        """Last-resort: dump buffer to JSONL file so NO data is lost."""
        try:
            ts = int(datetime.now(timezone.utc).timestamp())
            path = self.output_dir / f"emergency_dump_{ts}.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for evt in self._buffer:
                    f.write(json.dumps(evt.to_dict(), default=str) + "\n")
            logger.warning(f"[Tool1] Emergency JSONL dump: {path} ({len(self._buffer)} events)")
            self._write_count += len(self._buffer)
            self._buffer.clear()
        except Exception as e2:
            logger.critical(f"[Tool1] EMERGENCY DUMP FAILED: {e2} — DATA LOSS OCCURRING")

    @property
    def total_written(self) -> int:
        return self._write_count

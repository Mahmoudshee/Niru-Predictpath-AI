"""
Tool 1 - Event Intelligence Engine
Entry point: ingests any log file, normalizes, enriches, and stores to Parquet.
Usage from Tool1 directory:
    .venv\Scripts\python.exe -m src.main ingest "<path_to_log_file>"
"""
import sys
import logging
from pathlib import Path

import typer

from src.ingestion.universal import UniversalIngestor
from src.ingestion.auth_lanl import LanlAuthIngestor
from src.ingestion.net_cicids import CicIdsIngestor
from src.processing.pipeline import Pipeline
from src.core.config import settings, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="predictpath-tool1",
    help="PredictPath AI — Event Intelligence Engine (Ingestion, Normalisation, Enrichment)",
    add_completion=False,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_path(raw: str) -> Path:
    """
    Robustly resolve a path passed from the frontend/CLI.
    Handles:
     - Absolute paths (C:\...) — used as-is
     - Relative paths with leading ..\ — resolved from TOOLS_ROOT
     - Relative paths — resolved from CWD
     - Extra quotes / whitespace — stripped
    """
    cleaned = raw.strip("'\" \t\n\r")
    p = Path(cleaned)

    # 1. Already absolute and exists
    if p.is_absolute() and p.exists():
        return p

    # 2. Absolute path that doesn't exist — don't try to further resolve
    if p.is_absolute():
        return p

    # 3. Relative — try CWD first
    cwd_candidate = Path.cwd() / cleaned
    if cwd_candidate.exists():
        return cwd_candidate.resolve()

    # 4. Relative — try TOOLS_ROOT (one level above Tool1)
    tools_root = Path(__file__).resolve().parent.parent.parent  # .../Niru-Predictpath-AI
    root_candidate = tools_root / cleaned
    if root_candidate.exists():
        return root_candidate.resolve()

    # 5. Strip leading separators and retry against TOOLS_ROOT
    stripped = cleaned.lstrip(".\\/")
    root_candidate2 = tools_root / stripped
    if root_candidate2.exists():
        return root_candidate2.resolve()

    # 6. Return as-is (the caller will report "not found")
    return p.resolve()


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def ingest(
    source: str = typer.Argument(..., help="Path to raw log file (any format)"),
    log_type: str = typer.Option("auto", "--type", "-t",
                                  help="Ingestor type: auto | universal | lanl | cicids"),
    limit: int = typer.Option(5000, "--limit", "-l",
                               help="Maximum events to ingest (default: 5000)"),
):
    """
    Ingest a log file → normalize → enrich with MITRE + CVE → store as Parquet.
    Supports: JSON, NDJSON, XML (Nmap), CSV, PCAP, GZ, LOG, TXT and more.
    """
    # ── Resolve path ──────────────────────────────────────────────────────────
    source_path = _resolve_path(source)

    if not source_path.exists():
        typer.secho(f"✗ Error: Cannot find file: {source_path}", fg=typer.colors.RED, err=True)
        typer.secho(f"  Raw input was: {repr(source)}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"[Tool1] Source: {source_path}", fg=typer.colors.CYAN)
    typer.secho(f"[Tool1] Size  : {source_path.stat().st_size:,} bytes", fg=typer.colors.CYAN)

    # ── Select ingestor ───────────────────────────────────────────────────────
    ext = source_path.suffix.lower()
    ingest_type = log_type.lower()

    if ingest_type == "auto":
        if ext in (".csv", ".gz"):
            ingest_type = "lanl_or_universal"
        else:
            ingest_type = "universal"

    # Force universal for formats LANL/CICIDS can't handle
    if ingest_type in ("lanl", "cicids") and ext not in (".csv", ".gz", ".txt", ""):
        typer.secho(
            f"[!] Type '{ingest_type}' expects CSV/GZ but got '{ext}' — switching to universal",
            fg=typer.colors.YELLOW,
        )
        ingest_type = "universal"

    try:
        if ingest_type == "lanl":
            ingestor = LanlAuthIngestor(source_path)
        elif ingest_type == "cicids":
            ingestor = CicIdsIngestor(source_path)
        elif ingest_type == "lanl_or_universal":
            # Try LANL; fallback to universal
            try:
                ingestor = LanlAuthIngestor(source_path)
            except Exception:
                ingestor = UniversalIngestor(source_path)
        else:
            ingestor = UniversalIngestor(source_path)

        typer.secho(f"[Tool1] Ingestor: {ingestor.__class__.__name__}", fg=typer.colors.CYAN)

    except Exception as e:
        typer.secho(f"✗ Failed to initialise ingestor: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # ── Run pipeline ──────────────────────────────────────────────────────────
    try:
        pipeline = Pipeline(ingestor)
        summary = pipeline.run(max_lines=limit)

        typer.secho("\n✅ Ingestion complete!", fg=typer.colors.GREEN)
        typer.secho(f"   Events ingested: {summary['success']}", fg=typer.colors.GREEN)
        typer.secho(f"   Events failed  : {summary['failed']}", fg=typer.colors.YELLOW)
        typer.secho(f"   Output dir     : {summary['output_dir']}", fg=typer.colors.CYAN)

        intel = summary.get("intelligence", {})
        if intel.get("mitre_breakdown"):
            typer.secho(f"   MITRE Techniques: {intel['mitre_breakdown']}", fg=typer.colors.MAGENTA)
        if intel.get("severity_breakdown"):
            typer.secho(f"   Severity : {intel['severity_breakdown']}", fg=typer.colors.MAGENTA)
        if intel.get("cve_ids_observed"):
            typer.secho(f"   CVEs Observed: {intel['cve_ids_observed'][:5]}", fg=typer.colors.RED)

        if summary["success"] == 0:
            typer.secho("⚠  Warning: 0 events were successfully ingested.", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(code=2)

    except SystemExit:
        raise
    except Exception as e:
        typer.secho(f"\n✗ Pipeline failed: {e}", fg=typer.colors.RED, err=True)
        logger.exception("Pipeline fatal error")
        raise typer.Exit(code=1)


@app.command()
def query(
    sql: str = typer.Argument(..., help="DuckDB SQL query (SELECT ... FROM '<path>/**/*.parquet')"),
):
    """Query the processed Parquet events using DuckDB SQL."""
    import duckdb
    import polars as pl

    output_glob = str(settings.OUTPUT_DIR / "**" / "*.parquet").replace("\\", "/")
    typer.echo(f"Querying: {output_glob}")
    try:
        conn = duckdb.connect()
        if sql.strip().upper().startswith("SELECT"):
            result = conn.execute(sql).fetchdf()
        else:
            result = conn.execute(
                f"SELECT * FROM read_parquet('{output_glob}', union_by_name=true) WHERE {sql}"
            ).fetchdf()
        typer.echo(result.to_string())
    except Exception as e:
        typer.secho(f"Query error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

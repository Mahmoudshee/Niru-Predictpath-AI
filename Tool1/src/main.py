import typer
from pathlib import Path
from typing import Optional
from src.ingestion.auth_lanl import LanlAuthIngestor
from src.ingestion.net_cicids import CicIdsIngestor
from src.processing.pipeline import Pipeline
from src.core.config import settings
import logging

app = typer.Typer(name="predictpath-tool1", help="Unified Event Intelligence Engine")
logger = logging.getLogger(__name__)

@app.command()
def ingest(
    source: Path = typer.Argument(..., help="Path to raw log file", exists=True),
    type: str = typer.Option(..., "--type", "-t", help="Log type: 'lanl' or 'cicids'"),
    rate_limit: int = typer.Option(settings.MAX_INGEST_RATE, help="Max events per second")
):
    """
    Ingest raw security logs, normalize, enrich, and store them.
    """
    typer.echo(f"Starting ingestion for {source} as {type}...")
    
    # 1. Select Ingestor
    try:
        if type.lower() == 'lanl':
            print("Initializing LANL ingestor...")
            ingestor = LanlAuthIngestor(source)
        elif type.lower() == 'cicids':
            ingestor = CicIdsIngestor(source)
        else:
            typer.echo(f"Unknown type: {type}. Supported: lanl, cicids")
            raise typer.Exit(code=1)
            
        # 2. Configure Pipeline
        print("Initializing Pipeline...")
        pipeline = Pipeline(ingestor)
        pipeline.rate_limit = rate_limit
        
        # 3. Run
        print("Running Pipeline...")
        pipeline.run()
        print("Pipeline run completed.")
        typer.echo("Ingestion complete. Check output directory for Parquet files.")
    except Exception as e:
        print(f"CRITICAL ERROR IN MAIN: {e}")
        typer.echo(f"Ingestion failed: {e}")
        raise typer.Exit(code=1)

@app.command()
def query(
    query: str = typer.Argument(..., help="DuckDB SQL query to run against output")
):
    """
    Query the processed events using DuckDB.
    """
    import duckdb
    
    output_path = settings.OUTPUT_DIR / "**/*.parquet"
    typer.echo(f"Querying data at {output_path}...")
    
    try:
        # Create relation from parquet files
        conn = duckdb.connect()
        path_str = str(output_path).replace("\\", "/")
        
        # Determine if it's a full query or a filter
        if query.strip().upper().startswith("SELECT"):
            # Raw query, execute as is
            arrow_table = conn.execute(query).fetch_arrow_table()
        else:
            # Filter shorthand
            arrow_table = conn.execute(f"SELECT * FROM '{path_str}' WHERE {query}").fetch_arrow_table()
            
        import polars as pl
        df = pl.from_arrow(arrow_table)
        typer.echo(df)
        
    except Exception as e:
        typer.echo(f"Query error: {e}")

if __name__ == "__main__":
    app()

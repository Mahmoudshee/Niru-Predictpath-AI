import argparse
import sys
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .database import init_db, SessionLocal, ModelConfiguration
from .ledger import TrustLedgerSystem
from .learning import LearningEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool6")
console = Console()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def load_json(path: str):
    try:
        with open(path, 'r') as f: return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        sys.exit(1)

def display_status(db):
    console.print(Panel("📊 SYSTEM TRUST LEVEL & CONFIGURATION", style="bold blue"))
    
    config = db.query(ModelConfiguration).filter_by(is_active=1).first()
    
    status_data = {}
    
    if config:
        if config.trust_momentum < -0.001:
             trend_icon = "↘ (Tightening)"
             trend_color = "red"
             trend_val = "tightening"
        elif config.trust_momentum > 0.001:
             trend_icon = "↗ (Relaxing)"
             trend_color = "green"
             trend_val = "relaxing"
        else:
             trend_icon = "→ (Stable)"
             trend_color = "white"
             trend_val = "stable"
            
        table = Table(title=f"Active Model: {config.version_id}")
        table.add_column("Parameter")
        table.add_column("Value")
        table.add_column("Pressure/Trend", style=trend_color)
        
        table.add_row("Containment Threshold", f"{config.containment_threshold:.4f}", trend_icon)
        table.add_row("Disruptive Threshold", f"{config.disruptive_threshold:.4f}", trend_icon)
        table.add_row("Trust Momentum", f"{config.trust_momentum:.4f}", trend_icon)
        table.add_row("Streak", f"S:{config.success_streak} / F:{config.failure_streak}", "-")
        
        console.print(table)
        
        status_data = {
            "version_id": config.version_id,
            "containment_threshold": config.containment_threshold,
            "disruptive_threshold": config.disruptive_threshold,
            "trust_momentum": config.trust_momentum,
            "success_streak": config.success_streak,
            "failure_streak": config.failure_streak,
            "trend": trend_val
        }
    else:
        console.print("[red]No Active Configuration Found![/red]")
        status_data = {"error": "No active configuration"}

    # Write status to JSON for UI
    try:
        with open("status.json", "w") as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write status.json: {e}")


def process_ingest(file_path: str):
    db = SessionLocal()
    ledger = TrustLedgerSystem(db)
    learner = LearningEngine(db, ledger)
    
    logger.info(f"Ingesting execution report from {file_path}...")
    report = load_json(file_path)
    ledger.log_event("INGEST_REPORT", {"report_id": report.get("report_id", "unknown")}, "CLI_User")
    
    new_config = learner.process_execution_feedback(report)
    
    console.print(f"[green]✅ Learning Complete. Model updated to {new_config.version_id}[/green]")
    # We display stats from database object
    
    display_status(db)
    db.close()

def main():
    parser = argparse.ArgumentParser(description="Tool 6: Governance & Learning Engine")
    subparsers = parser.add_subparsers(dest="command")
    
    parser_ingest = subparsers.add_parser("ingest")
    parser_ingest.add_argument("report_path")
    
    parser_status = subparsers.add_parser("status")
    parser_init = subparsers.add_parser("init")

    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
        logger.info("Database initialized.")
        
    elif args.command == "ingest":
        process_ingest(args.report_path)
        
    elif args.command == "status":
        db = SessionLocal()
        display_status(db)
        db.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

import argparse
import sys
import json
import logging
import os
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .database import init_db, SessionLocal, ModelConfiguration, TrustLedgerEntry
from .ledger import TrustLedgerSystem
from .learning import LearningEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool6")
console = Console()

# Always write status.json to the Tool6 directory (one level above src/)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL6_DIR = os.path.dirname(_THIS_DIR)
STATUS_FILE = os.path.join(_TOOL6_DIR, "status.json")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_json(path: str, fatal: bool = True):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        if fatal:
            logger.error(f"Failed to load {path}: {e}")
            sys.exit(1)
        else:
            logger.warning(f"Optional file {path} could not be loaded: {e}")
            return None


def _trend_info(config: ModelConfiguration):
    if config.trust_momentum < -0.001:
        return "tightening", "Tightening (Hardening)", "red"
    elif config.trust_momentum > 0.001:
        return "relaxing", "Relaxing (Adapting)", "green"
    else:
        return "stable", "Stable", "white"


def _get_ledger_history(db, limit: int = 10):
    """Fetch the most recent trust ledger entries."""
    entries = (
        db.query(TrustLedgerEntry)
        .order_by(TrustLedgerEntry.timestamp.desc())
        .limit(limit)
        .all()
    )
    result = []
    for e in entries:
        result.append({
            "hash_id": e.hash_id[:12] + "...",
            "event_type": e.event_type,
            "actor": e.actor,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "payload": e.payload,
        })
    return result


def _get_model_history(db, limit: int = 5):
    """Fetch recent model versions."""
    configs = (
        db.query(ModelConfiguration)
        .order_by(ModelConfiguration.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for c in configs:
        result.append({
            "version_id": c.version_id,
            "is_active": bool(c.is_active),
            "containment_threshold": c.containment_threshold,
            "disruptive_threshold": c.disruptive_threshold,
            "trust_momentum": c.trust_momentum,
            "success_streak": c.success_streak,
            "failure_streak": c.failure_streak,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


def display_status(db, extra_context: dict = None):
    """Display rich terminal output and write comprehensive status.json."""
    console.print(Panel("[bold cyan]TOOL 6 — GOVERNANCE & ADAPTIVE LEARNING ENGINE[/bold cyan]", box=box.DOUBLE_EDGE))

    config = db.query(ModelConfiguration).filter_by(is_active=1).first()
    status_data = {}

    if config:
        trend_val, trend_label, trend_color = _trend_info(config)

        # ── Rich Terminal Table ────────────────────────────────────────
        table = Table(title=f"Active Trust Model: [bold]{config.version_id}[/bold]", box=box.ROUNDED)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Trend", style=trend_color)

        table.add_row("Containment Threshold", f"{config.containment_threshold:.4f} ({config.containment_threshold*100:.1f}%)", trend_label)
        table.add_row("Disruptive Threshold",  f"{config.disruptive_threshold:.4f} ({config.disruptive_threshold*100:.1f}%)", trend_label)
        table.add_row("Trust Momentum",        f"{config.trust_momentum:+.4f}", trend_label)
        table.add_row("Success Streak",        str(config.success_streak), "green" if config.success_streak > 0 else "white")
        table.add_row("Failure Streak",        str(config.failure_streak), "red" if config.failure_streak > 0 else "white")

        console.print(table)

        # ── Ledger Integrity Check ─────────────────────────────────────
        ledger = TrustLedgerSystem(db)
        integrity_ok = ledger.verify_ledger_integrity()
        total_entries = ledger.get_entry_count()
        ledger_entries = _get_ledger_history(db, limit=10)
        model_history = _get_model_history(db, limit=5)

        integrity_label = "[green]VERIFIED[/green]" if integrity_ok else "[red]TAMPERED[/red]"
        console.print(f"\n[bold]Ledger Integrity:[/bold] {integrity_label}")
        console.print(f"[bold]Total Ledger Entries:[/bold] {total_entries}")

        # ── Drift Alerts ───────────────────────────────────────────────
        drift_alerts = _check_drift_alerts(config)
        if drift_alerts:
            console.print("\n[bold yellow]⚠ Drift Alerts:[/bold yellow]")
            for alert in drift_alerts:
                console.print(f"  [yellow]• {alert}[/yellow]")

        # ── Build Status JSON ──────────────────────────────────────────
        status_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version_id": config.version_id,
            "containment_threshold": config.containment_threshold,
            "disruptive_threshold": config.disruptive_threshold,
            "trust_momentum": config.trust_momentum,
            "success_streak": config.success_streak,
            "failure_streak": config.failure_streak,
            "trend": trend_val,
            "trend_label": trend_label,
            "ledger_integrity": integrity_ok,
            "ledger_entry_count": total_entries,
            "recent_ledger_entries": ledger_entries,
            "model_history": model_history,
            "drift_alerts": drift_alerts,
        }

        # Attach extra context from learning if available
        if extra_context:
            status_data["last_learning_event"] = extra_context
            # Promote Audit PDF to top-level for UI easy access
            if "pdf_audit_path" in extra_context:
                status_data["pdf_audit_path"] = extra_context["pdf_audit_path"]
            if "pdf_audit_filename" in extra_context:
                status_data["pdf_audit_filename"] = extra_context["pdf_audit_filename"]

    else:
        console.print("[red]No Active Configuration Found — run 'init' first.[/red]")
        status_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": "No active configuration",
            "version_id": None,
            "containment_threshold": None,
            "disruptive_threshold": None,
            "trust_momentum": None,
            "success_streak": 0,
            "failure_streak": 0,
            "trend": "unknown",
            "trend_label": "Unknown",
            "ledger_integrity": False,
            "ledger_entry_count": 0,
            "recent_ledger_entries": [],
            "model_history": [],
            "drift_alerts": [],
        }

    # Write to status.json (always in Tool6 root)
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
        console.print(f"\n[green]✅ status.json written → {STATUS_FILE}[/green]")
    except Exception as e:
        logger.warning(f"Failed to write status.json: {e}")

    return status_data


def _check_drift_alerts(config: ModelConfiguration) -> list:
    """
    Detect anomalous trust-state conditions and return human-readable alerts.
    """
    alerts = []

    # Extreme momentum — system is drifting hard in one direction
    if config.trust_momentum <= -0.25:
        alerts.append(
            f"CRITICAL DRIFT: Trust momentum is severely negative ({config.trust_momentum:+.4f}). "
            "Autonomous actions are heavily restricted. Investigate recent failures."
        )
    elif config.trust_momentum >= 0.25:
        alerts.append(
            f"HIGH RELAXATION: Trust momentum is very high ({config.trust_momentum:+.4f}). "
            "Thresholds are significantly lowered. Verify no false-positive successes."
        )

    # Containment threshold has drifted to extremes
    if config.containment_threshold >= 0.90:
        alerts.append(
            f"THRESHOLD LOCK: Containment threshold is at {config.containment_threshold*100:.1f}%. "
            "Nearly all actions require human approval — system is in near-lockdown."
        )
    elif config.containment_threshold <= 0.45:
        alerts.append(
            f"LOW GUARD: Containment threshold is at {config.containment_threshold*100:.1f}%. "
            "System is highly permissive. Ensure this reflects genuine trust."
        )

    # Long failure streak
    if config.failure_streak >= 3:
        alerts.append(
            f"FAILURE STREAK: {config.failure_streak} consecutive failures detected. "
            "System is tightening posture. Review recent execution reports."
        )

    return alerts


def process_ingest(file_path: str, t3_path: str = None, t4_path: str = None, output_dir: str = None):
    """Ingest a Tool 5 execution/script report and update the governance model."""
    from .report_generator import AuditReportGenerator
    db = SessionLocal()
    ledger = TrustLedgerSystem(db)
    learner = LearningEngine(db, ledger)

    logger.info(f"Ingesting report from {file_path}...")
    report = load_json(file_path, fatal=True)

    report_id = report.get("report_id") or report.get("script_filename", "unknown")
    ledger.log_event("INGEST_REPORT", {"report_id": report_id}, "CLI_User")

    new_config = learner.process_execution_feedback(report)

    # --- PDF AUDIT GENERATION (Strategic Documentation) ---
    logger.info("Generating professional Audit PDF...")
    try:
        # Resolve path to report directory for co-lo discovery
        report_dir = os.path.dirname(os.path.abspath(file_path))

        # Resolve paths to upstream tools (Flexible Discovery)
        # 1. Explicit path provided via CLI
        # 2. Co-located with the ingested report (New Run pattern)
        # 3. Fallback to default centralized Tool3/Tool4 locations
        
        final_t3 = t3_path
        if not final_t3:
            # Check for co-location
            alt_t3 = os.path.join(report_dir, "trajectory_forecast.json")
            if os.path.exists(alt_t3):
                final_t3 = alt_t3
            else:
                # Standard Fallback
                final_t3 = os.path.normpath(os.path.join(_TOOL6_DIR, "..", "Tool3", "trajectory_forecast.json"))

        final_t4 = t4_path
        if not final_t4:
            # Check for co-location
            alt_t4 = os.path.join(report_dir, "response_plan.json")
            if os.path.exists(alt_t4):
                final_t4 = alt_t4
            else:
                # Standard Fallback
                final_t4 = os.path.normpath(os.path.join(_TOOL6_DIR, "..", "Tool4", "response_plan.json"))

        logger.info(f"Using Tool3 data: {final_t3}")
        logger.info(f"Using Tool4 data: {final_t4}")

        t3_data = load_json(final_t3, fatal=False) if os.path.exists(final_t3) else []
        t4_data = load_json(final_t4, fatal=False) if os.path.exists(final_t4) else []
        
        if t3_data is None: t3_data = [] # Handle load failure
        if t4_data is None: t4_data = []

        # Target directory for PDFs
        final_output_dir = output_dir or os.path.join(_TOOL6_DIR, "deployments")
        os.makedirs(final_output_dir, exist_ok=True)
        
        generator = AuditReportGenerator(final_output_dir)
        pdf_abs = generator.generate_pdf(t3_data, t4_data, report, new_config)
        logger.info(f"Audit PDF generated: {pdf_abs}")
        
        # Convert to relative path for backend API (if possible, fallback to absolute)
        tools_root = os.path.dirname(_TOOL6_DIR)
        try:
            pdf_rel = os.path.relpath(pdf_abs, tools_root).replace("\\", "/")
        except ValueError:
            # Handle cross-drive paths on Windows
            pdf_rel = pdf_abs
        
        extra_info = {"pdf_audit_path": pdf_rel, "pdf_audit_filename": os.path.basename(pdf_abs)}
    except Exception as e:
        logger.warning(f"Failed to generate Audit PDF: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        extra_info = {}

    # ── Rich Summary Panel ─────────────────────────────────────────────
    console.print(Panel(
        f"[bold green]✅ Learning Complete & Audit Generated[/bold green]\n"
        f"Model updated: [cyan]{new_config.version_id}[/cyan]\n"
        f"Audit Report: [yellow]{extra_info.get('pdf_audit_filename', 'FAILED')}[/yellow]\n"
        f"Narrative: [italic]{getattr(new_config, '_narrative', '')}[/italic]",
        title="Governance Update",
        border_style="green"
    ))

    # Build extra context for status.json
    extra_context = {
        "source_file": file_path,
        "report_id": report_id,
        "new_model_version": new_config.version_id,
        "actions_processed": getattr(new_config, '_actions_processed', 0),
        "domains_covered": getattr(new_config, '_domains_covered', []),
        "high_urgency_count": getattr(new_config, '_high_urgency_count', 0),
        "approval_required": getattr(new_config, '_approval_required', 0),
        "action_types": getattr(new_config, '_action_types', []),
        "is_script_gen": getattr(new_config, '_is_script_gen', False),
        "narrative": getattr(new_config, '_narrative', ''),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra_info
    }

    display_status(db, extra_context=extra_context)
    db.close()


def main():
    parser = argparse.ArgumentParser(description="Tool 6: Governance & Learning Engine")
    subparsers = parser.add_subparsers(dest="command")

    parser_ingest = subparsers.add_parser("ingest", help="Ingest a Tool 5 execution/script report")
    parser_ingest.add_argument("report_path", help="Path to execution_report.json")
    parser_ingest.add_argument("--t3-path", help="Optional path to trajectory_forecast.json")
    parser_ingest.add_argument("--t4-path", help="Optional path to response_plan.json")
    parser_ingest.add_argument("--output-dir", help="Optional directory to save the PDF audit report")

    subparsers.add_parser("status", help="Display current governance status")
    subparsers.add_parser("init", help="Initialize the governance database")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        logger.info("Governance database initialized.")
        # Create genesis config if none exists
        db = SessionLocal()
        existing = db.query(ModelConfiguration).filter_by(is_active=1).first()
        if not existing:
            genesis = ModelConfiguration(
                version_id="v1.0-genesis",
                is_active=1,
                containment_threshold=0.6,
                disruptive_threshold=0.85,
                trust_momentum=0.0,
                success_streak=0,
                failure_streak=0,
                risk_weights={"T1021": 0.8, "T1046": 0.4}
            )
            db.add(genesis)
            db.commit()
            logger.info("Genesis model configuration created.")
        # Write an initial status.json so the UI shows live data immediately
        display_status(db)
        db.close()

    elif args.command == "ingest":
        process_ingest(
            args.report_path, 
            t3_path=args.t3_path, 
            t4_path=args.t4_path, 
            output_dir=args.output_dir
        )

    elif args.command == "status":
        db = SessionLocal()
        display_status(db)
        db.close()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

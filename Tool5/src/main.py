import argparse
import sys
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .engine import ExecutionEngine
from .domain import ExecutionStatus, ExecutionMode

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool5")
console = Console()

def load_response_plan(path: str):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {path}")
        sys.exit(1)

def visualize_execution_board(report):
    """
    Renders the RESPONSE EXECUTION BOARD.
    """
    table = Table(title="🛡️ CONTROLLED RESPONSE EXECUTION BOARD 🛡️", show_header=True, header_style="bold white on red")
    table.add_column("Target", style="cyan")
    table.add_column("Action", style="bold white")
    table.add_column("Mode", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Rollback?", justify="center", style="dim white")
    table.add_column("Details", style="dim")

    for ex in report.executions:
        mode_style = "dim"
        if ex.execution_mode == ExecutionMode.AUTO: mode_style = "green bold"
        elif ex.execution_mode == ExecutionMode.STAGED: mode_style = "yellow"
        elif ex.execution_mode == ExecutionMode.REJECTED: mode_style = "red"
        
        status_style = "white"
        if ex.final_status == ExecutionStatus.SUCCESS: status_style = "green"
        elif ex.final_status == ExecutionStatus.PENDING: status_style = "yellow"
        elif ex.final_status == ExecutionStatus.BLOCKED: status_style = "red"
        
        rb = "Yes" if ex.rollback_token else "No"
        
        table.add_row(
            ex.target,
            ex.action_name,
            f"[{mode_style}]{ex.execution_mode}[/{mode_style}]",
            f"[{status_style}]{ex.final_status}[/{status_style}]",
            rb,
            ex.message
        )
        
    console.print(table)
    
    # Summary Panel
    stats = report.summary_stats
    console.print(Panel(
        f"[green]Success: {stats['success']}[/green] | [yellow]Pending: {stats['pending']}[/yellow] | [red]Blocked: {stats['blocked']}[/red] | Total: {stats['total']}",
        title="Execution Summary"
    ))
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(description="Tool 5: Controlled Response Execution Engine")
    parser.add_argument("input_plan", help="Path to Tool 4 output (response_plan.json)")
    parser.add_argument("--output", default="execution_report.json", help="Output path for JSON report")
    args = parser.parse_args()
    
    logger.info("Initializing Execution Engine...")
    engine = ExecutionEngine()
    
    logger.info(f"Loading input from {args.input_plan}...")
    plan = load_response_plan(args.input_plan)
    
    report = engine.process_plan(plan)
    
    # Visualize
    visualize_execution_board(report)
        
    # Write Output
    with open(args.output, "w") as f:
        f.write(report.model_dump_json(indent=2))
        
    logger.info(f"Execution Report written to {args.output}")
    logger.info(f"Audit Log written to execution_audit.log")

if __name__ == "__main__":
    main()

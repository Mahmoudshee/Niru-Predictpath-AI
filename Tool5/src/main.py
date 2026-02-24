import argparse
import sys
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .engine import ScriptGeneratorEngine

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool5")
console = Console()


def load_response_plan(path: str):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {path}")
        sys.exit(1)


def visualize_script_board(report: dict):
    """Renders the Script Generation Summary Board."""

    # ── Intro panel ─────────────────────────────────────────────────────────
    console.print(Panel(
        "[bold cyan]Tool 5: Remediation Script Generator[/bold cyan]\n"
        "[white]This tool does NOT execute any commands automatically.[/white]\n"
        "[dim]It generates a ready-to-run PowerShell script based on the AI decisions from Tool 4.\n"
        "Download the script, review it, and run it manually as Administrator.[/dim]",
        title="[bold white]PREDICTPATH AI — SCRIPT GENERATOR[/bold white]",
        border_style="cyan"
    ))

    # ── Actions table ────────────────────────────────────────────────────────
    table = Table(
        title="GENERATED REMEDIATION ACTIONS",
        show_header=True,
        header_style="bold white on dark_blue"
    )
    table.add_column("Session", style="cyan", max_width=25)
    table.add_column("Domain", justify="center", style="bold")
    table.add_column("Action", style="bold white")
    table.add_column("Target", style="dim white")
    table.add_column("Urgency", justify="center")
    table.add_column("Approval?", justify="center")

    for act in report.get("actions_included", []):
        domain = act["domain"]
        domain_style = "green" if domain == "Network" else "yellow" if domain == "Endpoint" else ("cyan" if domain == "Web" else "dim")
        urgency_style = "red bold" if act["urgency"] == "Critical" else "yellow"
        approval_text = "[red]YES[/red]" if act["requires_approval"] else "[green]No[/green]"

        table.add_row(
            act["session_id"][:24],
            f"[{domain_style}]{domain}[/{domain_style}]",
            act["action_type"],
            act["target"],
            f"[{urgency_style}]{act['urgency']}[/{urgency_style}]",
            approval_text,
        )

    console.print(table)

    # ── Script path panel ────────────────────────────────────────────────────
    script_path = report.get("script_path", "N/A")
    guideline_path = report.get("guideline_path", "N/A")
    total = report.get("total_actions", 0)
    staged = report.get("staged_count", 0)

    console.print(Panel(
        f"[bold green]Automated Script ready for download:[/bold green]\n"
        f"[bold white]{script_path}[/bold white]\n\n"
        f"[bold cyan]Tactical Remediation Guideline (Web/Manual Context):[/bold cyan]\n"
        f"[bold white]{guideline_path}[/bold white]\n\n"
        f"[dim]Total actions: {total}  |  Requires manual approval: {staged}[/dim]\n\n"
        f"[yellow]HOW TO RUN:[/yellow]\n"
        f"[dim]1. Use the .ps1 script for automated Network/Endpoint tasks.\n"
        f"2. Follow the .md guideline for Web analysis and manual console steps.[/dim]",
        title="[bold green]REMEDIATION PACKAGE GENERATED[/bold green]",
        border_style="green"
    ))


def main():
    parser = argparse.ArgumentParser(description="Tool 5: Remediation Script Generator")
    parser.add_argument("input_plan", help="Path to Tool 4 output (response_plan.json)")
    parser.add_argument("--output", default="execution_report.json", help="Output path for JSON report")
    args = parser.parse_args()

    logger.info("Initializing Script Generator Engine...")
    engine = ScriptGeneratorEngine()

    logger.info(f"Loading response plan from {args.input_plan}...")
    plan = load_response_plan(args.input_plan)

    report = engine.generate(plan)

    # Visualize
    visualize_script_board(report)

    # Write JSON report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Execution report written to {args.output}")
    logger.info(f"Remediation script: {report['script_path']}")


if __name__ == "__main__":
    main()

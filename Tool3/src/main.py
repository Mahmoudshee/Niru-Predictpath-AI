import argparse
import sys
import json
import logging
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .domain import PredictionSummary, CurrentState
from .predictor import TrajectoryEngine, get_technique_name

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool3")
console = Console()

def load_tool2_report(path: str):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {path}")
        sys.exit(1)

def visualize_forecast(summary: PredictionSummary):
    """
    Renders a premium visual forecast to the terminal.
    """
    # Header
    state_desc = ", ".join([get_technique_name(t) for t in summary.current_state.observed_techniques])
    header = Panel(
        f"[bold cyan]Session:[/bold cyan] {summary.session_id}\n"
        f"[bold yellow]Context:[/bold yellow] {state_desc}\n"
        f"[bold blue]Blast Radius:[/bold blue] {len(summary.current_state.host_scope)} hosts\n"
        f"[bold magenta]Model Confidence:[/bold magenta] {summary.aggregate_confidence:.0%}",
        title="Predictive Attack Trajectory (Perfected)",
        subtitle=f"Model: {summary.model_version}"
    )
    console.print(header)
    
    if summary.mentor_narrative:
        console.print(Panel(f"[italic white]{summary.mentor_narrative}[/italic white]", title="[bold]Strategic Insight[/bold]", border_style="cyan"))

    if summary.suppression_reason:
        console.print(f"[bold red]Predictions Suppressed:[/bold red] {summary.suppression_reason}\n")
        return

    # Table of Futures
    table = Table(title="Projected Scenarios", show_header=True, header_style="bold magenta")
    table.add_column("Prob", justify="right", style="cyan")
    table.add_column("Risk", justify="center")
    table.add_column("Likely Time Window", justify="center")
    table.add_column("Attacker's Next Steps", style="green")
    
    for path in summary.predicted_scenarios:
        # Format Path
        seq_str = path.human_readable_sequence
        
        # Colorize Risk
        risk_color = "green"
        if path.risk_level == "Critical": risk_color = "red bold blink"
        elif path.risk_level == "High": risk_color = "red"
        elif path.risk_level == "Medium": risk_color = "yellow"
        
        # Time Window
        t_win = path.time_window_text
        
        table.add_row(
            f"{path.probability:.1%}",
            f"[{risk_color}]{path.risk_level}[/{risk_color}]",
            t_win,
            seq_str
        )
        
    console.print(table)
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(description="Tool 3: Predictive Attack Trajectory Engine (Perfected)")
    parser.add_argument("input_report", help="Path to Tool 2 output (path_report.json)")
    parser.add_argument("--output", default="trajectory_forecast.json", help="Output path for JSON predictions")
    args = parser.parse_args()
    
    logger.info("Initializing Context-Aware Engine...")
    engine = TrajectoryEngine()
    
    logger.info(f"Loading input from {args.input_report}...")
    tool2_data = load_tool2_report(args.input_report)
    
    forecasts = []
    
    # Iterate over sessions from Tool 2
    for session_report in tool2_data:
        s_id = str(session_report.get("session_id", "Unknown Session"))
        
        # Resilient score extraction (handles alias names)
        risk_score = session_report.get("path_anomaly_score")
        if risk_score is None:
            risk_score = session_report.get("Score", 0.0)
        risk_score = float(risk_score)
        
        blast_radius = session_report.get("blast_radius", [])
        vuln_summary = session_report.get("vulnerability_summary", [])
        
        # --- REAL DATA EXTRACTION ---
        # 1. Use actual techniques detected by Tool 2
        observed = session_report.get("observed_techniques", [])
        if not observed:
            # Check if Tool 2 provided them in a different key or we need to infer from summary
            vuln_blob = " ".join(vuln_summary).lower()
            if any(k in vuln_blob for k in ["cache", "comment", "exposure", "info"]):
                observed = ["T1592"]
            elif any(k in vuln_blob for k in ["permission", "access", "auth"]):
                observed = ["T1078"]
            elif "protection" in vuln_blob:
                observed = ["T1562"]
            elif risk_score > 30:
                observed = ["T1190"]
            else:
                observed = ["T1595"]
            
        graph_depth = len(observed)
        
        # 2. Exhaustive extraction of security identifiers
        observed_ids = []
        import re
        for v_str in vuln_summary:
            matches = re.findall(r'(CVE-\d{4}-\d+|CWE-\d+)', v_str, re.I)
            observed_ids.extend(matches)

        # Create State with REAL context
        current_state = CurrentState(
            observed_techniques=observed,
            last_seen_timestamp=datetime.now(timezone.utc),
            graph_depth=graph_depth,
            host_scope=blast_radius,
            observed_vulnerabilities=list(set(observed_ids))
        )

        summary = engine.predict(
            session_id=s_id,
            current_state=current_state,
            current_risk=risk_score
        )
        
        # Avoid duplicate asset noise: Flag if we've seen this trajectory recently
        # (Simplified: just add to the list)
        forecasts.append(summary.model_dump(mode='json'))
        visualize_forecast(summary)
        
    # Write Output
    with open(args.output, "w") as f:
        json.dump(forecasts, f, indent=2)
        
    logger.info(f"Forecasts written to {args.output}")

if __name__ == "__main__":
    main()

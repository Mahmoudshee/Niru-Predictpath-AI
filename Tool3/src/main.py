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
    
    if summary.suppression_reason:
        console.print(f"[bold red]Predictions Suppressed:[/bold red] {summary.suppression_reason}\n")
        return

    # Table of Futures
    table = Table(title="Projected Scenarios", show_header=True, header_style="bold magenta")
    table.add_column("Prob", justify="right", style="cyan")
    table.add_column("Risk", justify="center")
    table.add_column("Time Window", justify="center")
    table.add_column("Sequence", style="green")
    table.add_column("Evidence", style="dim white")
    
    for path in summary.predicted_scenarios:
        # Format Path
        seq_str = " -> ".join([f"{t}" for t in path.sequence])
        
        # Colorize Risk
        risk_color = "green"
        if path.risk_level == "Critical": risk_color = "red bold blink"
        elif path.risk_level == "High": risk_color = "red"
        elif path.risk_level == "Medium": risk_color = "yellow"
        
        # Time Window
        t_win = f"{path.reaction_time_window.min_seconds}s-{path.reaction_time_window.max_seconds}s"
        
        # Evidence snippet
        # Show specific host names if mentioned
        ev_snip = path.explainability.positive_evidence[0] if path.explainability.positive_evidence else "None"
        if len(path.explainability.positive_evidence) > 1:
             ev_snip += f" (+{len(path.explainability.positive_evidence)-1} more)"
        
        table.add_row(
            f"{path.probability:.1%}",
            f"[{risk_color}]{path.risk_level}[/{risk_color}]",
            t_win,
            seq_str,
            ev_snip
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
        s_id = str(session_report.get("session_id"))
        risk_score = float(session_report.get("path_anomaly_score", 0.0))
        blast_radius = session_report.get("blast_radius", [])
        
        # --- SESSION DIFFERENTIATION LOGIC ---
        # Infer context from Tool 2 signals to create distinct profiles
        
        observed = ["T1078"] # Default: Valid User
        graph_depth = 1
        
        if "u999" in s_id or risk_score > 8.0:
            # High Risk / Admin -> Likely Brute Force or Lateral Mov
            observed = ["T1110", "T1078", "T1046"] 
            graph_depth = 3
        elif risk_score > 4.0:
            # Medium Risk -> Suspicious login
            observed = ["T1110", "T1078"]
            graph_depth = 2
        elif len(blast_radius) > 2:
             # Wide blast radius implies discovery/lateral
            observed = ["T1078", "T1046"]
            graph_depth = 2
            
        # Create State
        current_state = CurrentState(
            observed_techniques=observed,
            last_seen_timestamp=datetime.now(timezone.utc),
            graph_depth=graph_depth,
            host_scope=blast_radius
        )

        summary = engine.predict(
            session_id=s_id,
            current_state=current_state,
            current_risk=risk_score
        )
        
        forecasts.append(summary.model_dump(mode='json'))
        visualize_forecast(summary)
        
    # Write Output
    with open(args.output, "w") as f:
        json.dump(forecasts, f, indent=2)
        
    logger.info(f"Forecasts written to {args.output}")

if __name__ == "__main__":
    main()

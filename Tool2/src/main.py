import argparse
import sys
import json
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from .ingest import DataIngester
from .engine import GraphEngine

console = Console()

def visualize_path(session, report):
    """
    Key function to render the Directed Temporal Graph in ASCII using Rich.
    """
    # Header
    risk_color = "red" if report.business_risk_level == "High" else "yellow" if report.business_risk_level == "Medium" else "green"
    
    console.print(Panel(
        f"[bold {risk_color}]BUSINESS RISK: {report.business_risk_level}[/bold {risk_color}]\n"
        f"[bold white]WHAT HAPPENED:[/bold white] {report.plain_language_summary}\n\n"
        f"[dim white]Technical Session: {session.session_id}[/dim white]", 
        title=f"[bold]EXECUTIVE SUMMARY[/bold]",
        subtitle=f"Anomaly Score: {report.path_anomaly_score:.2f}",
        border_style=risk_color
    ))
    
    # Path Tree
    tree = Tree("[bold yellow]Root Cause (Entry Point)[/bold yellow]")
    tree.add(f"Event: {report.root_cause_node} | User: {session.user}")
    
    # Build a simple visualization of the sequence
    # Limit to first 10 events to avoid screen overflow
    last_node = tree
    for i, event in enumerate(session.events[:10]):
        # Calculate time delta from previous
        delta_msg = ""
        if i > 0:
            prev = session.events[i-1]
            dt = (event.timestamp - prev.timestamp).total_seconds()
            delta_msg = f"  ⬇  (+{dt:.2f}s)"
            
        node_text = Text()
        if delta_msg:
            # Add a 'node' just for the arrow/time if we want strict tree, 
            # or just append to the visual flow. 
            # Tree structures are hierarchical, linear paths are hard to represent perfectly as trees.
            # Let's just make a linear chain in the tree for specific events.
            pass

        # Stylize based on score/criticality
        style = "green"
        if event.confidence_score < 0.5: style = "red"
        
        step_node = last_node.add(f"[{style}]{event.mitre_technique or 'Unknown'} ({event.event_id})[/{style}]")
        step_node.add(f"Host: {event.source_host} -> {event.target_host or 'N/A'}")
        last_node = step_node

    if len(session.events) > 10:
        last_node.add(f"... {len(session.events) - 10} more events ...")

    # Blast Radius
    blast_table = Table(title="Blast Radius")
    blast_table.add_column("Host", style="cyan")
    for host in report.blast_radius:
        blast_table.add_row(host)
        
    # Vulnerability Intelligence Context
    if report.vulnerability_summary:
        vuln_table = Table(title="Vulnerability Intelligence Context", show_header=True, header_style="bold magenta")
        vuln_table.add_column("Observed CVE-ID", style="red")
        vuln_table.add_column("Risk Context", style="yellow")
        
        for vuln in report.vulnerability_summary:
            if "(" in vuln:
                name_and_rest = vuln.split(" (", 1)
                attack_name = name_and_rest[0]
                details = "(" + name_and_rest[1] if len(name_and_rest) > 1 else ""
                vuln_table.add_row(attack_name, details)
            else:
                vuln_table.add_row(vuln, "")
        console.print(vuln_table)

    if report.cwe_clusters:
        cwe_text = ", ".join([f"[bold cyan]{c}[/bold cyan]" for c in report.cwe_clusters])
        console.print(Panel(cwe_text, title="CWE Taxonomy Clusters", border_style="cyan"))

    # Predictions
    pred_text = ""
    for p in report.prediction_vector:
        pred_text += f"[bold blue]{p.next_node}[/bold blue] ({p.probability:.0%}) -> "

    console.print(tree)
    console.print(blast_table)
    console.print(Panel(f"Predicted Trajectory: {pred_text}END", title="AI Forecast", border_style="blue"))
    console.print("\n" + "="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Tool 2: Behavioral Path Reconstruction Engine")
    parser.add_argument("input_file", help="Path to input Parquet file (from Tool 1)")
    parser.add_argument("--threshold", type=float, default=5.0, help="Anomaly score threshold to alert on")
    
    args = parser.parse_args()
    
    ingester = DataIngester(args.input_file)
    engine = GraphEngine()
    
    if not ingester.verify_integrity():
        console.print("[bold red]FATAL: Integrity Check Failed![/bold red]")
        sys.exit(1)
        
    sessions = ingester.load_sessions()
    console.print(f"[bold green]Loaded {len(sessions)} sessions.[/bold green]")
    
    reports = []
    
    for session in sessions:
        report = engine.build_and_analyze(session)
        if not report:
            continue
            
        reports.append(report.model_dump(mode='json'))
        
        # Visualize if high priority or anomalous
        if session.is_high_priority or report.path_anomaly_score >= args.threshold:
            visualize_path(session, report)
            
    # Dump full report
    with open("path_report.json", "w") as f:
        json.dump(reports, f, indent=2)
        
    console.print("[bold green]Analysis Complete. Report saved to path_report.json[/bold green]")

if __name__ == "__main__":
    main()

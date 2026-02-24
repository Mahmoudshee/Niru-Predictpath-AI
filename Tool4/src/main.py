import argparse
import sys
import json
import logging
from collections import defaultdict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .engine import DecisionEngine

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PredictPath-Tool4")
console = Console()

def load_tool3_forecast(path: str):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {path}")
        sys.exit(1)

def visualize_decision_board(decisions: list):
    """
    Renders the SOC Response Board (Consolidated by Principal).
    """
    table = Table(title="ADAPTIVE RESPONSE PRIORITIZATION BOARD (ELITE TIER)", show_header=True, header_style="bold white on blue")
    table.add_column("Rank", justify="center", style="bold white")
    table.add_column("Principal / Session", style="cyan")
    table.add_column("Urgency", justify="center")
    table.add_column("Conf (Boosted)", justify="center", style="magenta")
    table.add_column("Action (Intent)", style="bold green")
    table.add_column("Risk Reduction", style="white")
    table.add_column("Rejected Strategy", style="red")
    table.add_column("If Ignored", style="dim yellow") # New Column

    # De-Duplication / Merging Logic
    # Group by Target Identifier (User/Host)
    grouped = defaultdict(list)
    for d_obj in decisions:
        d = d_obj if isinstance(d_obj, dict) else d_obj.model_dump()
        target_id = d["recommended_actions"][0]["target"]["identifier"]
        grouped[target_id].append(d)

    # Sort groups by the highest rank within them
    sorted_groups = sorted(grouped.items(), key=lambda x: min([item['priority_rank'] for item in x[1]]))

    final_rank = 1
    for target_id, group_items in sorted_groups:
        # Pick representative (highest urgency/rank)
        primary = group_items[0] 
        
        # --- NEW: Strategic Panel for Principal ---
        if primary.get("mentor_summary"):
             console.print(Panel(f"[italic white]{primary['mentor_summary']}[/italic white]", title=f"[bold]Strategy: {target_id}[/bold]", border_style="cyan"))

        count = len(group_items)
        session_label = f"{target_id}"
        if count > 1:
            session_label += f"\n({count} correlated sessions)"
            #session_label += f"\nPrimary: {primary['session_id']}"
        else:
             session_label += f"\n{primary['session_id']}"

        urgency = primary.get("urgency_level", "Low")
        urg_style = "green"
        if urgency == "Critical": urg_style = "red bold blink"
        elif urgency == "High": urg_style = "red"
        elif urgency == "Medium": urg_style = "yellow"
        
        main_action = primary["recommended_actions"][0]
        # Include Guidelines in Action Text for terminal viewing
        guidelines = main_action.get("mitigation_guidelines", [])
        guideline_text = "\n[dim]" + "\n".join([f"  • {g}" for g in guidelines]) + "[/dim]" if guidelines else ""
        action_text = f"{main_action['action_type']}{guideline_text}"
        
        rr = main_action["justification"]["risk_reduction"]
        rr_text = f"-{rr['absolute']:.0%} Abs."
        
        rejected_text = "-"
        if primary.get("rejected_actions"):
            # Format nicely
            lines = []
            for r in primary['rejected_actions']:
                lines.append(f"{r['candidate_action']}: {r['rejection_reasons'][0]}") # Show first reason
            rejected_text = "\n".join(lines)

        conf_text = f"{primary['decision_confidence']:.0%}"
        
        ignored_text = primary['decision_explainability']['what_happens_if_ignored']

        table.add_row(
            str(final_rank),
            session_label,
            f"[{urg_style}]{urgency}[/{urg_style}]",
            conf_text,
            action_text,
            rr_text,
            rejected_text,
            ignored_text
        )
        final_rank += 1
        
    console.print(table)
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(description="Tool 4: Adaptive Response Engine (Finalized)")
    parser.add_argument("input_forecast", help="Path to Tool 3 output (trajectory_forecast.json)")
    parser.add_argument("--output", default="response_plan.json", help="Output path for JSON decisions")
    args = parser.parse_args()
    
    logger.info("Initializing Decision Engine...")
    engine = DecisionEngine()
    
    logger.info(f"Loading input from {args.input_forecast}...")
    forecasts = load_tool3_forecast(args.input_forecast)
    
    decisions = []
    
    # Phase 0: Analyze Correlations
    correlation_map = engine.analyze_correlations(forecasts)
    
    # Phase 1: Evaluate Sessions
    raw_decisions = []
    for session_forecast in forecasts:
        s_id = session_forecast.get("session_id")
        correlation_ctx = correlation_map.get(s_id, {})
        decision = engine.evaluate_session(session_forecast, correlation_ctx)
        raw_decisions.append(decision)
        
    # Phase 2: STRATEGIC AGGREGATION (Eliminating Duplication)
    aggregated_map = {}
    merged_counts = defaultdict(int)
    
    for d in raw_decisions:
        target = d.recommended_actions[0].target.identifier
        key = f"{target}"
        
        if key not in aggregated_map:
            aggregated_map[key] = d
            merged_counts[key] = 1
        else:
            merged_counts[key] += 1
            existing = aggregated_map[key]
            urgency_levels = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            
            # Switch to the new decision if it's more urgent or higher confidence
            if urgency_levels[d.urgency_level] > urgency_levels[existing.urgency_level]:
                aggregated_map[key] = d
            elif urgency_levels[d.urgency_level] == urgency_levels[existing.urgency_level]:
                if d.decision_confidence > existing.decision_confidence:
                    aggregated_map[key] = d
    
    # Finalize Aggregated Decisions with visibility notes
    for key, d in aggregated_map.items():
        count = merged_counts[key]
        if count > 1:
            d.mentor_summary += f" [Consolidated Campaign: {count} correlated asset hits merged into this response]"
            
    decisions = list(aggregated_map.values())
        
    # Global Ranking
    urgency_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    decisions.sort(
        key=lambda x: (urgency_map[x.urgency_level], x.priority_rank),
        reverse=True
    )
    
    # Update Rank
    final_output = []
    for i, d in enumerate(decisions, 1):
        d.priority_rank = i
        final_output.append(d.model_dump(mode='json'))
        
    # Visualize
    visualize_decision_board(final_output)
        
    # Write Output
    with open(args.output, "w") as f:
        json.dump(final_output, f, indent=2)
        
    logger.info(f"Response Plan written to {args.output}")

if __name__ == "__main__":
    main()

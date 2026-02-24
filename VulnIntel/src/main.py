"""Main CLI entry point for VulnIntel."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import print as rprint

from src.config import DATABASE_PATH
from src.database.connection import init_database, vacuum_database
from src.ingestors.cve_ingester import CVEIngester
from src.ingestors.cwe_ingester import CWEIngester
from src.ingestors.kev_ingester import KEVIngester
from src.query.api import VulnIntelAPI
from src.utils.logger import setup_logging, get_logger

# Initialize console with forced UTF-8 for redirect support
console = Console(force_terminal=True, soft_wrap=True)
logger = get_logger(__name__)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize database."""
    try:
        init_database(force=args.force)
        console.print("✅ Database initialized successfully", style="green")
        return 0
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")
        return 1


def cmd_sync(args: argparse.Namespace) -> int:
    """Synchronize data from sources."""
    success = True
    
    try:
        if args.all or args.cve:
            console.print("\n[bold]Syncing CVE data...[/bold]")
            ingester = CVEIngester()
            feed = args.feed or "recent"
            if not ingester.sync(force=args.force, feed=feed):
                success = False
        
        if args.all or args.cwe:
            console.print("\n[bold]Syncing CWE data...[/bold]")
            ingester = CWEIngester()
            if not ingester.sync(force=args.force):
                success = False
        
        if args.all or args.kev:
            console.print("\n[bold]Syncing KEV data...[/bold]")
            ingester = KEVIngester()
            if not ingester.sync(force=args.force):
                success = False
        
        if success:
            console.print("\n✅ Sync completed successfully", style="green")
            return 0
        else:
            console.print("\n⚠️  Sync completed with errors", style="yellow")
            return 1
            
    except Exception as e:
        console.print(f"\n❌ Sync failed: {e}", style="red")
        logger.exception("Sync failed")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show sync status."""
    try:
        api = VulnIntelAPI()
        stats = api.get_vuln_stats()
        
        # Sync status table
        table = Table(title="Sync Status", show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Last Sync", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Records", style="yellow")
        
        for source, status in stats.get("sync_status", {}).items():
            table.add_row(
                source.upper(),
                status.get("last_sync_time", "Never"),
                status.get("last_sync_status", "Unknown"),
                str(status.get("records_processed", 0))
            )
        
        console.print(table)
        
        # Database stats
        console.print(f"\n[bold]Database Statistics:[/bold]")
        console.print(f"  CVEs: {stats.get('cve', 0):,}")
        console.print(f"  CWEs: {stats.get('cwe', 0):,}")
        console.print(f"  KEV Entries: {stats.get('kev', 0):,}")
        console.print(f"  Recent CVEs (30d): {stats.get('recent_cves_30d', 0):,}")
        
        return 0
        
    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Show detailed statistics."""
    try:
        api = VulnIntelAPI()
        stats = api.get_vuln_stats()
        
        console.print("\n[bold]Vulnerability Intelligence Statistics[/bold]\n")
        
        # Overall counts
        console.print(f"Total CVEs: {stats.get('cve', 0):,}")
        console.print(f"Total CWEs: {stats.get('cwe', 0):,}")
        console.print(f"Total KEV Entries: {stats.get('kev', 0):,}")
        console.print(f"Recent CVEs (30 days): {stats.get('recent_cves_30d', 0):,}\n")
        
        # CVE severity breakdown
        severity_table = Table(title="CVE Severity Distribution")
        severity_table.add_column("Severity", style="cyan")
        severity_table.add_column("Count", style="yellow")
        
        for severity, count in stats.get("cve_by_severity", {}).items():
            severity_table.add_row(severity, f"{count:,}")
        
        console.print(severity_table)
        
        # KEV ransomware stats
        console.print(f"\n[bold]KEV Ransomware Statistics:[/bold]")
        for status, count in stats.get("kev_ransomware", {}).items():
            console.print(f"  {status}: {count:,}")
        
        return 0
        
    except Exception as e:
        console.print(f"❌ Stats failed: {e}", style="red")
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    """Query vulnerability data."""
    try:
        api = VulnIntelAPI()
        
        if args.type == "cve":
            cve = api.get_cve_by_id(args.id)
            if cve:
                rprint(cve)
            else:
                console.print(f"CVE not found: {args.id}", style="yellow")
        
        elif args.type == "cwe":
            cwe = api.get_cwe_by_id(args.id)
            if cwe:
                rprint(cwe)
            else:
                console.print(f"CWE not found: {args.id}", style="yellow")
        
        elif args.type == "cwe-cves":
            cves = api.get_cves_by_cwe(args.id, limit=args.limit)
            console.print(f"\nFound {len(cves)} CVEs for {args.id}\n")
            for cve in cves:
                console.print(f"  {cve['cve_id']}: {cve['cvss_v3_score']} - {cve['description'][:80]}...")
        
        elif args.type == "high-risk":
            cves = api.get_high_risk_cves(
                min_cvss=args.min_cvss,
                kev_only=args.kev_only,
                limit=args.limit
            )
            console.print(f"\nFound {len(cves)} high-risk CVEs\n")
            for cve in cves:
                exploited = "🔥" if cve.get("is_exploited") else "  "
                console.print(f"{exploited} {cve['cve_id']}: {cve['cvss_v3_score']} - {cve['description'][:80]}...")
        
        elif args.type == "is-exploited":
            if api.is_cve_exploited(args.id):
                console.print(f"⚠️  {args.id} is in the KEV catalog (actively exploited)", style="red bold")
            else:
                console.print(f"✓ {args.id} is not in the KEV catalog", style="green")
        
        elif args.type == "kev":
            entries = api.get_kev_entries(days_back=args.days, ransomware_only=args.ransomware)
            console.print(f"\nFound {len(entries)} KEV entries\n")
            for entry in entries:
                ransomware = "💀" if entry.get("known_ransomware_use") == "Known" else "  "
                console.print(f"{ransomware} {entry['cve_id']}: {entry['vulnerability_name']} (added: {entry['date_added']})")
        
        return 0
        
    except Exception as e:
        console.print(f"❌ Query failed: {e}", style="red")
        logger.exception("Query failed")
        return 1


def cmd_vacuum(args: argparse.Namespace) -> int:
    """Vacuum database to reclaim space."""
    try:
        vacuum_database()
        console.print("✅ Database vacuumed successfully", style="green")
        return 0
    except Exception as e:
        console.print(f"❌ Vacuum failed: {e}", style="red")
        return 1


def cmd_daemon(args: argparse.Namespace) -> int:
    """Run as a daemon to periodically sync data."""
    import schedule
    import time
    from datetime import datetime
    
    console.print("[bold cyan]VulnIntel Daemon Started[/bold cyan]")
    console.print(f"Syncing every {UPDATE_INTERVALS['cve']/60} minutes for CVEs")
    console.print(f"Syncing every {UPDATE_INTERVALS['kev']/3600} hours for KEVs")
    console.print(f"Syncing every {UPDATE_INTERVALS['cwe']/86400} days for CWEs")
    console.print("\nPress Ctrl+C to stop.\n")

    def job():
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"[{now}] [yellow]Background Sync Started...[/yellow]")
        
        # We call the sync functions directly
        cve_ing = CVEIngester()
        cwe_ing = CWEIngester()
        kev_ing = KEVIngester()
        
        cve_ing.sync(feed="recent")
        cwe_ing.sync()
        kev_ing.sync()
        
        console.print(f"[{now}] [green]Background Sync Completed.[/green]")

    # Schedule the jobs based on config intervals
    # Note: schedule.every(X).seconds is easiest for testing/config harmony
    schedule.every(UPDATE_INTERVALS['cve']).seconds.do(job)
    
    # Run once at startup
    job()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        console.print("\n[bold red]Daemon stopped by user.[/bold red]")
        return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VulnIntel - Vulnerability Intelligence Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--force", action="store_true", help="Force reinitialize (deletes existing data)")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize data from sources")
    sync_parser.add_argument("--all", action="store_true", help="Sync all sources")
    sync_parser.add_argument("--cve", action="store_true", help="Sync CVE data")
    sync_parser.add_argument("--cwe", action="store_true", help="Sync CWE data")
    sync_parser.add_argument("--kev", action="store_true", help="Sync KEV data")
    sync_parser.add_argument("--force", action="store_true", help="Force sync even if not due")
    sync_parser.add_argument("--feed", help="CVE feed to sync (recent, modified, or year)")
    
    # Status command
    subparsers.add_parser("status", help="Show sync status")
    
    # Stats command
    subparsers.add_parser("stats", help="Show detailed statistics")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query vulnerability data")
    query_parser.add_argument("type", choices=["cve", "cwe", "cwe-cves", "high-risk", "is-exploited", "kev"])
    query_parser.add_argument("id", nargs="?", help="CVE or CWE ID")
    query_parser.add_argument("--limit", type=int, default=100, help="Result limit")
    query_parser.add_argument("--min-cvss", type=float, default=7.0, help="Minimum CVSS score")
    query_parser.add_argument("--kev-only", action="store_true", help="Only KEV CVEs")
    query_parser.add_argument("--days", type=int, default=30, help="Days to look back")
    query_parser.add_argument("--ransomware", action="store_true", help="Only ransomware KEVs")
    
    # Vacuum command
    subparsers.add_parser("vacuum", help="Vacuum database to reclaim space")
    
    # Daemon command
    subparsers.add_parser("daemon", help="Run as periodic update daemon")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    # Execute command
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "init": cmd_init,
        "sync": cmd_sync,
        "status": cmd_status,
        "stats": cmd_stats,
        "query": cmd_query,
        "vacuum": cmd_vacuum,
        "daemon": cmd_daemon,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

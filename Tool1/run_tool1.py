r"""
Tool1 Self-Test and Production Runner
Run: .venv\Scripts\python.exe run_tool1.py [path_to_log_file]
Output goes to BOTH console and tool1_test_result.txt
"""
import sys
import os
import time

# Force fresh imports — no stale bytecode
sys.dont_write_bytecode = True

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Redirect all output to file + console
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            try:
                f.write(obj)
                f.flush()
            except Exception:
                pass
    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except Exception:
                pass

log_file = open(os.path.join(os.path.dirname(__file__), "tool1_test_result.txt"), "w", encoding="utf-8")
sys.stdout = Tee(sys.__stdout__, log_file)
sys.stderr = Tee(sys.__stderr__, log_file)

def run(source_path: str):
    print(f"\n{'='*60}")
    print(f"  PredictPath AI — Tool 1 Production Test")
    print(f"  File: {source_path}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Step 1 — Validate file
    from pathlib import Path
    p = Path(source_path)
    if not p.exists():
        print(f"ERROR: File not found: {p}")
        sys.exit(1)
    print(f"[OK] File exists: {p.name} ({p.stat().st_size:,} bytes)")

    # Step 2 — Import modules
    t = time.time()
    print("[..] Loading modules...")

    from src.core.config import settings
    print(f"     config     : {time.time()-t:.2f}s")

    from src.core.schema import CanonicalEvent
    print(f"     schema     : {time.time()-t:.2f}s")

    from src.core.vulnintel_bridge import _check_db, get_kev_ids
    db_ok = _check_db()
    kev_count = len(get_kev_ids()) if db_ok else 0
    print(f"     vulnintel  : {time.time()-t:.2f}s  (DB={db_ok}, KEV={kev_count})")

    from src.ingestion.universal import UniversalIngestor
    print(f"     ingestor   : {time.time()-t:.2f}s")

    from src.processing.pipeline import Pipeline
    print(f"     pipeline   : {time.time()-t:.2f}s")

    # Step 3 — Run pipeline
    print(f"\n[..] Starting ingestion pipeline...")
    t2 = time.time()

    ingestor = UniversalIngestor(p)
    pipeline = Pipeline(ingestor)
    summary = pipeline.run(max_lines=5000)

    elapsed = time.time() - t2
    print(f"\n{'='*60}")
    print(f"  RESULT SUMMARY")
    print(f"{'='*60}")
    print(f"  Status          : {summary.get('status', 'unknown').upper()}")
    print(f"  Events Ingested : {summary['success']}")
    print(f"  Events Failed   : {summary['failed']}")
    print(f"  Duration        : {elapsed:.2f}s")
    print(f"  Output Dir      : {summary['output_dir']}")

    intel = summary.get("intelligence", {})
    if intel.get("event_types"):
        print(f"\n  Event Types:")
        for k, v in intel["event_types"].items():
            print(f"    {k:<25} : {v}")

    if intel.get("severity_breakdown"):
        print(f"\n  Severity Breakdown:")
        for k, v in intel["severity_breakdown"].items():
            print(f"    {k:<25} : {v}")

    if intel.get("mitre_breakdown"):
        print(f"\n  MITRE Techniques Detected:")
        for k, v in intel["mitre_breakdown"].items():
            print(f"    {k:<25} : {v}")

    if intel.get("cve_ids_observed"):
        print(f"\n  CVEs Observed   : {intel['cve_ids_observed'][:10]}")

    if intel.get("top_hosts"):
        print(f"\n  Top Hosts:")
        for k, v in list(intel["top_hosts"].items())[:5]:
            print(f"    {str(k):<30} : {v}")

    print(f"\n{'='*60}")
    if summary['success'] > 0:
        print(f"  ✅ PASS — Tool 1 is production ready!")
    else:
        print(f"  ❌ FAIL — 0 events ingested. Check file content.")
    print(f"{'='*60}\n")

    log_file.close()
    return summary['success'] > 0


if __name__ == "__main__":
    # Use provided path or default test file
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # Default: use the wazuh file in uploads
        default = os.path.join(os.path.dirname(__file__), "data", "uploads", "wazuh_report_20260206_121425.json")
        path = default
        print(f"No path given — using default: {path}")

    ok = run(path)
    sys.exit(0 if ok else 1)

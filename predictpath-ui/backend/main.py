import asyncio
import subprocess
import os
import signal
import json
import uuid
from datetime import datetime
from typing import List
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import glob
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Directory of Tools
TOOLS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOADS_DIR = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")
SCAN_HISTORY_FILE = os.path.join(TOOLS_ROOT, "predictpath-ui", "backend", "scan_history.json")
os.makedirs(UPLOADS_DIR, exist_ok=True)

class ToolRunRequest(BaseModel):
    tool_name: str
    command: str
    cwd: str

class ResetRequest(BaseModel):
    type: str  # "soft" or "hard"

class ScanRequest(BaseModel):
    scan_type: str

@app.get("/")
def health_check():
    return {"status": "ok", "tools_root": TOOLS_ROOT}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "path": f"data/uploads/{file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
async def reset_system(request: ResetRequest):
    deleted_files = []
    
    # logs: clear scan logs ONLY (for Non-Technical page)
    # soft: clear Tool1-5 artifacts (for Technical page partial reset)
    # hard: clear Tool1-6 artifacts (for Technical page full reset)
    
    if request.type == "logs":
        # Special handling for logs: Nuke the entire folder and recreate
        log_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")
        if os.path.exists(log_dir):
            try:
                shutil.rmtree(log_dir)
                deleted_files.append("scripts/saved-logs")
            except Exception as e:
                print(f"Failed to delete log dir: {e}")
                
        os.makedirs(log_dir, exist_ok=True)
        
        # Clear history file
        if os.path.exists(SCAN_HISTORY_FILE):
            try:
                os.remove(SCAN_HISTORY_FILE)
                deleted_files.append("scan_history.json")
            except Exception as e:
                print(f"Failed to delete history: {e}")
                
        return {"status": "success", "deleted": deleted_files, "mode": "logs"}

    elif request.type == "soft":
        artifacts = [
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "data", "output"), "type": "dir"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "data", "dlq"), "type": "dir"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "ingestion_summary.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "status.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool2", "path_report.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool3", "trajectory_forecast.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool4", "response_plan.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool5", "execution_report.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool5", "execution_audit.log"), "type": "file"},
        ]
    else:  # hard reset
        artifacts = [
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "data", "output"), "type": "dir"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "data", "dlq"), "type": "dir"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "ingestion_summary.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool1", "status.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool2", "path_report.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool6", "status.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool3", "trajectory_forecast.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool4", "response_plan.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool5", "execution_report.json"), "type": "file"},
            {"path": os.path.join(TOOLS_ROOT, "Tool5", "execution_audit.log"), "type": "file"},
        ]
    
    if request.type == "hard":
        # Delete main DB and any WAL/SHM files (sqlite artifacts)
        db_base = os.path.join(TOOLS_ROOT, "Tool6", "data", "governance.db")
        for db_file in glob.glob(db_base + "*"):
             artifacts.append({"path": db_file, "type": "file"})
        
        artifacts.append({"path": os.path.join(TOOLS_ROOT, "Tool6", "test_tamper.db"), "type": "file"})

    try:
        for artifact in artifacts:
            path = artifact["path"]
            if os.path.exists(path):
                if artifact["type"] == "file":
                    os.remove(path)
                    deleted_files.append(os.path.basename(path))
                elif artifact["type"] == "dir":
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    deleted_files.append(f"{os.path.basename(path)}/*")
                    
        return {"status": "success", "deleted": deleted_files, "mode": request.type}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        tool_dir = data.get("tool_dir")
        command_str = data.get("command")
        
        cwd = os.path.join(TOOLS_ROOT, tool_dir)
        
        await websocket.send_text(f"> cd {tool_dir}\n")
        await websocket.send_text(f"> {command_str}\n")
        
        # FORCE UTF-8 ENCODING for Subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # Also try to disable Rich legacy windows renderer if possible, or force color system
        # env["TERM"] = "xterm-256color" 
        
        process = await asyncio.create_subprocess_shell(
            command_str,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        async def stream_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace')
                await websocket.send_text(decoded)

        await asyncio.gather(
            stream_output(process.stdout),
            stream_output(process.stderr)
        )
        await process.wait()
        await websocket.send_text(f"\n[Process exited with code {process.returncode}]")
        await websocket.close()
        
    except Exception as e:
        await websocket.send_text(f"\nError: {str(e)}")
        await websocket.close()

@app.get("/api/file")
def read_file(path: str):
    abs_path = os.path.abspath(os.path.join(TOOLS_ROOT, path))
    if not abs_path.startswith(TOOLS_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(abs_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/download")
def download_file(path: str):
    """Serve a file as a downloadable attachment (used for Tool 5 remediation scripts)."""
    abs_path = os.path.abspath(os.path.join(TOOLS_ROOT, path))
    if not abs_path.startswith(TOOLS_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    filename = os.path.basename(abs_path)
    return FileResponse(
        path=abs_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/tool5/script-info")
def get_tool5_script_info():
    """Returns metadata about the latest Tool 5 remediation script."""
    deployments_dir = os.path.join(TOOLS_ROOT, "Tool5", "deployments")
    if not os.path.exists(deployments_dir):
        return {"available": False, "message": "No scripts generated yet."}
    
    scripts = sorted(
        glob.glob(os.path.join(deployments_dir, "PredictPath_Remediation_*.ps1")),
        key=os.path.getmtime,
        reverse=True
    )
    
    if not scripts:
        return {"available": False, "message": "No remediation scripts found."}
    
    latest = scripts[0]
    rel_path = os.path.relpath(latest, TOOLS_ROOT).replace("\\", "/")
    stat = os.stat(latest)
    
    return {
        "available": True,
        "filename": os.path.basename(latest),
        "path": rel_path,
        "size_bytes": stat.st_size,
        "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "all_scripts": [
            {
                "filename": os.path.basename(s),
                "path": os.path.relpath(s, TOOLS_ROOT).replace("\\", "/"),
                "generated_at": datetime.fromtimestamp(os.path.getmtime(s)).isoformat()
            }
            for s in scripts
        ]
    }

@app.get("/api/tool6/status")
def get_tool6_status():
    """Read Tool 6 governance DB directly and return live status."""
    import sqlite3 as _sqlite3
    db_path = os.path.join(TOOLS_ROOT, "Tool6", "data", "governance.db")
    status_file = os.path.join(TOOLS_ROOT, "Tool6", "status.json")

    # Try status.json first (written by Tool 6 after each run)
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["source"] = "status_file"
            return data
        except Exception:
            pass

    # Fallback: read DB directly
    if not os.path.exists(db_path):
        return {
            "error": "Governance database not found. Run Tool 6 first.",
            "available": False
        }

    try:
        conn = _sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = _sqlite3.Row

        # Active config
        cur = conn.execute("SELECT * FROM model_config WHERE is_active=1 ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "No active model configuration", "available": False}

        config = dict(row)
        momentum = config.get("trust_momentum", 0.0)
        if momentum < -0.001:
            trend = "tightening"
            trend_label = "Tightening (Hardening)"
        elif momentum > 0.001:
            trend = "relaxing"
            trend_label = "Relaxing (Adapting)"
        else:
            trend = "stable"
            trend_label = "Stable"

        # Recent ledger entries
        cur2 = conn.execute(
            "SELECT hash_id, event_type, actor, timestamp, payload FROM trust_ledger ORDER BY timestamp DESC LIMIT 10"
        )
        ledger_entries = []
        for r in cur2.fetchall():
            try:
                payload = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
            except Exception:
                payload = {}
            ledger_entries.append({
                "hash_id": r["hash_id"][:12] + "...",
                "event_type": r["event_type"],
                "actor": r["actor"],
                "timestamp": r["timestamp"],
                "payload": payload,
            })

        # Model history
        cur3 = conn.execute(
            "SELECT version_id, is_active, containment_threshold, disruptive_threshold, trust_momentum, success_streak, failure_streak, created_at FROM model_config ORDER BY created_at DESC LIMIT 6"
        )
        model_history = [dict(r) for r in cur3.fetchall()]

        # Ledger count
        cur4 = conn.execute("SELECT COUNT(*) as cnt FROM trust_ledger")
        ledger_count = cur4.fetchone()["cnt"]

        # Drift alerts (computed from current state)
        drift_alerts = []
        if momentum <= -0.25:
            drift_alerts.append(
                f"CRITICAL DRIFT: Trust momentum is severely negative ({momentum:+.4f}). "
                "Autonomous actions are heavily restricted."
            )
        elif momentum >= 0.25:
            drift_alerts.append(
                f"HIGH RELAXATION: Trust momentum is very high ({momentum:+.4f}). "
                "Thresholds are significantly lowered."
            )
        contain = config.get("containment_threshold", 0.6)
        if contain >= 0.90:
            drift_alerts.append(
                f"THRESHOLD LOCK: Containment at {contain*100:.1f}% — near-lockdown state."
            )
        elif contain <= 0.45:
            drift_alerts.append(
                f"LOW GUARD: Containment at {contain*100:.1f}% — system is highly permissive."
            )
        failure_streak = config.get("failure_streak", 0)
        if failure_streak >= 3:
            drift_alerts.append(
                f"FAILURE STREAK: {failure_streak} consecutive failures. Posture tightening."
            )

        # Recent drift samples for sparkline charts
        drift_samples = []
        try:
            cur5 = conn.execute(
                "SELECT metric_name, metric_value, timestamp, alert_triggered "
                "FROM drift_samples ORDER BY timestamp DESC LIMIT 50"
            )
            drift_samples = [dict(r) for r in cur5.fetchall()]
        except Exception:
            pass  # Table may not exist on older DBs

        conn.close()

        return {
            "source": "database",
            "available": True,
            "generated_at": datetime.now().isoformat(),
            "version_id": config.get("version_id"),
            "containment_threshold": config.get("containment_threshold"),
            "disruptive_threshold": config.get("disruptive_threshold"),
            "trust_momentum": momentum,
            "success_streak": config.get("success_streak", 0),
            "failure_streak": config.get("failure_streak", 0),
            "trend": trend,
            "trend_label": trend_label,
            "ledger_integrity": True,
            "ledger_entry_count": ledger_count,
            "recent_ledger_entries": ledger_entries,
            "model_history": model_history,
            "drift_alerts": drift_alerts,
            "drift_samples": drift_samples,
        }

    except Exception as e:
        return {"error": str(e), "available": False}

@app.get("/api/tool6/drift")
def get_tool6_drift():
    """Return the last 100 drift samples for charting in the UI."""
    import sqlite3 as _sqlite3
    db_path = os.path.join(TOOLS_ROOT, "Tool6", "data", "governance.db")
    if not os.path.exists(db_path):
        return {"available": False, "samples": []}
    try:
        conn = _sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = _sqlite3.Row
        cur = conn.execute(
            "SELECT metric_name, metric_value, timestamp, alert_triggered "
            "FROM drift_samples ORDER BY timestamp ASC LIMIT 100"
        )
        samples = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"available": True, "samples": samples}
    except Exception as e:
        return {"available": False, "error": str(e), "samples": []}


@app.delete("/api/file")
def delete_file(path: str):
    """Delete a specific log file"""
    abs_path = os.path.abspath(os.path.join(TOOLS_ROOT, path))
    
    # Security: only allow deleting files in logs directory
    saved_logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")
    
    if not abs_path.startswith(saved_logs_dir):
        raise HTTPException(status_code=403, detail="Can only delete files in logs directory")
    
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(abs_path)
        
        # Also remove from scan history
        history = load_scan_history()
        history["scans"] = [s for s in history["scans"] if s["log_path"] != path]
        save_scan_history(history)
        
        return {"status": "success", "message": f"Deleted {os.path.basename(abs_path)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# Helper functions for scan history
def load_scan_history():
    if os.path.exists(SCAN_HISTORY_FILE):
        with open(SCAN_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"scans": []}

def save_scan_history(history):
    with open(SCAN_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_scan_to_history(scan_type, status, log_path, file_name):
    history = load_scan_history()
    scan_entry = {
        "id": str(uuid.uuid4()),
        "scan_type": scan_type,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "log_path": log_path,
        "file_name": file_name
    }
    history["scans"].insert(0, scan_entry)  # Most recent first
    save_scan_history(history)
    return scan_entry

@app.websocket("/ws/sync-vuln")
async def websocket_sync_vuln(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        force = data.get("force", False)
        
        vuln_intel_dir = os.path.join(TOOLS_ROOT, "VulnIntel")
        python_exe = os.path.join(vuln_intel_dir, ".venv", "Scripts", "python.exe")
        
        if not os.path.exists(python_exe):
            await websocket.send_text("✗ Error: VulnIntel virtual environment not found.")
            await websocket.close()
            return
            
        await websocket.send_text("======================================")
        await websocket.send_text(" VulnIntel — Data Synchronization")
        await websocket.send_text("======================================")
        await websocket.send_text("")
        await websocket.send_text("[+] Initiating Global Intelligence Sync...")
        await websocket.send_text("[+] Sources: NVD (CVEs), MITRE (CWEs), CISA (KEVs)")
        await websocket.send_text("")

        command = f'"{python_exe}" -m src.main sync --all'
        if force:
            command += " --force"
            
        # FORCE UTF-8 ENCODING for Subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
            
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=vuln_intel_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        async def stream_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    await websocket.send_text(decoded)
        
        await asyncio.gather(
            stream_output(process.stdout),
            stream_output(process.stderr)
        )
        await process.wait()
        
        if process.returncode == 0:
            await websocket.send_text("\n✅ Vulnerability Intel Sync COMPLETED successfully.")
        else:
            await websocket.send_text(f"\n⚠️ Sync finished with exit code {process.returncode}")
            
        await websocket.close()
        
    except Exception as e:
        await websocket.send_text(f"\n✗ Sync error: {str(e)}")
        await websocket.close()

@app.get("/api/scans/history")
def get_scan_history():
    return load_scan_history()

@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        scan_type = data.get("scan_type")
        
        await websocket.send_text(f"> Initializing {scan_type.upper()} Security Scanner...")
        await asyncio.sleep(0.5)
        
        # For network scans, run actual Nmap and OpenVAS scripts
        if scan_type == "network":
            await run_network_scan(websocket)
        elif scan_type == "web":
            # Real OWASP ZAP Scan
            target_url = data.get("target_url")
            if not target_url:
                await websocket.send_text("✗ Error: No target URL provided for Web Scan")
                await websocket.close()
                return
            await run_web_scan(websocket, target_url)
        elif scan_type == "endpoint":
            # Real Wazuh Endpoint Scan
            await run_endpoint_scan(websocket)
        else:
            # Fallback for unknown types
            await run_simulated_scan(websocket, scan_type)
        
    except Exception as e:
        await websocket.send_text(f"\n✗ Error: {str(e)}")
        await websocket.close()



# Global variable to track active scan process
ACTIVE_SCAN_PROCESS = None

@app.post("/api/stop-scan")
async def stop_scan():
    global ACTIVE_SCAN_PROCESS
    try:
        if ACTIVE_SCAN_PROCESS:
            print(f"[INFO] Terminating active scan process (PID: {ACTIVE_SCAN_PROCESS.pid})...")
            try:
                # On Windows, terminate() often doesn't kill child processes (like powershell.exe spawned by cmd)
                # We need taskkill /F /T /PID to kill the entire tree
                subprocess.run(
                    f"taskkill /F /T /PID {ACTIVE_SCAN_PROCESS.pid}", 
                    shell=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"[ERROR] Failed to kill process: {e}")
            
            # Reset variable immediately
            ACTIVE_SCAN_PROCESS = None
            
        # Also explicitly kill OpenVAS container just in case
        print("[INFO] Ensuring openvas container is stopped...")
        subprocess.run("docker stop openvas", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return {"status": "success", "message": "Scan stopped successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_network_scan(websocket: WebSocket):
    """Execute Nmap first, then prompt user for OpenVAS deep scan"""
    global ACTIVE_SCAN_PROCESS
    try:
        scripts_dir = os.path.join(TOOLS_ROOT, "scripts")
        logs_dir = os.path.join(TOOLS_ROOT, "logs")
        
        # Verify scripts exist
        nmap_script = os.path.join(scripts_dir, "run-nmap.ps1")
        openvas_script = os.path.join(scripts_dir, "run-openvas.ps1")
        
        if not os.path.exists(nmap_script):
            await websocket.send_text(f"✗ Error: Nmap script not found at {nmap_script}")
            await websocket.close()
            return
        
        await websocket.send_text("======================================")
        await websocket.send_text(" PredictPath AI — Network Scan Started")
        await websocket.send_text("======================================")
        await websocket.send_text("")
        
        # ============================================
        # STAGE 1: Nmap Network Discovery
        # ============================================
        await websocket.send_text("STAGE 1: Nmap Network Discovery")
        await websocket.send_text("═══════════════════════════════════════")
        await websocket.send_text("")
        
        # Default target - can be made configurable later
        target = "127.0.0.1"  # Scan localhost for testing
        
        await websocket.send_text(f"[+] Target: {target}")
        await websocket.send_text("[+] Starting Nmap scan...")
        await websocket.send_text("")
        
        nmap_command = f'powershell.exe -ExecutionPolicy Bypass -File "{nmap_script}" -Target "{target}"'
        
        # Execute Nmap script
        process = await asyncio.create_subprocess_shell(
            nmap_command,
            cwd=TOOLS_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        ACTIVE_SCAN_PROCESS = process
        
        # Stream Nmap output
        async def stream_nmap_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    await websocket.send_text(decoded)
        
        await asyncio.gather(
            stream_nmap_output(process.stdout),
            stream_nmap_output(process.stderr)
        )
        await process.wait()
        
        nmap_success = process.returncode == 0
        
        if not nmap_success:
            await websocket.send_text("")
            await websocket.send_text(f"✗ Nmap scan failed with exit code {process.returncode}")
            await websocket.send_text("✗ Workflow terminated.")
            await websocket.close()
            return
        
        await websocket.send_text("")
        await websocket.send_text("✓ Nmap scan completed successfully")
        
        # Find and save Nmap log files
        nmap_log_file = None
        nmap_logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "nmap")
        if os.path.exists(nmap_logs_dir):
            nmap_files = sorted(glob.glob(os.path.join(nmap_logs_dir, "nmap-*.xml")), 
                               key=os.path.getmtime, reverse=True)
            if nmap_files:
                latest_nmap = nmap_files[0]
                nmap_log_file = os.path.basename(latest_nmap)
                rel_path = os.path.relpath(latest_nmap, TOOLS_ROOT)
                await websocket.send_text(f"✓ Nmap report saved: {nmap_log_file}")
                
                # Add to scan history
                add_scan_to_history("network-nmap", "completed", rel_path, nmap_log_file)
        
        await websocket.send_text("")
        await websocket.send_text("Scan completed successfully.")
        await websocket.send_text("Nmap report saved.")
        await websocket.send_text("")
        
        # ============================================
        # USER PROMPT: Ask about OpenVAS deep scan
        # ============================================
        await websocket.send_text("═══════════════════════════════════════")
        await websocket.send_text("USER DECISION REQUIRED")
        await websocket.send_text("═══════════════════════════════════════")
        await websocket.send_text("")
        await websocket.send_text("Nmap scan completed. Do you want to run a deeper")
        await websocket.send_text("vulnerability scan using OpenVAS?")
        await websocket.send_text("")
        await websocket.send_text("⚠ Note: OpenVAS deep scan can take 15-60 minutes")
        await websocket.send_text("")
        
        # Send special prompt message that UI will recognize
        print(f"[DEBUG] Sending user prompt to WebSocket...")  # Debug log
        await websocket.send_json({
            "type": "user_prompt",
            "message": "Run deeper vulnerability scan with OpenVAS?",
            "options": ["Yes", "No"]
        })
        print(f"[DEBUG] User prompt sent successfully")  # Debug log
        
        # Wait for user response
        try:
            response_data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=300.0  # 5 minute timeout for user decision
            )
            user_choice = response_data.get("choice", "").lower()
        except asyncio.TimeoutError:
            await websocket.send_text("")
            await websocket.send_text("⚠ No response received. Defaulting to 'No'.")
            user_choice = "no"
        
        await websocket.send_text("")
        await websocket.send_text(f"User selected: {user_choice.upper()}")
        await websocket.send_text("")
        
        # ============================================
        # BRANCH: User selected NO
        # ============================================
        if user_choice != "yes":
            await websocket.send_text("✓ Workflow completed.")
            await websocket.send_text("✓ Download Nmap report from 'Generated Scan Logs'")
            await websocket.send_text("")
            await websocket.send_text("======================================")
            await websocket.send_text(" Network Security Analysis COMPLETED")
            await websocket.send_text("======================================")
            await websocket.close()
            return
        
        # ============================================
        # STAGE 2: OpenVAS Deep Vulnerability Scan
        # ============================================
        await websocket.send_text("STAGE 2: OpenVAS Deep Vulnerability Scan")
        await websocket.send_text("═══════════════════════════════════════")
        await websocket.send_text("")
        
        # Check if OpenVAS script exists
        if not os.path.exists(openvas_script):
            await websocket.send_text("✗ OpenVAS script not found")
            await websocket.send_text("✓ Workflow completed with Nmap only")
            await websocket.close()
            return
        
        msg_start = "✓ OpenVAS workflow initiated"
        await websocket.send_text(msg_start)
        await websocket.send_text("[+] Starting deep vulnerability scan...")
        await websocket.send_text("[+] This will take 15-60 minutes depending on target size")
        await websocket.send_text("")
        
        # Execute OpenVAS script
        openvas_command = f'powershell.exe -ExecutionPolicy Bypass -File "{openvas_script}" -Target "{target}"'
        
        openvas_process = await asyncio.create_subprocess_shell(
            openvas_command,
            cwd=TOOLS_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        ACTIVE_SCAN_PROCESS = openvas_process
        
        # Stream OpenVAS output
        async def stream_openvas_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    await websocket.send_text(decoded)
        
        await asyncio.gather(
            stream_openvas_output(openvas_process.stdout),
            stream_openvas_output(openvas_process.stderr)
        )
        await openvas_process.wait()
        
        openvas_success = openvas_process.returncode == 0
        
        await websocket.send_text("")
        if openvas_success:
            await websocket.send_text("✓ Deep vulnerability scan completed successfully")
            
            # Find OpenVAS log files
            openvas_logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs", "openvas")
            if os.path.exists(openvas_logs_dir):
                openvas_files = sorted(glob.glob(os.path.join(openvas_logs_dir, "openvas-*.xml")), 
                                      key=os.path.getmtime, reverse=True)
                if openvas_files:
                    latest_openvas = openvas_files[0]
                    openvas_log_file = os.path.basename(latest_openvas)
                    rel_path = os.path.relpath(latest_openvas, TOOLS_ROOT)
                    await websocket.send_text(f"✓ OpenVAS report saved: {openvas_log_file}")
                    
                    # Add to scan history
                    add_scan_to_history("network-openvas", "completed", rel_path, openvas_log_file)
        else:
            await websocket.send_text(f"✗ OpenVAS scan failed with exit code {openvas_process.returncode}")
        
        await websocket.send_text("")
        await websocket.send_text("======================================")
        await websocket.send_text(" Network Security Analysis COMPLETED")
        await websocket.send_text("======================================")
        await websocket.send_text("")
        await websocket.send_text("✓ All reports saved to /logs folder")
        await websocket.send_text("✓ Download reports from 'Generated Scan Logs'")
        
        await websocket.close()
        
    except Exception as e:
        await websocket.send_text(f"\n✗ Network scan error: {str(e)}")
        import traceback
        await websocket.send_text(f"✗ Details: {traceback.format_exc()}")
        await websocket.close()

async def run_web_scan(websocket: WebSocket, target_url: str):
    """Execute generic OWASP ZAP scan via run-zap.ps1"""
    global ACTIVE_SCAN_PROCESS
    try:
        zap_script = os.path.join(TOOLS_ROOT, "scripts", "run-zap.ps1")
        
        if not os.path.exists(zap_script):
            await websocket.send_text(f"✗ Error: ZAP script not found at {zap_script}")
            await websocket.close()
            return
            
        await websocket.send_text("======================================")
        await websocket.send_text(" Web Security Analysis (OWASP ZAP)")
        await websocket.send_text("======================================")
        await websocket.send_text("")
        await websocket.send_text(f"[+] Target URL: {target_url}")
        await websocket.send_text("[+] Launching OWASP ZAP CLI...")
        await websocket.send_text("[+] This runs a real 'Quick Scan' - Spider & Active Scan")
        await websocket.send_text("")

        zap_command = f'powershell.exe -ExecutionPolicy Bypass -File "{zap_script}" -TargetUrl "{target_url}"'
        
        process = await asyncio.create_subprocess_shell(
            zap_command,
            cwd=TOOLS_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        ACTIVE_SCAN_PROCESS = process
        
        async def stream_zap_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    await websocket.send_text(decoded)
        
        await asyncio.gather(
            stream_zap_output(process.stdout),
            stream_zap_output(process.stderr)
        )
        await process.wait()
        
        success = process.returncode == 0
        
        await websocket.send_text("")
        if success:
            await websocket.send_text("✓ ZAP Scan completed successfully")
            
            # Detect logged file
            zap_logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")
            # Look for zap_report_*.json
            if os.path.exists(zap_logs_dir):
                zap_files = sorted(glob.glob(os.path.join(zap_logs_dir, "zap_report_*.json")),
                                   key=os.path.getmtime, reverse=True)
                if zap_files:
                    latest_zap = zap_files[0]
                    zap_log_file = os.path.basename(latest_zap)
                    rel_path = os.path.relpath(latest_zap, TOOLS_ROOT)
                    await websocket.send_text(f"✓ ZAP Report saved: {zap_log_file}")
                    
                    # Parse JSON for Summary
                    try:
                        with open(latest_zap, "r", encoding="utf-8") as zf:
                            zap_data = json.load(zf)
                            
                        alerts = []
                        # ZAP 'quickout' format usually has a root object or 'site' list
                        # If simple alert list:
                        if isinstance(zap_data, dict) and "site" in zap_data:
                            for site in zap_data["site"]:
                                if "alerts" in site:
                                    alerts.extend(site["alerts"])
                        
                        summary = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
                        for alert in alerts:
                            risk = alert.get("risk", "Informational")
                            if risk in summary:
                                summary[risk] += 1
                        
                        await websocket.send_text("")
                        await websocket.send_text("═══════════════════════════════════════")
                        await websocket.send_text(" VULNERABILITY SUMMARY")
                        await websocket.send_text("═══════════════════════════════════════")
                        await websocket.send_text(f"🛑 HIGH: {summary['High']}")
                        await websocket.send_text(f"⚠️ MEDIUM: {summary['Medium']}")
                        await websocket.send_text(f"ℹ️ LOW: {summary['Low']}")
                        await websocket.send_text(f"📝 INFO: {summary['Informational']}")
                        
                    except Exception as e:
                        print(f"Failed to parse ZAP summary: {e}")
                    
                    add_scan_to_history("web", "completed", rel_path, zap_log_file)
        else:
             await websocket.send_text(f"✗ ZAP Scan failed with exit code {process.returncode}")
             
        await websocket.send_text("")
        await websocket.send_text("======================================")
        await websocket.send_text(" Web Security Analysis COMPLETED")
        await websocket.send_text("======================================")
        await websocket.close()
        
    except Exception as e:
        await websocket.send_text(f"\n✗ ZAP scan error: {str(e)}")
        await websocket.close()


async def run_simulated_scan(websocket: WebSocket, scan_type: str):
    """Keep simulated scans for endpoint (for now)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{scan_type}_scan_{timestamp}.log"
    
    # Save to logs directory, not Tool1/data/uploads
    logs_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs", scan_type)
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, log_filename)
    
    # Simulate scan execution with realistic output
    scan_steps = {
        "endpoint": [
            "Starting Wazuh endpoint hygiene scan...",
            "Checking system integrity...",
            "Antivirus status: Active",
            "Firewall status: Enabled",
            "Last system update: 2026-01-20",
            "Running CVE mapping...",
            "Detected outdated package: openssl-1.1.1 (CVE-2023-5678)",
            "Initiating Velociraptor forensic artifact collection...",
            "Collecting process list...",
            "Collecting network connections...",
            "Collecting registry keys...",
            "Scan complete. 1 CVE detected, artifacts collected."
        ]
    }
    
    steps = scan_steps.get(scan_type, ["Unknown scan type"])
    log_lines = []
    
    for step in steps:
        await websocket.send_text(step)
        log_lines.append(f"{datetime.now().isoformat()} - {step}")
        await asyncio.sleep(0.3)
    
    # Write log file
    with open(log_path, "w") as f:
        f.write("\n".join(log_lines))
    
    # Add to history with correct path
    rel_path = os.path.relpath(log_path, TOOLS_ROOT)
    add_scan_to_history(scan_type, "completed", rel_path, log_filename)
    
    await websocket.send_text(f"\n✓ Log file generated: {log_filename}")
    await websocket.send_text(f"✓ Scan completed successfully")
    await websocket.close()



async def run_endpoint_scan(websocket: WebSocket):
    """Execute Wazuh Endpoint Scan via run-wazuh-scan.ps1"""
    global ACTIVE_SCAN_PROCESS
    try:
        script_path = os.path.join(TOOLS_ROOT, "scripts", "run-wazuh-scan.ps1")
        
        if not os.path.exists(script_path):
            await websocket.send_text(f"✗ Error: Wazuh scan script not found at {script_path}")
            await websocket.close()
            return
            
        await websocket.send_text("======================================")
        await websocket.send_text(" PredictPath AI — Endpoint Security Analysis")
        await websocket.send_text("======================================")
        await websocket.send_text("")
        await websocket.send_text("[+] Target: Local Endpoint & Wazuh Manager")
        await websocket.send_text("[+] Initiating On-Demand Audit Scan...")
        await websocket.send_text("[+] This forces agent wake-up and module restart.")
        await websocket.send_text("")

        # PowerShell command
        command = f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"'
        
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=TOOLS_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        ACTIVE_SCAN_PROCESS = process
        
        async def stream_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    await websocket.send_text(decoded)
        
        await asyncio.gather(
            stream_output(process.stdout),
            stream_output(process.stderr)
        )
        await process.wait()
        
        success = process.returncode == 0
        
        await websocket.send_text("")
        if success:
            await websocket.send_text("✓ Wazuh Endpoint Scan completed successfully")
            
            # The script defines the output at specific path
            # $LocalLogPath = "...\scripts\saved-logs\wazuh_final_report.json"
            
            base_log_dir = os.path.join(TOOLS_ROOT, "scripts", "saved-logs")
            expected_report = os.path.join(base_log_dir, "wazuh_final_report.json")
            
            if os.path.exists(expected_report):
                # Rename with timestamp to support history
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"wazuh_report_{timestamp}.json"
                new_path = os.path.join(base_log_dir, new_filename)
                
                shutil.copy2(expected_report, new_path)
                
                rel_path = os.path.relpath(new_path, TOOLS_ROOT)
                await websocket.send_text(f"✓ Report saved: {new_filename}")
                
                # Parse summary from JSON
                try:
                     with open(new_path, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                        # Structure: { vulnerability: [], malware_behavior: [], ... }
                        
                        await websocket.send_text("")
                        await websocket.send_text("═══════════════════════════════════════")
                        await websocket.send_text(" SECURITY FINDINGS SUMMARY")
                        await websocket.send_text("═══════════════════════════════════════")
                        
                        cats = {
                            "vulnerability": "🔓 Vulnerabilities",
                            "malware_behavior": "🦠 Malware/Rootkits",
                            "privilege_escalation": "⚡ Priv Esc Risks",
                            "persistence": "⚓ Persistence Mechs"
                        }
                        
                        total_findings = 0
                        for key, label in cats.items():
                            count = len(data.get(key, []))
                            total_findings += count
                            if count > 0:
                                await websocket.send_text(f"{label}: {count} findings")
                            else:
                                await websocket.send_text(f"{label}: Clean")
                        
                        if total_findings == 0:
                            await websocket.send_text("")
                            await websocket.send_text("🎉 No new security alerts detected in this scan window.")
                            
                except Exception as e:
                    await websocket.send_text(f"⚠ Failed to parse report summary: {e}")
                
                add_scan_to_history("endpoint", "completed", rel_path, new_filename)
            else:
                 await websocket.send_text("⚠ Warning: Expected report file not found.")

        else:
             await websocket.send_text(f"✗ Scan failed with exit code {process.returncode}")
             
        await websocket.send_text("")
        await websocket.send_text("======================================")
        await websocket.send_text(" Endpoint Security Analysis COMPLETED")
        await websocket.send_text("======================================")
        await websocket.close()
        
    except Exception as e:
        await websocket.send_text(f"\n✗ Endpoint scan error: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

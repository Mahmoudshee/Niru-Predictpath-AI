<div align="center">

# 🛡️ PredictPath AI

### Autonomous Cyber Defense Pipeline (CLI + UI)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Windows](https://img.shields.io/badge/Windows-PowerShell-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

**PredictPath AI** is a real, end-to-end autonomous cyber-defense system composed of six tightly integrated tools.

It ingests raw security logs, builds behavioral context, predicts attacker trajectories, plans defensive actions, executes real system controls, and continuously learns through governance feedback.

</div>

---

## 📋 Table of Contents

- [Operation Modes](#-operation-modes)
- [System Architecture](#-system-architecture-overview)
- [Part 1: Terminal (CLI) Usage](#%EF%B8%8F-part-1--terminal-cli-usage)
- [Part 2: UI Usage (Operator Mode)](#%EF%B8%8F-part-2--ui-usage-operator-mode)
- [Verification & Demonstration](#-verification--demonstration)
- [Audit & Compliance](#-audit--compliance)

---

## 🎯 Operation Modes

| Mode | Description |
|------|-------------|
| **Terminal (CLI)** | Full transparency, engineering & SOC-grade control |
| **UI Mode** | Operator cockpit with live terminal streaming and visual intelligence |

---

## 🧠 System Architecture Overview

```
Raw Logs
   ↓
Tool 1 ── Event Intelligence Engine
   ↓
Tool 2 ── Session Context & Risk Engine
   ↓
Tool 3 ── Predictive Attack Trajectory Engine
   ↓
Tool 4 ── Adaptive Decision Engine
   ↓
Tool 5 ── Controlled Response Execution Engine
   ↓
Tool 6 ── Trust & Governance Learning Engine
```

### Each tool:

- ✅ Is independently executable
- ✅ Produces real artifacts (Parquet / JSON / DB)
- ✅ Has zero mock logic
- ✅ Can be audited and replayed

---

## ⚙️ PART 1 — TERMINAL (CLI) USAGE

### 1️⃣ Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.11+ |
| **OS** | Windows (PowerShell required for Tool 5) |
| **Permissions** | Administrator (for firewall / audit policy execution) |

### 2️⃣ Environment Setup (One-Time)

Each tool runs in its own virtual environment.

```powershell
# Tool 1
cd Tool1
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Tool 2
cd ..\Tool2
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Tool 3
cd ..\Tool3
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Tool 4
cd ..\Tool4
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Tool 5
cd ..\Tool5
python -m venv .venv
.\.venv\Scripts\pip install -e .

# Tool 6
cd ..\Tool6
python -m venv .venv
.\.venv\Scripts\pip install -e .
```

> ⚠️ Each tool's `pyproject.toml` defines its exact dependencies.  
> Editable installs (`-e .`) are recommended.

---

### 3️⃣ End-to-End CLI Execution

#### 🔷 Tool 1 — Event Intelligence Engine

**Purpose:** Ingest raw logs, normalize, enrich with MITRE ATT&CK

```powershell
cd Tool1
.\.venv\Scripts\python.exe -m src.main ingest data/samples/lanl_small.txt --type lanl
```

**Output:** `Tool1/data/output/YYYY-MM-DD/*.parquet`

---

#### 🔷 Tool 2 — Session Context Engine

**Purpose:** Build sessions, detect anomalies, compute risk

```powershell
cd ..\Tool2
.\.venv\Scripts\python.exe -m src.main "..\Tool1\data\output\**\*.parquet"
```

**Output:** `risk_assessment.json`

---

#### 🔷 Tool 3 — Predictive Trajectory Engine

**Purpose:** Forecast attacker next moves probabilistically

```powershell
cd ..\Tool3
.\.venv\Scripts\python.exe -m src.main "..\Tool2\risk_assessment.json"
```

**Output:** `trajectory_forecast.json`

---

#### 🔷 Tool 4 — Adaptive Decision Engine

**Purpose:** Rank and justify defensive actions

```powershell
cd ..\Tool4
.\.venv\Scripts\python.exe -m src.main "..\Tool3\trajectory_forecast.json"
```

**Output:** `response_plan.json`

---

#### 🔷 Tool 5 — Controlled Response Execution Engine

**Purpose:** Execute real system controls safely

```powershell
cd ..\Tool5
.\.venv\Scripts\python.exe -m src.main "..\Tool4\response_plan.json"
```

**Outputs:**
- `execution_report.json`
- `execution_audit.log`

> ⚠️ **Warning:** Tool 5 performs real system changes (audit policy, firewall rules).  
> Rollback instructions are embedded and logged.

---

#### 🔷 Tool 6 — Trust & Governance Engine

**Purpose:** Learn from outcomes and adapt autonomy

```powershell
cd ..\Tool6

# View current system trust
.\.venv\Scripts\python.exe -m src.main status

# Ingest execution feedback
.\.venv\Scripts\python.exe -m src.main ingest "..\Tool5\execution_report.json"
```

**Persistent State:** `Tool6/data/governance.db`

---

### 🔄 Reset Modes (CLI)

#### Soft Reset (New Run, Preserve Learning)
```powershell
# Delete Tool1–Tool5 outputs only
```

#### Hard Reset (Clear Learning)
```powershell
cd Tool6
Remove-Item data/governance.db
.\.venv\Scripts\python.exe -m src.main init
```

---

## 🖥️ PART 2 — UI USAGE (OPERATOR MODE)

### 🎛️ UI Philosophy

> **The UI is not a simulator.**  
> It is a live orchestration cockpit that:

- ✅ Executes real CLI commands
- ✅ Streams live terminal output
- ✅ Displays structured intelligence
- ✅ Preserves auditability

---

### 🚀 Launching the UI

1. **Start Backend (Terminal 1)**
   ```powershell
      cd cd c:\Users\cisco\Documents\pushing_Niru_codes\Niru-Predictpath-AI\predictpath-ui\backend
      .\venv\Scripts\activate

      venv\Scripts\python.exe main.py

      

      ```

2. **Start Frontend (Terminal 2)**
   ```powershell
   cd predictpath-ui
   npm run dev
   ```

3. **Access**: Open `http://localhost:5173`

---

### 🧱 UI Layout

#### 1️⃣ Pipeline Control Panel (Left)

**Buttons for:**
- Tool 1 → Tool 6
- Status indicators (Idle / Running / Completed / Failed)

**Reset controls:**
- 🔄 New Run (Preserve Learning)
- 🧹 Full Reset (Clear Governance)

---

#### 2️⃣ Live Terminal Panel (Center)

- Displays exact commands being executed
- Streams stdout/stderr in real time
- Mirrors PowerShell behavior

**Example:**
```
> Tool3
.\.venv\Scripts\python.exe -m src.main "..\Tool2\risk_assessment.json"
```

---

#### 3️⃣ Intelligence View (Right)

**Renders real outputs:**

| Tool | Output |
|------|--------|
| Tool 3 | Predicted attack paths |
| Tool 4 | Ranked response plans |
| Tool 5 | Execution outcomes |
| Tool 6 | Trust thresholds & trends |

---

### ▶️ UI Workflow

1. Upload or select raw log file
2. Click **Run Tool 1**
3. Progressively run Tool 2 → Tool 6
4. Approve Tool 5 actions explicitly
5. Observe trust adaptation in Tool 6
6. Reset when needed

---

### 🔐 Safety & Governance (UI)

| Feature | Status |
|---------|--------|
| Tool 5 actions require explicit confirmation | ✅ |
| Tool 6 learning cannot be auto-reset | ✅ |
| All executions are logged and replayable | ✅ |
| Terminal output is never hidden | ✅ |

---

## 🧪 Verification & Demonstration

### Force Learning Behavior

```powershell
cd Tool6
.\.venv\Scripts\python.exe -m src.main ingest data/failed_report.json
.\.venv\Scripts\python.exe -m src.main ingest data/success_report.json
```

**Observe:**
- Threshold tightening after failures
- Relaxation after success streaks

---

## 📜 Audit & Compliance

| Tool | Feature |
|------|---------|
| **Tool 1** | Hash-chained event integrity |
| **Tool 5** | Tamper-evident audit logs |
| **Tool 6** | Persistent governance DB |

> 📁 Full replay possible from artifacts alone

---

## 🏁 Summary

<div align="center">

### PredictPath AI is:

| ✅ Real | ✅ Explainable | ✅ Auditable | ✅ Self-correcting |
|---------|----------------|--------------|---------------------|
| No simulations | Full transparency | Complete logs | Adaptive learning |

---

**CLI mode** provides engineering-grade control.  
**UI mode** provides SOC-grade operational visibility.

Both operate on the same execution backbone.

---

### 🛡️ PredictPath AI — Autonomous Defense, Done Right

**© 2026**

</div>

# PredictPath AI - Tool 5: Automated Execution

## 📋 Overview
Tool 5 executes the approved response plans. It interfaces with system APIs (mocked for safety) to apply changes.

## ⚠️ Warning
By default, this tool runs in **Simulation Mode** (Dry Run). To enable active execution, modify `config.yaml`.

## 🚀 Quick Start

### 1. Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

### 2. Running
```bash
python main.py
```

### 3. Logs
Execution audit trails are saved to `audit/`.

# PredictPath AI - Tool 2: Path Prediction Engine

## 📋 Overview
Tool 2 analyzes processed logs from Tool 1 to predict potential attack paths. It uses graph-based analysis to map lateral movement possibilities.

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.8+
- Tool 1 output files (optional but recommended)

### 2. Setup Virtual Environment
**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

### 3. Missing Files
These folder are ignored and will be created automatically:
- `data/` - Input/Output data
- `cache/` - Graph processing cache

### 4. Running the Tool
```bash
python main.py
```
*Note: Ensure Tool 1 has run at least once to populate input data.*
